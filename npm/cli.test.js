"use strict";

const test = require("node:test");
const assert = require("node:assert");

const { run, runners } = require("./bin/cli.js");
const { version } = require("./package.json");

const enoent = () => ({ error: Object.assign(new Error("nope"), { code: "ENOENT" }) });

test("uses uvx pinned to the package version", () => {
  const calls = [];
  const code = run(["--fix", "."], (cmd, args) => {
    calls.push([cmd, args]);
    return { status: 0 };
  });
  assert.strictEqual(code, 0);
  assert.deepStrictEqual(calls, [["uvx", [`keepmeachangelog==${version}`, "--fix", "."]]]);
});

test("passes through the exit code", () => {
  assert.strictEqual(run(["."], () => ({ status: 1 })), 1);
});

test("falls back to pipx when uvx is missing", () => {
  const calls = [];
  const code = run(["."], (cmd, args) => {
    calls.push(cmd);
    return cmd === "uvx" ? enoent() : { status: 0 };
  });
  assert.strictEqual(code, 0);
  assert.deepStrictEqual(calls, ["uvx", "pipx"]);
});

test("falls back to python only when the package imports", () => {
  const calls = [];
  const code = run(["."], (cmd, args) => {
    calls.push([cmd, args[0]]);
    if (cmd === "python3" && args[0] === "-c") return { status: 0 };
    if (cmd === "uvx" || cmd === "pipx") return enoent();
    return { status: 0 };
  });
  assert.strictEqual(code, 0);
  assert.deepStrictEqual(calls.at(-1), ["python3", "-m"]);
});

test("skips python when the package is not importable", () => {
  const code = run(["."], (cmd, args) => {
    if (args[0] === "-c") return { status: 1 };
    return enoent();
  });
  assert.strictEqual(code, 127);
});

test("reports when nothing is available", () => {
  assert.strictEqual(run(["."], enoent), 127);
});

test("reports unexpected spawn errors and signals as failure", () => {
  assert.strictEqual(run(["."], () => ({ error: new Error("boom") })), 1);
  assert.strictEqual(run(["."], () => ({ status: null })), 1);
});

test("runners cover uvx, pipx and python", () => {
  assert.deepStrictEqual(runners([]).map((r) => r.cmd), ["uvx", "pipx", "python3", "python"]);
});
