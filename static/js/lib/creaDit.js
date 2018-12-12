
function formToObj(form){
	/*{
	"Ensembl_Gene_ID": "ENSG00000200378",
	"Associated_Gene_Name": "RNU5B-4P",
	"Chromosome_Name": "5",
	"Band": "q31.2",
	"Strand": 1,
	"Gene_Start": 138783596,
	"Gene_End": 138783706
	}*/
	let fields = form.getElementsByClassName("form-control");
	let geneObj= {};
	for (let i = 0; i < fields.length; i++) {
		geneObj[fields[i].name]=fields[i].value;
	}
	return geneObj
}

function getEtag(url, req){
	return fetch(url, req).then((response) => {
		// cette fonction est appelée lorsque
		// les en-têtes de la réponse ont été reçu
		if (!response.ok) {
			throw ("Error " + response.status);
		}
		let etag = response.headers.get('etag'); // attend la contenu
		return etag
	}).then((data) => {
		// cette fonction est appelée lorsque
		// le contenu de la réponse a été reçu,
		// et analysé comme du JSON
		console.log("Etag OK")
		return data
	}).catch((err) => {
		// cette fonction est appelée en cas d'erreur
		console.log(err);
	});
}

function insertGene(url, req){
	fetch(url, req).then((response) => {
		// cette fonction est appelée lorsque
		// les en-têtes de la réponse ont été reçu
		if (!response.ok) {
			console.log(response);
		}
		return response.json() // attend la contenu
	}).then((data) => {
		// cette fonction est appelée lorsque
		// le contenu de la réponse a été reçu,
		// et analysé comme du JSON
		console.log(data)
		console.log("OK")
	}).catch((err) => {
		// cette fonction est appelée en cas d'erreur
		console.log(err);
	});

}

function editGene(form){
	let geneObj = formToObj(form);
	let main = 'http://127.0.0.1:5000/api/Genes/';
	let iD=geneObj["Ensembl_Gene_ID"]
	let url = main.concat(iD);
	let reqGet = {method: 'GET'};
	getEtag(url, reqGet).then(resp => {
		let reqPut = {	method: 'PUT', 
						headers: { "content-type": "application/json",
									"If-None-Match":resp,
									"If-Match":resp},
						body: JSON.stringify(geneObj)};
		insertGene(url, reqPut);
		});
}

function createGene(form){
	let geneObj = formToObj(form);
	console.log(JSON.stringify(geneObj))
	let main = 'http://127.0.0.1:5000/api/Genes/';
	let iD=geneObj["Ensembl_Gene_ID"]
	let url = main.concat(iD);
	let reqPut = {	method: 'PUT',
					headers: { 	"content-type": "application/json"},
					body: JSON.stringify(geneObj)};
	insertGene(url, reqPut);
}