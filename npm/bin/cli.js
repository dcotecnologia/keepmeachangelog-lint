#!/usr/bin/env node
"use strict";

// Thin wrapper: runs the Python `keepmeachangelog` package, pinned to this
// package's version, using the first runner available (uvx, pipx, python).

const { spawnSync } = require("node:child_process");

const { version } = require("../package.json");

function runners(argv) {
  const spec = `keepmeachangelog==${version}`;
  return [
    { cmd: "uvx", args: [spec, ...argv] },
    { cmd: "pipx", args: ["run", "--spec", spec, "keepmeachangelog", ...argv] },
    // Only when the package is already installed in that interpreter.
    ...["python3", "python"].map((cmd) => ({
      cmd,
      args: ["-m", "keepmeachangelog.cli", ...argv],
      probe: ["-c", "import keepmeachangelog"],
    })),
  ];
}

function available(spawn, runner) {
  if (!runner.probe) return true;
  const r = spawn(runner.cmd, runner.probe, { stdio: "ignore" });
  return !r.error && r.status === 0;
}

function run(argv, spawn = spawnSync) {
  for (const runner of runners(argv)) {
    if (!available(spawn, runner)) continue;
    const r = spawn(runner.cmd, runner.args, { stdio: "inherit" });
    if (r.error && r.error.code === "ENOENT") continue;
    if (r.error) {
      console.error(`keepmeachangelog: ${r.error.message}`);
      return 1;
    }
    return r.status === null ? 1 : r.status;
  }
  console.error(
    "keepmeachangelog: needs uv (https://docs.astral.sh/uv/), pipx or Python 3.11+ " +
      "with the `keepmeachangelog` package installed."
  );
  return 127;
}

module.exports = { run, runners };

if (require.main === module) {
  process.exitCode = run(process.argv.slice(2));
}
