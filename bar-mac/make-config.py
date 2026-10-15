#!/usr/bin/env python3
"""Writes the launcher config of BAR for macOS (bar-mac/config.json).

Defaults, links, server and spring settings come from BYAR-Chobby's
dist_cfg/config.json. Its setups are replaced by one for macOS that downloads
the engine from the given release of the macOS engine builds. With
--test-engine, a second setup like BAR's "Engine Test" one uses the engine
version of manual-linux-test-engine from that release.

Usage: make-config.py <BYAR-Chobby dist_cfg/config.json> <engine release tag> [engine version]
                      [--test-engine <engine release tag>]
"""
import json
import os
import sys

ENGINE_REPO = "leonseemann/RecoilEngine"
CONFIG_URL = "https://raw.githubusercontent.com/leonseemann/spring-launcher/bar-mac/bar-mac/config.json"

args = sys.argv[1:]
test_tag = None
if "--test-engine" in args:
	i = args.index("--test-engine")
	test_tag = args[i + 1]
	del args[i:i + 2]

src, tag = args[0], args[1]
with open(src) as f:
	config = json.load(f)


def mac_setup(base, package_id, tag, version):
	# the release tag is part of the name, so fixed builds of the same engine
	# version are downloaded again
	engine = f"recoil_{version}_{tag}"
	resources = [r for r in base["downloads"].get("resources", []) if not r["destination"].startswith("engine/")]
	resources.append({
		"url": f"https://github.com/{ENGINE_REPO}/releases/download/{tag}/recoil_{version}_arm64-macos.7z",
		"destination": f"engine/{engine}",
		"extract": True,
	})
	return {
		"package": {
			"id": package_id,
			"display": base["package"]["display"],
			"platform": "darwin",
		},
		"config_url": CONFIG_URL,
		"env_variables": base["env_variables"],
		"auto_download": True,
		"downloads": {
			"games": base["downloads"]["games"],
			"resources": resources,
		},
		"no_start_script": base["no_start_script"],
		"logs_s3_bucket": base.get("logs_s3_bucket"),
		"launch": {
			"start_args": base["launch"]["start_args"],
			"engine": engine,
			"springsettings": base["launch"].get("springsettings", {}),
		},
	}


def setup(package_id):
	return next(s for s in config["setups"] if s["package"]["id"] == package_id)


def engine_version(base):
	return base["launch"]["engine"].removeprefix("recoil_")


base = setup("manual-linux")
version = args[2] if len(args) > 2 else engine_version(base)
setups = [mac_setup(base, "manual-mac", tag, version)]
if test_tag:
	test_base = setup("manual-linux-test-engine")
	setups.append(mac_setup(test_base, "manual-mac-test-engine", test_tag, engine_version(test_base)))
config["setups"] = setups

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), "w") as f:
	json.dump(config, f, indent=4)
	f.write("\n")
