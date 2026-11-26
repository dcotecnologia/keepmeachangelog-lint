#!/usr/bin/env node
"use strict";

// Copies the Python sources into npm/python so they ship inside the npm package.
// Runs on `prepack` (npm pack / npm publish) and can be run by hand.

const fs = require("node:fs");
const path = require("node:path");

const SOURCE = path.resolve(__dirname, "..", "..", "src", "keepmeachangelog");
const TARGET = path.resolve(__dirname, "..", "python", "keepmeachangelog");

function sync(source = SOURCE, target = TARGET) {
  fs.rmSync(path.dirname(target), { recursive: true, force: true });
  fs.mkdirSync(target, { recursive: true });
  const copied = [];
  for (const name of fs.readdirSync(source)) {
    if (!name.endsWith(".py")) continue;
    fs.copyFileSync(path.join(source, name), path.join(target, name));
    copied.push(name);
  }
  if (!copied.includes("cli.py")) {
    throw new Error(`no cli.py found in ${source}`);
  }
  return copied.sort();
}

module.exports = { sync };

if (require.main === module) {
  console.log(`copied: ${sync().join(", ")}`);
}
