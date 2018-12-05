#!/usr/bin/python3
#Web
from flask import Flask, g, url_for, request, app, render_template, redirect, jsonify, make_response
#Utils
from classes.persError import dictError #Personnalied error class
from classes.baseDeal import Query

app = Flask(__name__)

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
		cursor = Query().executeQuery(queryGenes)[0]
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
		
		try:
			res = Query().viewGene(iD)
			print("non")
			trans = res['trans']
			genes = res['gene']
			return render_template("geneview.html", infos=genes.values(), trans=trans, 
				gnames=genes.keys(), tnames=[*trans[0].keys()], title="Genes", iD=iD)
		except dictError as e:
			mess=e["errors"]
			status = e["status"]
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
			try:
				checkQuery = Query().queryDel(iD)
				modDate = Query().executeQuery(checkQuery["query"], commit = True)[1]
				if modDate is not None:
					Query().saveDate(modDate)
				return render_template("del.html", iD=iD, title="Genes")
			except dictError as e:
				mess=e["errors"]
				status=e["status"]
				return render_template("error.html", title="Erreur", mess=mess), status
		else:
			status = 405
			mess=Query().error(detail="Vous devez utiliser le formulaire spécifique du gène %s." % iD, status=status,
				source={"query" : "Suppression"})
			return render_template("error.html", title="Erreur", mess=[mess]), status

@app.route("/Genes/new",  methods=['POST', 'GET'])
def genenew():
	"""Route to create a gene.
	Accept both GET and POST methods
	GET : show an empty formular
	POST : create the gene
	"""
	with app.app_context():
		quer=Query().queryAllTable()["query"]
		cursor = Query().executeQuery(quer)[0]
		cols = [desc[0] for desc in cursor.description]
		cols.remove('Transcript_count')
		if request.method=="GET":
			gene=[""]*len(cols)
			return render_template("form.html", title="Genes", cols=cols, default=gene, action="new")

		elif request.method=="POST":
			dicinfos = request.form.to_dict()
			try:
				checkQuery=Query().queryIns(dicinfos)
				quer=checkQuery["query"]
				modDate = Query().executeQuery(quer, commit = True)[1]
				if modDate is not None:
					Query().saveDate(modDate)
				return redirect(url_for('geneview', iD=dicinfos['Ensembl_Gene_ID']), code=302)
			except dictError as e:
				mess = e["errors"]
				status = e["status"]
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
			##
			try:
				checkQuery = Query().queryOneGene(iD)
				##Remove Transcript count from fields
				quer = checkQuery["query"]
				cursor = Query().executeQuery(quer)[0]
				gene = cursor.fetchone()
				cols=[desc[0] for desc in cursor.description]
				cols.remove('Transcript_count')
				gene = [*gene]
				del gene[-1]
				##
				return render_template("form.html", title="Genes", cols=cols, default=gene, action="edit")
			except dictError as e:
				mess = e["errors"]
				status = e["status"]
				return render_template("error.html", title="Erreur", mess=mess), status
				
		if request.method=="POST":
			print(request.form.to_dict())
			try:
				checkQuery = Query().queryEdit(request.form.to_dict(), iD)
				quer=checkQuery["query"]
				modDate = Query().executeQuery(quer, commit=True)[1]
				if modDate is not None:
					Query().saveDate(modDate)
				return redirect(url_for('geneview', iD=iD), code=302)
			except dictError as e:
				mess = e["errors"]
				status = e["status"]
				return render_template("error.html", title="Erreur", mess=mess), status


@app.route("/Transcripts", methods=['GET'])
def trans():
	"""Route for transcript list.
	Accept only GET method
	GET : show the list of 1000 first transcripts
	"""
	with app.app_context():
		queryTrans = 'SELECT Ensembl_Transcript_ID, Transcript_Biotype, Ensembl_Gene_ID FROM Transcripts;'
		cursor = Query().executeQuery(queryTrans)[0]
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
		cursor = Query().executeQuery(queryTran)[0]
		infos = cursor.fetchall()[0]
		tnames = [description[0] for description in cursor.description]
		return render_template("transview.html", iD=iD, tnames=tnames, infos=infos, title="Transcrits")


@app.route("/api/Genes", methods=['GET'])
def apiGenesGet():
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
		etag = Query().getEtag()
		if etag in request.if_none_match:#If ETag is already in cache, do not query again
			status=304
			resp = make_response(jsonify(""), status)
			resp.set_etag(etag) #This is the ETag to use
			return (resp)
		queryAll = Query().queryAllTable()["query"]
		cursor = Query().executeQuery(queryAll)[0]
		genes = cursor.fetchall()
		cols = [desc[0] for desc in cursor.description]
		res = []
		for index, row in enumerate(genes):
			res.append(dict(zip(cols, row)))
			res[index]["href"] = url_for('apiGenesViewiD', iD=res[index]['Ensembl_Gene_ID'], _external=True)
		sortRes = sorted(res, key=lambda x: x['Ensembl_Gene_ID'])
		prev = url_for('apiGenesGet', offset=max(0,offset-100), _external=True)
		nexte = url_for('apiGenesGet', offset=min(offset+100, len(sortRes)), _external=True)
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
	Les champs optionnels doivent être conservés et égaux à null si absents.
	"""
	with app.app_context():
		req = request.json
		if not isinstance(req, list):
			status=418
			mess=Query().error(title="Vous ne passerez pas !", detail="Le fichier JSON est mal formaté",
				status=status, source={"api" : "Insertion de gènes"})
			return jsonify({"errors" : mess}), status
		res ={}
		res["created"] = []
		quers=[]
		iDs=[]
		for gene in req:
			if not isinstance(gene, dict):
				status=418
				mess=Query().error(title="Vous ne passerez pas !", detail="Le fichier JSON est mal formaté",
				status=status, source={"api" : "Insertion de gènes"})
				return jsonify({"errors" : mess}), status
			try:
				quer = Query().queryIns(gene)
				iDs.append(gene["Ensembl_Gene_ID"])
				quers.append(quer["query"])
			except dictError as e:
				mess=e["errors"]
				status=e["status"]
				return jsonify({"errors" : mess}), status
		try:
			assert len(set(iDs))==len(iDs)
		except AssertionError as e:
			status=403
			mess=Query().error(detail="Certains gènes sont en plusieurs copies", status=status, 
				source={"api" : "Insertion de gènes"})
			return jsonify({"errors" : mess}), status
		for index, que in enumerate(quers):
			modDate = Query().executeQuery(que, commit=True)[1]
			res["created"].append(url_for('apiGenesViewiD', iD=req[index]['Ensembl_Gene_ID'], _external=True))
		if modDate is not None:
			Query().saveDate(modDate)
		return jsonify(res), 200


@app.route("/api/Genes/<iD>", methods=['GET'])
def apiGenesViewiD(iD):
	"""API route to visualize a single gene given its iD.
	GET : show the gene in a json format
	"""
	with app.app_context():
		try:
			res = Query().viewGene(iD)
			view = res['gene']
			view['transcripts'] = res['trans']
			status = 200
		except dictError as e:
			view = e["errors"]
			status = e["status"]
		etag = Query().getEtag()
		if etag in request.if_none_match:#If ETag is already in cache, do not query again
			status=304
			resp = make_response(jsonify(""), status)
			resp.set_etag(etag) #This is the ETag to use
			return (resp)
		resp=make_response(jsonify(view), status)
		resp.set_etag(etag)
		return resp

@app.route("/api/Genes/<iD>", methods=['DELETE'])
def apiGenesDeleteiD(iD):
	"""API route to delete a gene given its iD.
	DELETE : delete the gene from the database
	"""
	with app.app_context():
		try:
			checkQuery = Query().queryDel(iD)
			quer = checkQuery["query"]
			modDate = Query().executeQuery(quer, commit = True)[1]
			if modDate is not None:
				Query().saveDate(modDate)
			return jsonify({ "deleted": iD })
		except dictError as e:
			mess=e["errors"]
			status=e["status"]
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
			status=418
			mess=Query().error(title="Vous ne passerez pas !", detail="Le fichier JSON est mal formaté", status=status, 
				source={"api" : "Insertion ou modification d'un gène"})
			return jsonify({"errors" : [mess]}), status
		if req["Ensembl_Gene_ID"]!=iD:
			status=403
			err=Query().error(detail="Les gènes %s et %s ne correspondent pas" % (req["Ensembl_Gene_ID"], iD), 
				status=status, source={"api" : "Insertion ou modification d'un gène"})			
			return jsonify(err), status
		try:
			checkQueryEdit=Query().queryEdit(req, iD)
			checkQueryIns=Query().queryIns(req)
			return jsonify(error)
		except:
			pass
		try:
			checkQueryEdit=Query().queryEdit(req, iD)
			etag=Query().getEtag() #This is the current ETag that any client have to possess when querying
			if etag not in request.if_match:#If ETag not in this list, do not edit the gene
				status=412
				#Client must get the ETag in a proper way to be able to query
				resp = make_response(jsonify(""), status)
				return resp
			quer = checkQueryEdit["query"]
			modDate = Query().executeQuery(quer, commit = True)[1]
			if modDate is not None:
				Query().saveDate(modDate)
			resp = make_response(jsonify({"edited": url_for('apiGenesViewiD', iD=req['Ensembl_Gene_ID'], _external=True)}), 200)
			etag=Query().getEtag() #This is the updated ETag that any client have to obtain before querying
			resp.set_etag(etag)
			return resp
		except dictError as e:
			editErr=e["errors"]
		try:
			checkQueryIns=Query().queryIns(req)
			quer = checkQueryIns["query"]
			modDate = Query().executeQuery(quer, commit = True)[1]
			if modDate is not None:
				Query().saveDate(modDate)
			return jsonify({"created": url_for('apiGenesViewiD', iD=req['Ensembl_Gene_ID'], _external=True)})
		except dictError as e:
			insErr=e["errors"]
			mess=editErr+insErr
			status=400
			return jsonify({"errors" : mess}), status



