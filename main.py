#!/usr/bin/python3

from flask import Flask, g, url_for, request, app, render_template, redirect, jsonify
import sqlite3
import json
import mysql.connector

app = Flask(__name__)
dbtype='sql'

def link_db(dbtype):
	with open("details.json") as f:
		infos = json.load(f)
		dbinfos = infos[dbtype]
	f.close()
	return dbinfos

def get_db():
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
	err={"error": "Vous ne pouvez pas faire ça comme ça !"}
	if somanyerrors!={}:
		for keys in somanyerrors:
			err[keys]=somanyerrors[keys]
	return err

def allGenes():
	cursor = get_db().cursor()
	queryKeyes = 'SELECT * FROM Genes;'
	cursor.execute(queryKeyes)
	genes = cursor.fetchall()
	cols = [description[0] for description in cursor.description]
	return [cols, genes]

def oneGene(iD):
	cursor = get_db().cursor()
	queryGene=("SELECT G.* FROM Genes G WHERE G.Ensembl_Gene_ID = '%s' ;" % iD)
	cursor.execute(queryGene)
	gene = cursor.fetchone()
	cols = [description[0] for description in cursor.description]
	return [cols, gene]

def viewGene(iD):
	cursor = get_db().cursor()
	cols, infos = oneGene(iD)
	if infos == []:
		mess=error(e1="Ce gène n'existe pas")
		status=400
		return [0, {"error" : mess, "status" : status}]
	else:
		gene = [dict(zip(cols, infos))]
		queryTrans = ("""SELECT T.Ensembl_Transcript_ID, T.Transcript_Start, T.Transcript_End
		FROM Transcripts T WHERE T.Ensembl_Gene_ID = '%s' ;""" % iD)
		cursor.execute(queryTrans)
		cols = [column[0] for column in cursor.description]
		infos = cursor.fetchall()
		trans = [{}] if infos == [] else [dict(zip(cols, row)) for row in infos]
		return [1, {"gene" : gene, "trans" : trans}]

def verifGene(dictCont):
	try:
		int(dictCont["Strand"])
		int(dictCont["Gene_Start"])
		int(dictCont["Gene_End"])
	except:
		mess=error(e1="Erreur de typage.", e2="Strand, Gene_Start et Gene_End doivent être des entiers.")
		status = 400
		return [0, {"error" : mess, "status" : status}]
	if int(dictCont["Gene_End"])<= int(dictCont["Gene_Start"]):
		mess=error(e2="Gene_Start doit être stricitement inférieur à Gene_End.")
		status = 400
		return [0, {"error" : mess, "status" : status}]

	types=[isinstance(dictCont["Ensembl_Gene_ID"], str),
		isinstance(dictCont["Chromosome_Name"], str),
		isinstance(dictCont["Band"], str),
		isinstance(dictCont["Associated_Gene_Name"], str)
		]
	if (not all(types)):
		mess=error(e1="Erreur de typage.", 
			e2="Ensembl_Gene_ID, Chromosome_Name, Band et Associated_Gene_Name doivent être des chaines de carcatères.")
		status = 400
		return [0, {"error" : mess, "status" : status}]

	for oblgKeys in ["Ensembl_Gene_ID", "Chromosome_Name", "Gene_Start", "Gene_End"]:
		if dictCont[oblgKeys] == "":
			mess=error(e1="Champs manquants.", 
				e2="Ensembl_Gene_ID, Chromosome_Name, Gene_Start et Gene_End ne doivent pas être vides.")
			status = 400
			return [0, {"error" : mess, "status" : status}]

	if len(dictCont)!=7:
		mess=error(e1="Attributs supplémentaires inattendus.")
		status = 418
		return [0, {"error" : mess, "status" : status}]
	return[1, {}]

def createGene(form):
	dicinfos=form
	verif = verifGene(dicinfos)
	allnames=allGenes()[1]
	iDs = map(lambda x : x[0], allnames)
	if dicinfos["Ensembl_Gene_ID"] in iDs:
		mess=error(e1="Le gène existe déjà.")
		status = 403
		return [0, {"error" : mess, "status" : status}]
	if verif[0]:
		cursor = get_db().cursor()
		queryIns = "INSERT INTO Genes (%s) VALUES (%s)" % (', '.join([*dicinfos.keys()]), 
			', '.join(map(lambda x: "'" + str(x) + "'" , [*dicinfos.values()])))
		cursor.execute(queryIns)
		get_db().commit()
		return [1, dicinfos]
	else:
		return verif

def editGene(form, iD):
	dicinfos = form
	comb = []
	verif = verifGene(dicinfos)
	if verif[0]:
		for col in dicinfos:
			comb.append("%s='%s'" % (col, dicinfos[col]))
		cursor = get_db().cursor()
		queryIns = ("UPDATE Genes SET %s WHERE Ensembl_Gene_ID = '%s' ;" % (",".join([*comb]), iD))
		cursor.execute(queryIns)
		get_db().commit()
		mess=("Le gène %s a bien été modifié !" % iD)
		return [1, {"mess" : mess}]
	else:
		return verif

@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()


@app.route("/")
def root():
	l1=("Liste des gènes", url_for('genes'))
	l2=("Liste des transcrits", url_for('trans'))
	l3=("Doom", url_for('doom'))
	links = [l1,l2,l3]
	return render_template("base.html", links=links, title="Bienvenue")

@app.route("/Doom")
def doom():
	return render_template("doom.html", title="DOOM")

@app.route("/Genes", methods=['GET', 'POST'])
def genes():
	with app.app_context():
		cursor = get_db().cursor()
		queryGenes = 'SELECT Ensembl_Gene_ID, Associated_Gene_Name FROM Genes;'
		cursor.execute(queryGenes)
		genes = cursor.fetchall()
		subgenes=genes[0:1000]
		return render_template("genes.html", genes=subgenes, title="Genes")

@app.route("/Genes/view/<iD>")
def geneview(iD):
	with app.app_context():
		res = viewGene(iD)
		if res[0]:
			trans = res[1]['trans']
			genes = res[1]['gene'][0]
			return render_template("geneview.html", infos=genes.values(), trans=trans, 
				gnames=genes.keys(), tnames=[*trans[0].keys()], title="Genes", iD=iD)
		else:
			mess=res[1]["error"]
			status = res[1]["status"]
			return render_template("error.html", title="Erreur", mess=mess), status

@app.route("/Genes/del/<iD>",  methods=['POST', 'GET'])
def genedel(iD):
	with app.app_context():
		if request.method=="POST":
			cursor = get_db().cursor()
			queryDel = ("DELETE FROM Genes WHERE Ensembl_Gene_ID = '%s' ;" % iD)
			cursor.execute(queryDel)
			get_db().commit() #PERMANENT REMOVAL
			back=url_for('genes')
			return render_template("del.html", iD=iD, back=back, title="Genes")
		else:
			mess=error(e1="Vous devez utiliser le formulaire spécifique.")
			status = 405
			return render_template("error.html", title="Erreur", mess=mess), status

@app.route("/Genes/new",  methods=['POST', 'GET'])
def genenew():
	with app.app_context():
		cols=allGenes()[0]
		cols.remove('Transcript_count')
		if request.method=="GET":
			return render_template("new.html", title="Genes", cols=cols)

		elif request.method=="POST":
			dicinfos=createGene(request.form.to_dict())
			if dicinfos[0]:
				return redirect(url_for('geneview', iD=dicinfos[1]['Ensembl_Gene_ID']), code=302)
			else:
				mess = dicinfos[1]["error"]
				status = dicinfos[1]["status"]
				return render_template("error.html", title="Erreur", mess=mess), status

@app.route("/Genes/edit/<iD>",  methods=['POST', 'GET'])
def geneedit(iD):
	with app.app_context():
		cols, gene = oneGene(iD)
		cols.remove('Transcript_count')
		gene = [*gene]
		del gene[-1]
		if request.method=="GET":
			return render_template("edit.html", title="Genes", cols=cols, default=gene, iD=iD)
		if request.method=="POST":
			edit = editGene(request.form.to_dict(), iD)
			if edit[0]:
				return redirect(url_for('geneview', iD=iD), code=302)
			else:
				mess = edit[1]["error"]
				status = edit[1]["status"]
				return render_template("error.html", title="Erreur", mess=mess), status


@app.route("/Transcripts")
def trans():
	with app.app_context():
		cursor = get_db().cursor()
		queryTrans = 'SELECT Ensembl_Transcript_ID, Transcript_Biotype, Ensembl_Gene_ID FROM Transcripts;'
		cursor.execute(queryTrans)
		trans = cursor.fetchall()
		subtrans=trans[1:1000]
		return render_template("trans.html", trans=subtrans, title="Transcrits")

@app.route("/Transcrits/<iD>")
def transview(iD):
	with app.app_context():
		cursor = get_db().cursor()
		queryTran = ("SELECT * FROM Transcripts WHERE Ensembl_Transcript_ID = '%s';" % iD)
		cursor.execute(queryTran)
		infos = cursor.fetchall()[0]
		tnames = [description[0] for description in cursor.description]
		return render_template("transview.html", iD=iD, tnames=tnames, infos=infos, title="Transcrits")

@app.route("/api/Genes/<iD>", methods=['GET', 'DELETE'])
def apiGenesId(iD):
	with app.app_context():
		if request.method=='GET':
			res = viewGene(iD)
			if res[0]:
				view = res[1]['gene']
				view[0]['transcripts'] = res[1]['trans']
				status = 200
			else:
				view = res[1]["error"]
				status = res[1]["status"]
			return jsonify(view), status
		elif request.method=='DELETE':
			return jsonify(error), 200

@app.route("/api/Genes", methods=['POST', 'GET'])
def apiGenes():
	if request.method=="GET":
		with app.app_context():
			offset = request.args.get('offset', default = 0, type = int)
			cols, genes=allGenes()
			res = []
			for index, row in enumerate(genes):
				res.append(dict(zip(cols, row)))
				res[index]["href"] = url_for('apiGenesId', iD=res[index]['Ensembl_Gene_ID'], _external=True)
			sortRes = sorted(res, key=lambda x: x['Ensembl_Gene_ID'])
			prev = url_for('apiGenes', offset=max(0,offset-100), _external=True)
			nexte = url_for('apiGenes', offset=min(offset+100, len(sortRes)), _external=True)
			geneSet = {"items": sortRes[offset:offset+99],
			"first": offset+1,
			"last": offset+100,
			"prev": prev,
			"next": nexte,
			}
			return jsonify(geneSet)
	elif request.method == "POST":
		with app.app_context():
			req = request.json
			res = createGene(req)
			if res[0]:
				return jsonify({"created": [url_for('apiGenesId', iD=res[1]['Ensembl_Gene_ID'], _external=True)]}), 201
			else:
				return jsonify(res[1]["error"]), res[1]["status"]

