#!/usr/bin/env python3
"""Writes the launcher config of BAR for macOS (bar-mac/config.json).

Defaults, links, server and spring settings come from BYAR-Chobby's
dist_cfg/config.json. Its setups are replaced by one for macOS that downloads
the engine from the given release of the macOS engine builds. With
--test-engine, a second setup like BAR's "Engine Test" one uses the engine
version of manual-linux-test-engine from that release.

With --sync, the releases are picked from the current bar-mac/config.json and
the engine releases: a setup keeps its release while BAR's engine version is
unchanged, otherwise it takes a release of the new version that another setup
already uses, or the newest one with an archive for it. Without a macOS
release for BAR's new version a setup stays as it is (the test setup is left
out if there is none yet); exits with 1 if that is the main setup.

Usage: make-config.py <BYAR-Chobby dist_cfg/config.json> <engine release tag> [engine version]
                      [--test-engine <engine release tag>]
       make-config.py <BYAR-Chobby dist_cfg/config.json> --sync
"""
import json
import os
import re
import sys
import urllib.request

ENGINE_REPO = "leonseemann/RecoilEngine"
CONFIG_URL = "https://raw.githubusercontent.com/leonseemann/spring-launcher/bar-mac/bar-mac/config.json"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


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


def find_setup(config, package_id):
	return next((s for s in config["setups"] if s["package"]["id"] == package_id), None)


def engine_version(setup):
	return setup["launch"]["engine"].removeprefix("recoil_")


def current_engines():
	"""{package id: (version, tag)} of the current bar-mac/config.json"""
	with open(CONFIG_PATH) as f:
		current = json.load(f)
	engines = {}
	for s in current["setups"]:
		m = re.fullmatch(r"recoil_(.+)_(bar-mac-v.+)", s["launch"]["engine"])
		if m:
			engines[s["package"]["id"]] = (m.group(1), m.group(2))
	return engines


def release_tags(version):
	"""tags of the engine releases with an archive of that version, newest first"""
	request = urllib.request.Request(f"https://api.github.com/repos/{ENGINE_REPO}/releases?per_page=100")
	token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
	if token:
		request.add_header("Authorization", f"Bearer {token}")
	with urllib.request.urlopen(request) as response:
		releases = json.load(response)
	asset = f"recoil_{version}_arm64-macos.7z"
	releases = [r for r in releases if not r["draft"] and any(a["name"] == asset for a in r["assets"])]
	releases.sort(key=lambda r: r["published_at"], reverse=True)
	return [r["tag_name"] for r in releases]


def sync(config):
	"""picks (tag, version) for the main and the test setup (None: no test setup)"""
	current = current_engines()
	missing = False

	def pick(package_id, version, required):
		nonlocal missing
		mine = current.get(package_id)
		if mine and mine[0] == version:
			return mine[1], version
		tags = [tag for v, tag in current.values() if v == version] or release_tags(version)
		if tags:
			return tags[0], version
		print(f"no macOS engine release for {version} ({package_id})", file=sys.stderr)
		missing = missing or required
		return (mine[1], mine[0]) if mine else None

	main_version = engine_version(find_setup(config, "manual-linux"))
	main = pick("manual-mac", main_version, True)
	if main is None:
		sys.exit(f"no macOS engine release for {main_version} and no current one to keep")

	test = None
	test_base = find_setup(config, "manual-linux-test-engine")
	if test_base and engine_version(test_base) != main[1]:
		test = pick("manual-mac-test-engine", engine_version(test_base), False)
	return main, test, missing


def main():
	args = sys.argv[1:]
	test_tag = None
	if "--test-engine" in args:
		i = args.index("--test-engine")
		test_tag = args[i + 1]
		del args[i:i + 2]

	with open(args[0]) as f:
		config = json.load(f)
	base = find_setup(config, "manual-linux")
	test_base = find_setup(config, "manual-linux-test-engine")

	missing = False
	if args[1] == "--sync":
		(tag, version), test, missing = sync(config)
	else:
		tag = args[1]
		version = args[2] if len(args) > 2 else engine_version(base)
		test = (test_tag, engine_version(test_base)) if test_tag else None

	setups = [mac_setup(base, "manual-mac", tag, version)]
	if test:
		setups.append(mac_setup(test_base, "manual-mac-test-engine", *test))
	config["setups"] = setups

	with open(CONFIG_PATH, "w") as f:
		json.dump(config, f, indent=4)
		f.write("\n")
	print("\n".join(s["package"]["display"] + ": " + s["launch"]["engine"] for s in setups))
	sys.exit(1 if missing else 0)


main()
