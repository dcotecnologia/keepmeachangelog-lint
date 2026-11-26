#!/usr/bin/env node
"use strict";

// Runs the Python linter that ships inside this package (npm/python, copied from
// src/keepmeachangelog at pack time) with the system Python 3.11+.
// $KEEPMEACHANGELOG_PYTHON picks a specific interpreter.

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const { version } = require("../package.json");

const MIN_PYTHON = "3.11";
const CHECK = ["-c", "import sys; sys.exit(sys.version_info < (3, 11))"];

// Shipped copy first; the repo's src/ when running from a checkout.
function embeddedDir(exists = fs.existsSync) {
  const candidates = [
    path.resolve(__dirname, "..", "python"),
    path.resolve(__dirname, "..", "..", "src"),
  ];
  return candidates.find((dir) => exists(path.join(dir, "keepmeachangelog", "cli.py"))) || null;
}

function interpreters(env = process.env) {
  return env.KEEPMEACHANGELOG_PYTHON ? [env.KEEPMEACHANGELOG_PYTHON] : ["python3", "python"];
}

function run(argv, spawn = spawnSync, env = process.env, dir = embeddedDir()) {
  if (!dir) {
    console.error("keepmeachangelog: the bundled Python sources are missing; reinstall the package.");
    return 1;
  }
  for (const python of interpreters(env)) {
    const probe = spawn(python, CHECK, { stdio: "ignore" });
    if (probe.error || probe.status !== 0) continue;
    const r = spawn(python, ["-m", "keepmeachangelog.cli", ...argv], {
      stdio: "inherit",
      env: {
        ...env,
        PYTHONPATH: [dir, env.PYTHONPATH].filter(Boolean).join(path.delimiter),
        PYTHONDONTWRITEBYTECODE: "1",
        KEEPMEACHANGELOG_VERSION: version,
      },
    });
    if (r.error) {
      console.error(`keepmeachangelog: ${r.error.message}`);
      return 1;
    }
    return r.status === null ? 1 : r.status;
  }
  console.error(
    `keepmeachangelog: needs Python ${MIN_PYTHON}+ on PATH (python3 or python), ` +
      "or set KEEPMEACHANGELOG_PYTHON."
  );
  return 127;
}

module.exports = { run, embeddedDir, interpreters };

if (require.main === module) {
  process.exitCode = run(process.argv.slice(2));
}
