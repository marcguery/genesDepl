

function oblgAtt(att) {
	for (var i = 0; i < att.length; i++) {
		console.log(att[i]);
	};
};


function checkVals(objs){
	let gid = objs[0];
	let assName = objs[1];
	let chr = objs[2];
	let band = objs[3];
	let strand = objs[4];
	let start = objs[5];
	let end = objs[6];
	var oblg = [gid, assName, start, end];
	oblgAtt(oblg);
	if (gid.length > 15) {
		return false
	};

	for (let i = 0; i < 5 ; i++) {
		console.log(objs[i].value)
	};
};


function listenBoxes() {
	var textBoxes = document.querySelectorAll('*[id]');
	var state = checkVals(textBoxes);
	if (state) {
		console.log("CHECK")
	}else {
		console.log("NONECOR")
	};
};



