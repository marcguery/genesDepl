from flask import g

import json #database infos
import datetime #database state
from hashlib import md5 #ETag hash
#Database
import sqlite3
import mysql.connector
#Config
from .dbInfos import DataBase #Set your own database informations in this file
#utils
from .persError import dictError #Personnalised error class

class Query(DataBase):
	"""Functions of connection, verification and query generation
	of a given DatabBase.
	All attributes are inherited from DatabBase.
	See DataBase class for personnalisation of your DB infos"""
	def linkDb(self, dbtype):
		"""Get informations needed for connection.
		Need to know the database type
		"""
		with open(self.detail) as f:
			infos = json.load(f)
			dbinfos = infos[dbtype]
		f.close()
		return dbinfos

	def getDb(self):
		"""Connection to database.
		"""
		db = getattr(g, '_database', None)
		if db is None:
			if self.dbtype=='sql':
				dbinfos=self.linkDb(self.dbtype)
				try:
					db = g._database = mysql.connector.connect(
						user=dbinfos['pers']['login'],
						password=dbinfos['pers']['password'],
						host=dbinfos['base']['host'],
						database=dbinfos['base']['database'])
				except:
					mess="Impossible de se connecter à la base de données MySQL. Vous devriez vérifier vos fichiers de configuration."
					raise Exception(mess)
			elif self.dbtype=='sqlite':
				dbinfos=self.linkDb(self.dbtype)
				try:
					db = g._database = sqlite3.connect(str(self.location) + str(dbinfos['database']))
				except:
					mess="Le fichier sqlite est introuvable. Vous devriez vérifier vos fichiers de configuration."
					raise Exception(mess)
		return db

	def error(self, status=400, title="Vous ne pouvez pas faire ça comme ça.", source={}, detail=None):
		"""Provide a dict containing statements when something went wrong.
		General statement for all errors plus optionnaly statements
		Optionnaly arguments passed to function like 'arg = sentence'
		"""
		#General statement
		err={"status": status,
		  "source": source,
		  "title":  title,
		  "detail": detail}
		return err

	def saveDate(self, date, append=True):
		"""Save the current state of database in a log file.
		The date of modification (typically provided by executeQuery()) could be in any format.
		Append to log file if True, otherwise overwrite.
		"""
		try:
			if append:
				with open(self.log, "a") as f:
					f.write(str(date)+"\n")
			else:
				with open(self.log, "w") as f:
					f.write(str(date)+"\n")
			f.close()
		except:
			mess="Impossible de sauver la date de modification, log introuvable."
			raise FileNotFoundError(mess)

	def getEtag(self, date = True, crit = None):
		"""Generate a md5 hash to be passed to ETag header.
		If date is True, takes the last date of modification from log file
		crit argument is a string to be hashed. If both date and crit are provided, 
			hash is a result of them merged
		"""
		if date:
			etag=str(self.date)
		else:
			etag = ""
		etag = ';'.join([etag, crit]) if crit is not None else etag
		hetag = md5(etag.encode('utf-8')).hexdigest()
		return hetag

	def isInBase(self, giD, iDs):
		"""Check if a given gene is in the database.
		If gene is not in database, raise Exception
		"""
		if giD in iDs:
			return
		else:
			status = 403
			mess=self.error(detail="Le gène %s n'existe pas." % giD, status=status, 
				source={"verif" : "Présence dans la base"})
			raise dictError({"errors" : [mess], "status" : status})

	def isNotInBase(self, giD, iDs):
		"""Check if a given gene is in the database.
		If gene is in database, raise Exception
		"""
		if giD not in iDs:
			return
		else:
			status = 403
			mess=self.error(detail="Le gène %s existe déjà." % giD, status=status, 
				source={"verif" : "Présence dans la base"})
			raise dictError({"errors" : [mess], "status" : status})
	def verifGene(self, dictCont):
		"""Check if informations of a gene are correct.
		Need a dictionnary for one gene
		Return a dictionnary of well formated fields if success
		"""
		##Attribut length verification
		if len(dictCont)!=7:
			status = 418
			mess=self.error(title="Mauvais encodage du gène %s." % dictCont["Ensembl_Gene_ID"], 
				detail="Nombre d'attributs inattendu, les champs optionnels, même nuls, doivent apparaître.", status=status,
				source={"verif" : "Format du gène"})
			raise dictError({"errors" : [mess], "status" : status})
		##
		##Necessary keys verification
		for oblgKeys in ["Ensembl_Gene_ID", "Chromosome_Name", "Gene_Start", "Gene_End"]:
			if dictCont[oblgKeys] == "" or dictCont[oblgKeys] is None:
				status = 400
				mess=self.error(title="Champs manquants du gène %s." % dictCont["Ensembl_Gene_ID"], 
					detail="Ensembl_Gene_ID, Chromosome_Name, Gene_Start et Gene_End ne doivent pas être vides.",
					status=status, source={"verif" : "Format du gène"})
				raise dictError({"errors" : [mess], "status" : status})
		##
		##Format verification
		#String and integer formating
		try:
			for strKeys in ["Ensembl_Gene_ID", "Chromosome_Name", "Band", "Associated_Gene_Name"]:
				dictCont[strKeys]=str(dictCont[strKeys])
			for intKeys in ["Strand", "Gene_Start", "Gene_End"]:
				dictCont[intKeys]=int(dictCont[intKeys])
		except:
			status = 400
			mess1=self.error(title="Mauvais encodage du gène %s." % dictCont["Ensembl_Gene_ID"], 
				detail="Ensembl_Gene_ID, Chromosome_Name, Band et Associated_Gene_Name doivent être des chaines de carcatères",
				status=status, source={"verif" : "Format du gène"})
			mess2=self.error(title="Mauvais encodage du gène %s." % dictCont["Ensembl_Gene_ID"], 
				detail="Strand, Gene_Start et Gene_End doivent être des entiers.",
				status=status, source={"verif" : "Format du gène"})
			raise dictError({"errors" : [mess1, mess2], "status" : status})
		#
		#Difference between End and Start
		if dictCont["Gene_End"]<= dictCont["Gene_Start"]:
			status = 400
			mess=self.error(title="Incohérence du gène %s." % dictCont["Ensembl_Gene_ID"],
				detail="Gene_Start doit être strictement inférieur à Gene_End.", status=status,
				source={"verif" : "Format du gène"})
			raise dictError({"errors" : [mess], "status" : status})
		#
		##
		return dictCont

	def executeQuery(self, query, commit = False, save = False):
		"""Execute a query in the database.
		Require a query
		Commit is necessary when creating, editing or deleting
		Return a cursor object and a date of modification if commit is True
		"""
		modDate = None
		cursor = self.getDb().cursor()
		cursor.execute(query)
		if commit:
			self.getDb().commit() #PERMANENT CHANGE
			modDate = datetime.datetime.now()
			if save:
				self.saveDate(modDate)
		return [cursor, modDate]

	def queryAllTable(self, table="Genes"):
		"""Generate a query of all elements in a given table.
		Default table is Genes
		Return the string formated query
		"""
		queryKeyes = ("SELECT * FROM %s;" % (table,))
		return {"query" : queryKeyes}

	def queryOneGene(self, iD):
		"""Generate a query to pick one gene in the database.
		iD must belong to Ensembl_Gene_ID column
		Return the string formated query
		"""
		queryGenes=self.queryAllTable()["query"]
		cursor = self.executeQuery(queryGenes)[0]
		genes = cursor.fetchall()
		iDs = map(lambda x : x[0], genes)
		##Check if gene is in database first
		try:
			inBase = self.isInBase(iD, iDs)
		except dictError as e:
			raise e
		queryGene=("SELECT G.* FROM Genes G WHERE G.Ensembl_Gene_ID = '%s' ;" % (iD,))
		return {"query" : queryGene}
		

	def queryIns(self, form):
		"""Generate a query to insert one gene in the database.
		iD must belong to Ensembl_Gene_ID column
		Return the string formated query
		"""
		dicinfos=form
		##Verification
		queryAll=self.queryAllTable()["query"]
		cursor = self.executeQuery(queryAll)[0]
		genes = cursor.fetchall()
		iDs = map(lambda x : x[0], genes)
		try:
			notInBase = self.isNotInBase(dicinfos["Ensembl_Gene_ID"], iDs)
		##
		except dictError as e:#if gene already exists, error
			for err in e["errors"]:
				err["source"]["query"]="Insertion d'un gène"
			raise e
		try:
			verif = self.verifGene(dicinfos)
			cols=', '.join([*verif.keys()])
			vals=', '.join(map(lambda x: "'" + str(x) + "'" , [*verif.values()]))
			queryIns = ("INSERT INTO Genes (%s) VALUES (%s)" % (cols, vals,))
			return {"query" : queryIns}
		except dictError as e:
			for err in e["errors"]:
				err["source"]["query"]="Insertion d'un gène"
			raise e

	def queryEdit(self, form, iD):
		"""Generate a query to edit an existing gene in the database.
		Require a dictionnary of one gene and its iD
		Return the string formated query
		"""
		dicinfos = form
		dicinfos["Ensembl_Gene_ID"]=iD #Reset Id if it has been changed
		comb = []
		##Verification
		queryAll=self.queryAllTable()["query"]
		cursor = self.executeQuery(queryAll)[0]
		genes = cursor.fetchall()
		iDs = map(lambda x : x[0], genes)
		try:
			inBase = self.isInBase(iD, iDs)
		except dictError as e: #if gene does not exist, error
			for err in e["errors"]:
				err["source"]["query"]="Modification d'un gène"
			raise e
		##
		try:
			verif = self.verifGene(dicinfos)
			for col in dicinfos:
				comb.append("%s='%s'" % (col, dicinfos[col]))
			queryEdit = ("UPDATE Genes SET %s WHERE Ensembl_Gene_ID = '%s' ;" % (",".join([*comb]), iD,))
			return {"query" : queryEdit}
		except dictError as e:
			for err in e["errors"]:
				err["source"]["query"]="Modification d'un gène"
			raise e

	def queryDel(self, iD):
		"""Generate a query to delete an existing gene from the database.
		Require gene iD
		Return the string formated query
		"""
		##Verification
		queryAll=self.queryAllTable()["query"]
		cursor = self.executeQuery(queryAll)[0]
		genes = cursor.fetchall()
		iDs = map(lambda x : x[0], genes)
		try:
			inBase = self.isInBase(iD, iDs)
		except dictError as e: #if gene does not exist, error
			for err in e["errors"]:
				err["source"]["query"]="Suppression d'un gène"
			raise e
		queryDel = ("DELETE FROM Genes WHERE Ensembl_Gene_ID = '%s' ;" % (iD,))
		return {"query" : queryDel}

	def viewGene(self, iD):
		"""Give the representation for a given gene.
		`gene` key points to a dictionnary of the gene
		`trans` key points to a list of dictionnary of transcripts
		Return a dictionnary of gene and its transcripts if succeeded
		"""
		##
		##Gene
		try:
			one = self.queryOneGene(iD)
		except dictError as e:
			for err in e["errors"]:
				err["source"]["query"]="Visualisation d'un gène"
			raise e
		queryOne = one["query"]
		cursor = self.executeQuery(queryOne)[0]
		info = cursor.fetchone()
		cols = [description[0] for description in cursor.description]
		gene = dict(zip(cols, info))
		##
		##Transcripts
		queryTrans = ("""SELECT T.Ensembl_Transcript_ID, T.Transcript_Start, T.Transcript_End
		FROM Transcripts T WHERE T.Ensembl_Gene_ID = '%s' ;""" % (iD,))
		cursor = self.executeQuery(queryTrans)[0]
		cols = [column[0] for column in cursor.description]
		infos = cursor.fetchall()
		#If no transcripts for this gene
		trans = [{}] if infos == [] else [dict(zip(cols, row)) for row in infos]
		##
		return {"gene" : gene, "trans" : trans}
		


	
