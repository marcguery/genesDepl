
function colReset(att){
	att.style.backgroundColor = ""
}


function colError(att){
	att.style.backgroundColor = "MistyRose"
}

function colBadError(att){
	att.style.backgroundColor = "LightCoral"
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
	let assName = objs[1];
	let chr = objs[2];
	let band = objs[3];
	let strand = objs[4];
	let start = objs[5];
	let end = objs[6];
	let oblg = [assName, chr, start, end];
	if (oblgAtt(oblg)===false) {
		return false
	};
	let lenVer=[[end, 11]]
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
	let src = document.getElementById("gid");
	src.style.background = 'url(https://i.stack.imgur.com/qq8AE.gif) right no-repeat';
	let main = 'http://127.0.0.1:5000/api/Genes/';
	let url = main.concat(iD);
	let gid = document.getElementById('gid');
	let req = {method: 'HEAD'};
	fetch(url, req).then((response) => {
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
	}).catch((err) => {
		// cette fonction est appelée en cas d'erreur
		valid(gid);
		colGood(gid);
	}).finally(() => {
		src.style.backgroundImage = '';
	});
}


function listenBoxes() {
	let btn = document.getElementById('btn');
	let textBoxes = document.getElementsByClassName('form-control');
	let state = checkVals(textBoxes);
	btn.disabled=!state;
	if (state) {
		console.log("CHECK")
		
	}else {
		console.log("NONENCOR")
	};
	return state
};


function checkId(att, iD) {
	if (oblgAtt([att])===false) {
		return false
	};
	if (diffLen(att, 15)===false){
			return false
		};
	uniq(iD);
	return true
};

function deactivateBtn(btId){
	let btn = document.getElementById(btId);
	btn.setCustomValidity("Modifiez le formulaire pour activer le bouton")
	btn.disabled=true;
}

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
