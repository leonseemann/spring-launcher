'use strict';

const fs = require('fs');
const path = require('path');
const { fileURLToPath } = require('url');
const shell = require('electron').shell;
const { writePath } = require('./spring_platform');

// The lobby opens data folders such as demos/ before the engine has written
// anything there, and opening a folder that does not exist fails.
function createMissingDataFolder(url) {
	let dir;
	try {
		dir = fileURLToPath(url);
	} catch (e) {
		return;
	}

	const rel = path.relative(writePath, dir);
	if (rel.startsWith('..') || path.isAbsolute(rel) || fs.existsSync(dir)) {
		return;
	}
	fs.mkdirSync(dir, { recursive: true });
}

module.exports.open = async (target) => {
	if (target.match(/^https?:\/\/.*$/) ||
		target.match(/^file:\/\/\/.*$/)) {
		if (target.startsWith('file:')) {
			createMissingDataFolder(target);
		}
		await shell.openExternal(target);
	} else {
		await shell.openPath(target);
	}
};
