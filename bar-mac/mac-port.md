# BAR launcher for macOS

This fork builds BAR's launcher for Apple Silicon Macs. It works like the Linux
and Windows launcher. The app holds only the launcher. On start it downloads
the macOS engine from github.com/leonseemann/RecoilEngine releases and the
game through the engine's pr-downloader. It updates itself from this fork's
releases.

## Branches

- `mac-support`: generic macOS support for spring-launcher, meant for
  upstream:
  - darwin platform, write path in `~/Library/Application Support/<title>`
  - starting engines from `Engine.app`
  - the engine's pr-downloader as a fallback, because no macOS pr-downloader is
    bundled
  - hiding the Dock icon while the game runs, the app menu, relaunch
  - `build.mac` settings
  - creating missing data folders before opening them
- `bar-mac` (default branch): `mac-support` plus BAR's macOS configuration:
  - `bar-mac/config.json`, generated from BYAR-Chobby's `dist_cfg/config.json`
    by `bar-mac/make-config.py`
  - `bar-mac/build.sh`
  - the footer showing the launcher and engine version
  - the workflows

A change for `mac-support` is merged there first and then cherry-picked to
`bar-mac`. Merges are rebase-only, so both branches stay linear.

## Releases and engine updates

- `.github/workflows/bar-mac.yml` builds every push and PR. A `v*` tag signs,
  notarizes and publishes the launcher (DMG, zip, `latest-mac.yml`).
- `.github/workflows/bar-mac-engine-sync.yml` runs hourly. When BAR moves Alpha
  or Engine Test to another engine version, it points `config.json` to a macOS
  engine release of that version (`make-config.py --sync`). A rebuilt engine
  of the same version, such as `bar-mac-v0.3.4`, is switched to by hand:
  `make-config.py <dist_cfg/config.json> <Alpha release tag> --test-engine <Engine Test release tag>`.
- Launchers read `config.json` from this branch on every start, so a config
  change needs no launcher release.

## AI assistance

Following spring-launcher's AI usage policy, this section states how AI was
used. The macOS port of the launcher was written with Claude Code (Anthropic):
- the darwin support on `mac-support`
- the BAR config generator and engine sync
- the build, signing and notarization workflow
- the 2026-10-16 cleanup and the missing-folder fix

The human contributor (Leon Seemann) set the goals, made the decisions,
reviewed the changes and tested the launcher on his Mac:
- install from the DMG
- self-update
- engine and game downloads
- starting games
