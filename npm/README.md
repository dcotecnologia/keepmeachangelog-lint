# keepmeachangelog (npm)

Linter for changelogs following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

This package is a thin wrapper around the Python tool
[`keepmeachangelog`](https://pypi.org/project/keepmeachangelog/). It runs the Python
package pinned to the same version, using the first of these available on your machine:
`uvx`, `pipx run`, or `python3 -m` (when the package is already installed).
You need [uv](https://docs.astral.sh/uv/), pipx or Python 3.11+.

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
