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

def createGene(form):
	cursor = get_db().cursor()
	queryKeyes = 'SELECT * FROM Genes;'
	cursor.execute(queryKeyes)
	allnames = cursor.fetchall()
	cols = [description[0] for description in cursor.description]
	dicinfos=form
	verif=[elm[0] for elm in allnames]
	if dicinfos["Ensembl_Gene_ID"] in verif:
		mess=error(e="Vous ne pouvez pas ajouter un gène existant.")
		return [0, mess]
	if '' in dicinfos.values():
		mess=error(e="Vous devez remplir tous les champs.")
		return [0, mess]
	queryIns = "INSERT INTO Genes (%s) VALUES (%s)" % (', '.join([*dicinfos.keys()]), 
		', '.join(map(lambda x: "'" + str(x) + "'" , [*dicinfos.values()])))
	cursor.execute(queryIns)
	get_db().commit()
	return [1, dicinfos]

@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()


@app.route("/")
def root():
	l1=("Liste des gènes", url_for('genes'))
	l2=("Liste des transcrits", url_for('trans'))
	links = [l1,l2]
	return render_template("base.html", links=links, title="Bienvenue")

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
		cursor = get_db().cursor()
		queryInfos = ("SELECT G.* FROM Genes G WHERE G.Ensembl_Gene_ID = '%s' ;" % iD)
		queryTrans = ("""SELECT T.Ensembl_Transcript_ID, T.Transcript_Start, T.Transcript_End
			FROM Transcripts T WHERE T.Ensembl_Gene_ID = '%s' ;""" % iD)
		cursor.execute(queryInfos)
		try:
			infos = cursor.fetchall()[0]
			gnames = [description[0] for description in cursor.description]
			cursor.execute(queryTrans)
			trans=cursor.fetchall()
			tnames = [description[0] for description in cursor.description]
			return render_template("geneview.html", infos=infos, trans=trans, gnames=gnames, tnames=tnames, title="Genes", iD=iD)
		except:
			mess=error(e1="Ce gène n'existe pas")
			return render_template("error.html", title="Erreur", mess=mess)

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
			mess=error(e="Vous devez utiliser le formulaire spécifique.")
			return render_template("error.html", title="Erreur", mess=mess)

@app.route("/Genes/new",  methods=['POST', 'GET'])
def genenew():
	with app.app_context():
		cursor = get_db().cursor()
		queryKeyes = 'SELECT * FROM Genes;'
		cursor.execute(queryKeyes)
		allnames = cursor.fetchall()
		cols = [description[0] for description in cursor.description]

		if request.method=="GET":
			return render_template("new.html", title="Genes", cols=cols)

		elif request.method=="POST":
			dicinfos=createGene(request.form.to_dict())
			if dicinfos[0]:
				return redirect(url_for('geneview', iD=dicinfos[1]['Ensembl_Gene_ID']), code=302)
			else:
				return render_template("error.html", title="Erreur", mess=dicinfos[1])

@app.route("/Genes/edit/<iD>",  methods=['POST', 'GET'])
def geneedit(iD):
	with app.app_context():
		cursor = get_db().cursor()
		queryEdit=("SELECT G.* FROM Genes G WHERE G.Ensembl_Gene_ID = '%s' ;" % iD)
		cursor.execute(queryEdit)
		default = cursor.fetchall()[0]
		cols = [description[0] for description in cursor.description]
		if request.method=="GET":
			return render_template("edit.html", title="Genes", cols=cols[1:], default=default[1:], iD=iD)
		if request.method=="POST":
			dicinfos=request.form.to_dict(flat=False)
			comb=[]
			for col in dicinfos:
				if dicinfos[col][0]=="":
					mess=error(e="Vous ne pouvez pas laisser un champ vide.")
					return render_template("error.html", title="Erreur", mess=mess)
				else:
					comb.append("%s='%s'" % (col, dicinfos[col][0]))
			queryIns = ("UPDATE Genes SET %s WHERE Ensembl_Gene_ID = '%s' ;" % (",".join([*comb]), iD))
			cursor.execute(queryIns)
			get_db().commit()
			mess=("Le gène %s a bien été modifié !" % iD)
			return redirect(url_for('geneview', iD=iD), code=302)
		return


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

@app.route("/api/Genes/<iD>", methods=['GET'])
def apiGenesId(iD):
	with app.app_context():
		cursor = get_db().cursor()
		queryInfos = ("SELECT G.* FROM Genes G WHERE G.Ensembl_Gene_ID = '%s' ;" % iD)
		queryTrans = ("""SELECT T.Ensembl_Transcript_ID, T.Transcript_Start, T.Transcript_End
			FROM Transcripts T WHERE T.Ensembl_Gene_ID = '%s' ;""" % iD)
		cursor.execute(queryInfos)
		infos = cursor.fetchall()
		if infos == []:
			return jsonify(error(e1="Ce gène n'existe pas"))
		else:
			columns = [column[0] for column in cursor.description]
			gene = []
			for row in infos:
					gene.append(dict(zip(columns, row)))
			cursor.execute(queryTrans)
			columns = [column[0] for column in cursor.description]
			trans = []
			for row in cursor.fetchall():
					trans.append(dict(zip(columns, row)))
			res = gene
			res[0]['transcripts'] = trans
			return jsonify(res)

@app.route("/api/Genes", methods=['POST', 'GET'])
def apiGenes():
	if request.method=="GET":
		with app.app_context():
			offset = request.args.get('offset', default = 0, type = int)
			cursor = get_db().cursor()
			queryGenes = 'SELECT * FROM Genes;'
			cursor.execute(queryGenes)
			columns = [column[0] for column in cursor.description]
			res = []
			for index, row in enumerate(cursor.fetchall()):
				res.append(dict(zip(columns, row)))
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
	elif request.method=="POST":
		with app.app_context():
			req = request.json
			print(req)
			res = createGene(req)
			if res[0]:
				return jsonify({"created": [url_for('apiGenesId', iD=res[1]['Ensembl_Gene_ID'], _external=True)]})
			else:
				return jsonify(res[1])

