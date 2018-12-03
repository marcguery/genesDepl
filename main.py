#!/usr/bin/python3

#Web
from flask import Flask, g, url_for, request, app, render_template, redirect, jsonify, make_response
#Database
import sqlite3
import mysql.connector
#Utils
import json #database infos
import datetime #database state
from hashlib import md5 #ETag hash

app = Flask(__name__)
#Type of database : sql or sqlite
dbtype='sqlite'


def link_db(dbtype):
	"""Get informations needed for connection.
	Need to know the database type
	"""
	with open("details.json") as f:
		infos = json.load(f)
		dbinfos = infos[dbtype]
	f.close()
	return dbinfos

def get_db():
	"""Connection to database.
	"""
	db = getattr(g, '_database', None)
	if db is None:
		if dbtype=='sql':
			dbinfos=link_db(dbtype)
			db = g._database = mysql.connector.connect(
				user=dbinfos['pers']['login'],
				password=dbinfos['pers']['password'],
				host=dbinfos['base']['host'],
				database=dbinfos['base']['database'])
		elif dbtype=='sqlite':
			dbinfos=link_db(dbtype)
			db = g._database = sqlite3.connect(dbinfos['database'])
	return db

def error(**somanyerrors):
	"""Provide a dict containing statements when something went wrong.
	General statement for all errors plus optionnaly statements
	Optionnaly arguments passed to function like 'arg = sentence'
	"""
	#General statement
	err={"error": "Vous ne pouvez pas faire ça comme ça !"}
	if somanyerrors!={}: #If arg(s) passed to function
		for keys in somanyerrors:
			err[keys]=somanyerrors[keys]
	return err

def saveDate(date, append=True):
	"""Save the current state of database in a log file.
	The date of modification (typically provided by executeQuery()) could be in any format.
	Append to log file if True, otherwise overwrite.
	"""
	if append:
		with open("log/last-mod.txt", "a") as f:
			f.write(str(date))
	else:
		with open("log/last-mod.txt", "w") as f:
			f.write(str(date))
	f.close()


def getEtag(date = True, crit = None):
	"""Generate a md5 hash to be passed to ETag header.
	If date is True, takes the last date of modification from log file
	crit argument is a string to be hashed. If both date and crit are provided, 
		hash is a result of them merged
	"""
	if date:
		with open("log/last-mod.txt", "r") as f:
			etag = f.readlines()[-1]
			f.close()
	else:
		etag = ""
	etag = ';'.join([etag, crit]) if crit is not None else etag
	hetag = md5(etag.encode('utf-8')).hexdigest()
	return hetag


def isGeneinBase(giD, iDs):
	"""Check if a given gene is in the database.
	Return an error message for both cases (could be used regarding the context,
		e.g. editing non existing gene or creating existing gene)
	If gene is in database first argument returned is 1 otherwise 0
	"""
	if giD in iDs:
		mess=error(e1="Le gène %s existe déjà." % giD)
		status = 403
		return [1, {"error" : mess, "status" : status}]
	else:
		mess=error(e1="Le gène %s n'existe pas." % giD)
		status = 403
		return [0, {"error" : mess, "status" : status}]

def verifGene(dictCont):
	"""Check if informations of a gene are correct.
	Need a dictionnary for one gene
	Return 1 and a dictionnary of well formated fields if success
	"""
	##Attribut length verification
	if len(dictCont)!=7:
		mess=error(e1="Nombre d'attributs inattendus du gène %s." % dictCont["Ensembl_Gene_ID"])
		status = 418
		return [0, {"error" : mess, "status" : status}]
	##
	##Necessary keys verification
	for oblgKeys in ["Ensembl_Gene_ID", "Chromosome_Name", "Gene_Start", "Gene_End"]:
		if dictCont[oblgKeys] == "":
			mess=error(e1="Champs manquants du gène %s." % dictCont["Ensembl_Gene_ID"], 
				e2="Ensembl_Gene_ID, Chromosome_Name, Gene_Start et Gene_End ne doivent pas être vides.")
			status = 400
			return [0, {"error" : mess, "status" : status}]
	##
	##Format verification
	#String and integer formating
	try:
		for strKeys in ["Ensembl_Gene_ID", "Chromosome_Name", "Band", "Associated_Gene_Name"]:
			dictCont[strKeys]=str(dictCont[strKeys])
		for intKeys in ["Strand", "Gene_Start", "Gene_End"]:
			dictCont[intKeys]=int(dictCont[intKeys])
	except:
		mess=error(e1="Erreur de typage du gène %s." % dictCont["Ensembl_Gene_ID"], 
			e2="Ensembl_Gene_ID, Chromosome_Name, Band et Associated_Gene_Name doivent être des chaines de carcatères.",
			e3="Strand, Gene_Start et Gene_End doivent être des entiers.")
		status = 400
		return [0, {"error" : mess, "status" : status}]
	#
	#Difference between End and Start
	if dictCont["Gene_End"]<= dictCont["Gene_Start"]:
		mess=error(e1="Erreur de typage du gène %s." % dictCont["Ensembl_Gene_ID"],
			e2="Gene_Start doit être stricitement inférieur à Gene_End.")
		status = 400
		return [0, {"error" : mess, "status" : status}]
	#
	##
	return[1, dictCont]

def executeQuery(query, commit = False):
	"""Execute a query in the database.
	Require a query
	Commit is necessary when creating, editing or deleting
	Return a cursor object and a date of modification if commit is True
	"""
	modDate = None
	cursor = get_db().cursor()
	cursor.execute(query)
	if commit:
		get_db().commit() #PERMANENT CHANGE
		modDate = datetime.datetime.now()
	return [cursor, modDate]

def queryAllTable(table="Genes"):
	"""Generate a query of all elements in a given table.
	Default table is Genes
	Return 1 (success) and the string formated query
	"""
	queryKeyes = ("SELECT * FROM %s;" % (table,))
	return [1, {"query" : queryKeyes}]

def queryOneGene(iD):
	"""Generate a query to pick one gene in the database.
	iD must belong to Ensembl_Gene_ID column
	Return 1 (success) and the string formated query
	"""
	queryGenes=queryAllTable()[1]["query"]
	cursor = executeQuery(queryGenes)[0]
	genes = cursor.fetchall()
	iDs = map(lambda x : x[0], genes)
	inBase = isGeneinBase(iD, iDs)
	##Check if gene is in database first
	if not inBase[0]:
		return [0, inBase[1]]
	queryGene=("SELECT G.* FROM Genes G WHERE G.Ensembl_Gene_ID = '%s' ;" % (iD,))
	return [1, {"query" : queryGene}]

def queryIns(form):
	"""Generate a query to insert one gene in the database.
	iD must belong to Ensembl_Gene_ID column
	Return 1 (success) and the string formated query
	"""
	dicinfos=form
	##Verification
	verif = verifGene(dicinfos)
	queryAll=queryAllTable()[1]["query"]
	cursor = executeQuery(queryAll)[0]
	genes = cursor.fetchall()
	iDs = map(lambda x : x[0], genes)
	inBase = isGeneinBase(dicinfos["Ensembl_Gene_ID"], iDs)
	##
	if inBase[0]: #if gene already exists, error
		return [0, inBase[1]]
	if verif[0]:
		cols=', '.join([*verif[1].keys()])
		vals=', '.join(map(lambda x: "'" + str(x) + "'" , [*verif[1].values()]))
		queryIns = ("INSERT INTO Genes (%s) VALUES (%s)" % (cols, vals,))
		print(queryIns)
		return [1, {"query" : queryIns}]
	else:
		return [0, verif[1]]

def queryEdit(form, iD):
	"""Generate a query to edit an existing gene in the database.
	Require a dictionnary of one gene and its iD
	Return 1 (success) and the string formated query
	"""
	dicinfos = form
	dicinfos["Ensembl_Gene_ID"]=iD #Reset Id if it has been changed
	comb = []
	##Verification
	verif = verifGene(dicinfos)
	queryAll=queryAllTable()[1]["query"]
	cursor = executeQuery(queryAll)[0]
	genes = cursor.fetchall()
	iDs = map(lambda x : x[0], genes)
	inBase = isGeneinBase(iD, iDs)
	##
	if not inBase[0]: #if gene does not exist, error
		return [0, inBase[1]]
	if verif[0]:
		for col in dicinfos:
			comb.append("%s='%s'" % (col, dicinfos[col]))
		queryEdit = ("UPDATE Genes SET %s WHERE Ensembl_Gene_ID = '%s' ;" % (",".join([*comb]), iD,))
		return [1, {"query" : queryEdit}]
	else:
		return [0, verif[1]]

def queryDel(iD):
	"""Generate a query to delete an existing gene from the database.
	Require gene iD
	Return 1 (success) and the string formated query
	"""
	##Verification
	queryAll=queryAllTable()[1]["query"]
	cursor = executeQuery(queryAll)[0]
	genes = cursor.fetchall()
	iDs = map(lambda x : x[0], genes)
	inBase = isGeneinBase(iD, iDs)
	##
	if not inBase[0]: #if gene does not exist, error
		return [0, inBase[1]]
	queryDel = ("DELETE FROM Genes WHERE Ensembl_Gene_ID = '%s' ;" % (iD,))
	return [1, {"query" : queryDel}]

def viewGene(iD):
	"""Give the representation for a given gene.
	`gene` key points to a dictionnary of the gene
	`trans` key points to a list of dictionnary of transcripts
	Return 1 (success) and a dictionnary of gene and its transcripts if successed
	"""
	##
	##Gene
	one = queryOneGene(iD)
	if one[0]:
		queryOne = one[1]["query"]
	else:
		return [0, one[1]]
	cursor = executeQuery(queryOne)[0]
	info = cursor.fetchone()
	cols = [description[0] for description in cursor.description]
	gene = dict(zip(cols, info))
	##
	##Transcripts
	queryTrans = ("""SELECT T.Ensembl_Transcript_ID, T.Transcript_Start, T.Transcript_End
	FROM Transcripts T WHERE T.Ensembl_Gene_ID = '%s' ;""" % (iD,))
	cursor = executeQuery(queryTrans)[0]
	cols = [column[0] for column in cursor.description]
	infos = cursor.fetchall()
	#If no transcripts for this gene
	trans = [{}] if infos == [] else [dict(zip(cols, row)) for row in infos]
	##
	return [1, {"gene" : gene, "trans" : trans}]


@app.teardown_appcontext
def close_connection(exception):
	"""Close connection to database.
	"""
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()


@app.route("/")
def root():
	"""Base route.
	Show the main links available in the website
	"""
	l1=("Liste des gènes", url_for('genes'))
	l2=("Liste des transcrits", url_for('trans'))
	l3=("Doom", url_for('doom'))
	links = [l1,l2,l3]
	return render_template("base.html", links=links, title="Bienvenue")

@app.route("/Doom")
def doom():
	"""Doom route.
	Play Doom when you are bored
	"""
	return render_template("doom.html", title="DOOM")

@app.route("/Genes", methods=['GET'])
def genes():
	"""Route for gene list.
	Accept only GET method
	GET : show the list of 1000 first genes
	"""
	with app.app_context():
		queryGenes = 'SELECT Ensembl_Gene_ID, Associated_Gene_Name FROM Genes;'
		cursor = executeQuery(queryGenes)[0]
		genes = cursor.fetchall()
		subgenes=genes[0:1000]
		subgenes = sorted(subgenes, key=lambda x: x[0])
		return render_template("genes.html", genes=subgenes, title="Genes")

@app.route("/Genes/view/<iD>", methods=['GET'])
def geneview(iD):
	"""Route to show a specific gene given its iD.
	Accept only GET method
	GET : show a gene and its transcripts
	"""
	with app.app_context():
		res = viewGene(iD)
		if res[0]:
			trans = res[1]['trans']
			genes = res[1]['gene']
			return render_template("geneview.html", infos=genes.values(), trans=trans, 
				gnames=genes.keys(), tnames=[*trans[0].keys()], title="Genes", iD=iD)
		else:
			mess=res[1]["error"]
			status = res[1]["status"]
			return render_template("error.html", title="Erreur", mess=mess), status

@app.route("/Genes/del/<iD>",  methods=['POST', 'GET'])
def genedel(iD):
	"""Route to delete a gene.
	Accept both GET and POST methods
	GET : raise an error
	POST : delete the gene
	"""
	with app.app_context():
		if request.method=="POST":
			checkQuery = queryDel(iD)
			if checkQuery[0]:
				modDate = executeQuery(checkQuery[1]["query"], commit = True)[1]
				if modDate is not None:
					saveDate(modDate)
				return render_template("del.html", iD=iD, title="Genes")
			else:
				mess=checkQuery[1]["error"]
				status=checkQuery[1]["status"]
				return render_template("error.html", title="Erreur", mess=mess), status
		else:
			mess=error(e1="Vous devez utiliser le formulaire spécifique du gène %s." % iD)
			status = 405
			return render_template("error.html", title="Erreur", mess=mess), status

@app.route("/Genes/new",  methods=['POST', 'GET'])
def genenew():
	"""Route to create a gene.
	Accept both GET and POST methods
	GET : show an empty formular
	POST : create the gene
	"""
	with app.app_context():
		quer=queryAllTable()[1]["query"]
		cursor = executeQuery(quer)[0]
		cols = [desc[0] for desc in cursor.description]
		cols.remove('Transcript_count')
		if request.method=="GET":
			gene=[""]*len(cols)
			return render_template("form.html", title="Genes", cols=cols, default=gene, action="new")

		elif request.method=="POST":
			dicinfos = request.form.to_dict()
			checkQuery=queryIns(dicinfos)
			if checkQuery[0]:
				quer=checkQuery[1]["query"]
				modDate = executeQuery(quer, commit = True)[1]
				if modDate is not None:
					saveDate(modDate)
				return redirect(url_for('geneview', iD=dicinfos['Ensembl_Gene_ID']), code=302)
			else:
				mess = checkQuery[1]["error"]
				status = checkQuery[1]["status"]
				return render_template("error.html", title="Erreur", mess=mess), status

@app.route("/Genes/edit/<iD>",  methods=['POST', 'GET'])
def geneedit(iD):
	"""Route to edit a gene.
	Accept both GET and POST methods
	GET : show a filled formular
	POST : edit the gene
	"""
	with app.app_context():
		if request.method=="GET":
			##Verification
			checkQuery = queryOneGene(iD)
			##
			if not checkQuery[0]:
				mess = checkQuery[1]["error"]
				status = checkQuery[1]["status"]
				return render_template("error.html", title="Erreur", mess=mess), status
			else:
				##Remove Transcript count from fields
				quer = checkQuery[1]["query"]
				cursor = executeQuery(quer)[0]
				gene = cursor.fetchone()
				cols=[desc[0] for desc in cursor.description]
				cols.remove('Transcript_count')
				gene = [*gene]
				del gene[-1]
				##
				return render_template("form.html", title="Genes", cols=cols, default=gene, action="edit")
		if request.method=="POST":
			print(request.form.to_dict())
			checkQuery = queryEdit(request.form.to_dict(), iD)
			if checkQuery[0]:
				quer=checkQuery[1]["query"]
				modDate = executeQuery(quer, commit=True)[1]
				if modDate is not None:
					saveDate(modDate)
				return redirect(url_for('geneview', iD=iD), code=302)
			else:
				mess = checkQuery[1]["error"]
				status = checkQuery[1]["status"]
				return render_template("error.html", title="Erreur", mess=mess), status


@app.route("/Transcripts", methods=['GET'])
def trans():
	"""Route for transcript list.
	Accept only GET method
	GET : show the list of 1000 first transcripts
	"""
	with app.app_context():
		queryTrans = 'SELECT Ensembl_Transcript_ID, Transcript_Biotype, Ensembl_Gene_ID FROM Transcripts;'
		cursor = executeQuery(queryTrans)[0]
		trans = cursor.fetchall()
		subtrans=trans[1:1000]
		return render_template("trans.html", trans=subtrans, title="Transcrits")

@app.route("/Transcrits/<iD>", methods=['GET'])
def transview(iD):
	"""Route to show a transcript given its iD.
	Accept only GET method
	GET : show the transcript
	"""
	with app.app_context():
		queryTran = ("SELECT * FROM Transcripts WHERE Ensembl_Transcript_ID = '%s';" % (iD,))
		cursor = executeQuery(queryTran)[0]
		infos = cursor.fetchall()[0]
		tnames = [description[0] for description in cursor.description]
		return render_template("transview.html", iD=iD, tnames=tnames, infos=infos, title="Transcrits")

@app.route("/api/Genes/<iD>", methods=['GET'])
def apiGenesViewiD(iD):
	"""API route to visualize a single gene given its iD.
	GET : show the gene in a json format
	"""
	with app.app_context():
		res = viewGene(iD)
		if res[0]:
			view = res[1]['gene']
			view['transcripts'] = res[1]['trans']
			status = 200
		else:
			view = res[1]["error"]
			status = res[1]["status"]
		return jsonify(view), status

@app.route("/api/Genes/<iD>", methods=['DELETE'])
def apiGenesDeleteiD(iD):
	"""API route to delete a gene given its iD.
	DELETE : delete the gene from the database
	"""
	with app.app_context():
		checkQuery = queryDel(iD)
		if checkQuery[0]:
			quer = checkQuery[1]["query"]
			modDate = executeQuery(quer, commit = True)[1]
			if modDate is not None:
				saveDate(modDate)
			return jsonify({ "deleted": iD })
		else:
			mess=checkQuery[1]["error"]
			status=checkQuery[1]["status"]
			return jsonify(mess), status

@app.route("/api/Genes/<iD>", methods=['PUT'])
def apiGenesPutiD(iD):
	"""API route to edit/create a gene given its iD.
	PUT : edit the gene if it exists
	PUT : create the gene if it does not exist
	Accept a dictionnary of one well formated gene (see apiPostGenes)
	Return 304 if request has not changed since last request (for editing).
		check values of If-None-Match (request) and ETag (response) headers
	"""
	with app.app_context():
		req=request.json
		if not isinstance(req, dict):
			mess=error(e2="Vous ne passerez pas !")
			status=418
			return jsonify(mess), status
		if req["Ensembl_Gene_ID"]!=iD:
			err=error(e1="Les gènes %s et %s ne correspondent pas" % (req["Ensembl_Gene_ID"], iD))
			status=403
			return jsonify(err), status
		checkQueryEdit=queryEdit(req, iD)
		checkQueryIns=queryIns(req)
		if checkQueryEdit[0] and checkQueryIns[0]:
			return jsonify(error())
		if checkQueryEdit[0]:
			etag=getEtag(date=False, crit=str(req))
			if etag in request.if_none_match:
				resp = make_response("", 304)
				resp.set_etag(etag)
				return (resp)
			quer = checkQueryEdit[1]["query"]
			modDate = executeQuery(quer, commit = True)[1]
			if modDate is not None:
				saveDate(modDate)
			resp = make_response(jsonify({"edited": url_for('apiGenesViewiD', iD=req['Ensembl_Gene_ID'], _external=True)}), 200)
			resp.set_etag(etag)
			return resp
		elif checkQueryIns[0]:
			quer = checkQueryIns[1]["query"]
			modDate = executeQuery(quer, commit = True)[1]
			if modDate is not None:
				saveDate(modDate)
			return jsonify({"created": url_for('apiGenesViewiD', iD=req['Ensembl_Gene_ID'], _external=True)})
		else:
			mess=[{"edition" : checkQueryEdit[1]["error"]}, {"creation" : checkQueryIns[1]["error"]}]
			status=400
			return jsonify(mess), status


@app.route("/api/Genes", methods=['GET'])
def apiGetGenes():
	"""API route to show genes.
	Accept only GET method
	GET : show a list of 100 genes given an optional start index
	Genes are sorted by iD value
	Start index is 0 by default (first gene of the database)
	example of use : /api/Genes/?offset=100
	Return 304 if database last modification and offset have not changed since last request.
		check values of If-None-Match (request) and ETag (response) headers
	"""
	with app.app_context():
		offset = request.args.get('offset', default = 0, type = int)
		etag = getEtag(crit=str(offset))
		if etag in request.if_none_match:
			resp = make_response("", 304)
			resp.set_etag(etag)
			return (resp)
		queryAll = queryAllTable()[1]["query"]
		cursor = executeQuery(queryAll)[0]
		genes = cursor.fetchall()
		cols = [desc[0] for desc in cursor.description]
		res = []
		for index, row in enumerate(genes):
			res.append(dict(zip(cols, row)))
			res[index]["href"] = url_for('apiGenesViewiD', iD=res[index]['Ensembl_Gene_ID'], _external=True)
		sortRes = sorted(res, key=lambda x: x['Ensembl_Gene_ID'])
		prev = url_for('apiGetGenes', offset=max(0,offset-100), _external=True)
		nexte = url_for('apiGetGenes', offset=min(offset+100, len(sortRes)), _external=True)
		geneSet = {"items": sortRes[offset:offset+99],
		"first": offset+1,
		"last": offset+100,
		"prev": prev,
		"next": nexte,
		}
		resp = make_response(jsonify(geneSet), 200)
		resp.set_etag(etag)
		return resp

@app.route("/api/Genes", methods=['POST'])
def apiPostGenes():
	"""API route to create genes.
	Accept only POST method
	POST : create genes given json formated genes
	Json should contain a specific number of fields 
		and acceptable values (i.e. string or int)
	Genes should be an array of objects 
		(corresponding to list of dictionnaries in Python)
	example of acceptable json formated genes:
	[{"Ensembl_Gene_ID": "ENSG00000000003",
	"Associated_Gene_Name": "TSPAN6",
	"Chromosome_Name": "X",
	"Band": "q22.1",
	"Strand": -1,
	"Gene_Start": 99883667,
	"Gene_End": 99894988
	},
	{
	"Ensembl_Gene_ID": "ENSG00000200378",
	"Associated_Gene_Name": "RNU5B-4P",
	"Chromosome_Name": "5",
	"Band": "q31.2",
	"Strand": 1,
	"Gene_Start": 138783596,
	"Gene_End": 138783706
	}
	]
	"""
	with app.app_context():
		req = request.json
		if not isinstance(req, list):
			mess=error(e2="Vous ne passerez pas !")
			status=418
			return jsonify(mess), status
		res ={}
		res["created"] = []
		quers=[]
		for gene in req:
			if not isinstance(gene, dict):
				mess=error(e2="Vous ne passerez pas !")
				status=418
				return jsonify(mess), status
			quer = queryIns(gene)
			if quer[0]:
				quers.append(quer[1]["query"])
			else:
				return jsonify(quer[1]["error"]), quer[1]["status"]
		for index, que in enumerate(quers):
			modDate = executeQuery(que, commit=True)[1]
			res["created"].append(url_for('apiGenesViewiD', iD=req[index]['Ensembl_Gene_ID'], _external=True))
		if modDate is not None:
			saveDate(modDate)
		return jsonify(res), 200

