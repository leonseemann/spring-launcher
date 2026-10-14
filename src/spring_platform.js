'use strict';

const log = require('electron-log');
const path = require('path');
const fs = require('fs');
const { existsSync, mkdirSync } = fs;
const assert = require('assert');

const platformName = process.platform;

const { config } = require('./launcher_config');
const { resolveWritePath } = require('./write_path');

var FILES_DIR = 'files';
FILES_DIR = path.resolve(`${__dirname}/../files`);
if (!existsSync(FILES_DIR)) {
	FILES_DIR = path.resolve(`${process.resourcesPath}/../files`);
}

// The following order is necessary:
// 1. Set write dir
// 2. Set logfile based on the writedir
// 3. Start logging

assert(config.title != undefined);
const writePath = resolveWritePath(config.title);

assert(writePath != undefined);
if (!existsSync(writePath)) {
	try {
		mkdirSync(writePath, { recursive: true });
	} catch (err) {
		log.error(`Cannot create writePath at: ${writePath}`);
		log.error(err);
	}
}

// This is a workaround for bug in electron-updater that changed
// installation path on windows on update. The bug was fixed, but
// we put this workaround here to fix installations that were
// already affected by the bug.
// TODO: Delete this code after some a while.
try {
	if (process.platform == 'win32' &&
		fs.existsSync(path.join(writePath, '../../data/springsettings.cfg')) &&
		!fs.existsSync(path.join(writePath, 'springsettings.cfg'))) {
		fs.rmdirSync(writePath);
		fs.renameSync(path.join(writePath, '../../data'), writePath);
	}
} catch (err) {
	log.error('Failed to move old installation to new location, ignoring. Error: ', err);
}

if (existsSync(FILES_DIR) && existsSync(writePath)) {
	fs.readdirSync(FILES_DIR).forEach(function (file) {
		const srcPath = path.join(FILES_DIR, file);
		const dstPath = path.join(writePath, file);
		// NB: we copy files each time, which is possibly slow
		// if (!existsSync(dstPath)) {
		try {
			fs.copyFileSync(srcPath, dstPath);
		} catch (err) {
			log.error(`Failed to copy file from ${srcPath} tp ${dstPath}`);
			log.error(err);
		}
		//}
	});
}

let prDownloaderBin;
// pr-downloader within a downloaded engine
let enginePrDownloaderBin;
if (platformName === 'win32') {
	prDownloaderBin = 'pr-downloader.exe';
	enginePrDownloaderBin = prDownloaderBin;
	exports.springBin = 'spring.exe';
} else if (platformName === 'linux') {
	prDownloaderBin = 'pr-downloader';
	enginePrDownloaderBin = prDownloaderBin;
	exports.springBin = 'spring';
} else if (platformName === 'darwin') {
	prDownloaderBin = 'pr-downloader';
	// the engine runs as the main executable of an app bundle, which gives
	// the game its own name and icon in the Dock
	exports.springBin = 'Engine.app/Contents/MacOS/spring';
	enginePrDownloaderBin = 'Engine.app/Contents/Resources/pr-downloader';
} else {
	log.error(`Unsupported platform: ${platformName}`);
	process.exit(-1);
}

exports.prDownloaderPath = path.resolve(`${__dirname}/../bin/${prDownloaderBin}`);
if (!existsSync(exports.prDownloaderPath)) {
	exports.prDownloaderPath = path.resolve(`${process.resourcesPath}/../bin/${prDownloaderBin}`);
}

// Without a pr-downloader of its own the launcher uses the one that comes with
// the engine, available once the engine has been downloaded.
exports.getPrDownloaderPath = function () {
	if (existsSync(exports.prDownloaderPath)) {
		return exports.prDownloaderPath;
	}
	const engineName = config.launch.engine || config.downloads.engines[0];
	if (engineName != null) {
		const enginePrDownloader = path.join(writePath, 'engine', engineName, enginePrDownloaderBin);
		if (existsSync(enginePrDownloader)) {
			return enginePrDownloader;
		}
	}
	return exports.prDownloaderPath;
};

exports.writePath = writePath;
