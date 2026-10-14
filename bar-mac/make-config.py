#!/usr/bin/env python3
"""Writes the launcher config of BAR for macOS (bar-mac/config.json).

Defaults, links, server and spring settings come from BYAR-Chobby's
dist_cfg/config.json. Its setups are replaced by one for macOS that downloads
the engine from the given release of the macOS engine builds.

Usage: make-config.py <BYAR-Chobby dist_cfg/config.json> <engine release tag> [engine version]
"""
import json
import os
import sys

ENGINE_REPO = "leonseemann/RecoilEngine"
CONFIG_URL = "https://raw.githubusercontent.com/leonseemann/spring-launcher/bar-mac/bar-mac/config.json"

src, tag = sys.argv[1], sys.argv[2]
with open(src) as f:
	config = json.load(f)

base = next(s for s in config["setups"] if s["package"]["id"] == "manual-linux")
version = sys.argv[3] if len(sys.argv) > 3 else base["launch"]["engine"].removeprefix("recoil_")

# the release tag is part of the name, so fixed builds of the same engine
# version are downloaded again
engine = f"recoil_{version}_{tag}"
resources = [r for r in base["downloads"].get("resources", []) if not r["destination"].startswith("engine/")]
resources.append({
	"url": f"https://github.com/{ENGINE_REPO}/releases/download/{tag}/recoil_{version}_arm64-macos.7z",
	"destination": f"engine/{engine}",
	"extract": True,
})

config["setups"] = [{
	"package": {
		"id": "manual-mac",
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
}]

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), "w") as f:
	json.dump(config, f, indent=4)
	f.write("\n")
