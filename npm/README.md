# keepmeachangelog (npm)

Linter for changelogs following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

The Python linter ([`keepmeachangelog`](https://pypi.org/project/keepmeachangelog/)) ships
**inside this package**, so the version you install is the version that runs. Nothing is
downloaded and it works offline. It only needs **Python 3.11 or newer** on your `PATH`
(`python3` or `python`); set `KEEPMEACHANGELOG_PYTHON` to use a specific interpreter.

```sh
npx keepmeachangelog .        # also: bunx keepmeachangelog . / yarn dlx keepmeachangelog .
```

In a Node project:

```sh
npm i -D keepmeachangelog
```

```json
{ "scripts": { "changelog:lint": "keepmeachangelog --version-from package.json ." } }
```

See the [main README](https://github.com/dcotecnologia/keepmeachangelog-lint#readme) for rules and options.
