

function oblgAtt(att) {
	var state=true
	for (let i = 0; i < att.length; i++) {
		console.log(att[i].value);
		if (att[i].value==="") {
			att[i].style.backgroundColor = "orange";
			state=false
		}else{
			att[i].style.backgroundColor = "";
		}
	};
	return state
};

function diffLen(att, val) {
 	if (att.value.length > val) {
 		att.style.backgroundColor = "yellow";
		return false
	};
 }

function diffNum(start, end) {
	if (parseInt(start.value, 10)>=parseInt(end.value, 10)) {
		start.style.backgroundColor = "yellow";
		return false
	}else{
		start.style.backgroundColor = "";
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
	let oblg = [gid, assName, start, end];
	if (oblgAtt(oblg)===false) {
		return false
	};
	let lenVer=[[gid, 15],[end, 11]]
	for (var o of lenVer) {
		if (diffLen(o[0], o[1])===false){
			return false
		};
	};

	if (diffNum(start, end)===false) {
		return false
	}  


	for (let i = 0; i < 5 ; i++) {
		console.log(objs[i].value)
	};

	return true
};


function listenBoxes() {
	let textBoxes = document.querySelectorAll('*[id]');
	let state = checkVals(textBoxes);
	if (state) {
		console.log("CHECK")
	}else {
		console.log("NONENCOR")
	};
};



