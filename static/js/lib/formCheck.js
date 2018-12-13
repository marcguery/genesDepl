
function colReset(att){
	att.style.backgroundColor = ""
}


function colError(att){
	att.style.backgroundColor = "MistyRose"
}

function colBadError(att){
	att.style.backgroundColor = "Crimson"
}

function colGood(att){
	att.style.backgroundColor = "LawnGreen"
}

function invalid(att, err){
	att.setCustomValidity(err);
}

function valid(att){
	att.setCustomValidity("");
}


function oblgAtt(att) {
	let state=true
	for (let i = 0; i < att.length; i++) {
		if (att[i].value==="") {
			colError(att[i]);
			invalid(att[i], "Valeur manquante");
			state=false
		}else{
			colReset(att[i]);
			valid(att[i]);
		}
	};
	return state
};

function diffLen(att, val) {
 	if (att.value.length > val) {
 		colBadError(att);
 		invalid(att, "Valeur trop longue");
		return false
	}else{
		colReset(att);
		valid(att);
		return true
	}
 }

function diffNum(start, end) {
	if (parseInt(start.value, 10)>=parseInt(end.value, 10)) {
		colBadError(start);
		invalid(start, "Valeur trop élevée");
		return false
	}else{
		colReset(start);
		valid(start);
		return true
	}
}


function checkVals(objs){
	let gid = objs[0];
	let assName = objs[1];
	let chr = objs[2];
	let band = objs[3];
	let strand = objs[4];
	let start = objs[5];
	let end = objs[6];
	let oblg = [gid, assName, chr, start, end];
	if (oblgAtt(oblg)===false) {
		return false
	};
	let lenVer=[[gid, 15], [end, 11]]
	for (let o of lenVer) {
		if (diffLen(o[0], o[1])===false){
			return false
		};
	};

	if (diffNum(start, end)===false) {
		return false
	}

	return true
};

function uniq(iD){
	let main = 'http://127.0.0.1:5000/api/Genes/';
	let url = main.concat(iD);
	let gid = document.getElementById('gid');
	gid.style.backgroundImage='url(https://i.stack.imgur.com/qq8AE.gif)'
	let req = {method: 'HEAD'};
	return fetch(url, req).then((response) => {
		// cette fonction est appelée lorsque
		// les en-têtes de la réponse ont été reçu
		if (!response.ok) {
			throw ("Error " + response.status);
		}
		return response // attend la contenu
	}).then((data) => {
		// cette fonction est appelée lorsque
		// le contenu de la réponse a été reçu,
		// et analysé comme du JSON
		invalid(gid, "Le gène existe déjà");
		colBadError(gid);
		return false
	}).catch((err) => {
		// cette fonction est appelée en cas d'erreur
		valid(gid);
		colGood(gid);
		return true
	}).finally(() => {
		gid.style.backgroundImage='none';
	});
}

function deactivateBtn(btId, state){
	let btn = document.getElementById(btId);
	btn.disabled=state;
};


function listenBoxes() {
	let textBoxes = document.getElementsByClassName('form-control');
	let state = checkVals(textBoxes);
	if (state) {
		console.log("CHECK");
		let gid = textBoxes[0];
		uniq(gid.value).then(resp => {
			if (resp) {
				deactivateBtn('btn', false);
			}else{
				deactivateBtn('btn', true);
			}
		})		
	}else {
		deactivateBtn('btn', true);
		console.log("NONENCOR")
	};
	return state
};

$(document).ready(function(){
	let e = document.getElementsByClassName('popdown');
	for (let pop of e){
		let f = pop.getElementsByClassName('popup')[0];
		pop.onmouseover = function() {
			f.style.display = 'block';
		}
		pop.onmouseout = function() {
			f.style.display = 'none';
		}
	}
});
