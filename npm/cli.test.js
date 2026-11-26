"use strict";

const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const { run, embeddedDir, interpreters } = require("./bin/cli.js");
const { sync } = require("./scripts/sync-python.js");
const { version } = require("./package.json");

const DIR = "/pkg/python";
const ok = { status: 0 };
const missing = { error: Object.assign(new Error("nope"), { code: "ENOENT" }) };

test("runs the bundled module with the package version and PYTHONPATH", () => {
  const calls = [];
  const code = run(
    ["--fix", "."],
    (cmd, args, opts) => {
      calls.push([cmd, args, opts]);
      return ok;
    },
    { PYTHONPATH: "/extra" },
    DIR
  );
  assert.strictEqual(code, 0);
  const [cmd, args, opts] = calls[1];
  assert.strictEqual(cmd, "python3");
  assert.deepStrictEqual(args, ["-m", "keepmeachangelog.cli", "--fix", "."]);
  assert.strictEqual(opts.env.PYTHONPATH, [DIR, "/extra"].join(path.delimiter));
  assert.strictEqual(opts.env.KEEPMEACHANGELOG_VERSION, version);
  assert.strictEqual(opts.env.PYTHONDONTWRITEBYTECODE, "1");
});

test("passes through the exit code", () => {
  const spawn = (cmd, args) => (args[0] === "-c" ? ok : { status: 1 });
  assert.strictEqual(run(["."], spawn, {}, DIR), 1);
});

test("falls back to python when python3 is missing or too old", () => {
  const tried = [];
  const spawn = (cmd, args) => {
    tried.push(cmd);
    if (cmd === "python3") return args[0] === "-c" ? missing : ok;
    return ok;
  };
  assert.strictEqual(run(["."], spawn, {}, DIR), 0);
  assert.deepStrictEqual(tried, ["python3", "python", "python"]);
});

test("reports when no Python 3.11+ exists", () => {
  assert.strictEqual(run(["."], () => ({ status: 1 }), {}, DIR), 127);
  assert.strictEqual(run(["."], () => missing, {}, DIR), 127);
});

test("KEEPMEACHANGELOG_PYTHON selects the interpreter", () => {
  assert.deepStrictEqual(interpreters({ KEEPMEACHANGELOG_PYTHON: "/opt/py" }), ["/opt/py"]);
  assert.deepStrictEqual(interpreters({}), ["python3", "python"]);
  const tried = [];
  run(["."], (cmd) => (tried.push(cmd), ok), { KEEPMEACHANGELOG_PYTHON: "/opt/py" }, DIR);
  assert.deepStrictEqual(tried, ["/opt/py", "/opt/py"]);
});

test("reports spawn errors and signals as failure", () => {
  const boom = (cmd, args) => (args[0] === "-c" ? ok : { error: new Error("boom") });
  assert.strictEqual(run(["."], boom, {}, DIR), 1);
  const signal = (cmd, args) => (args[0] === "-c" ? ok : { status: null });
  assert.strictEqual(run(["."], signal, {}, DIR), 1);
});

test("fails clearly when the bundled sources are missing", () => {
  assert.strictEqual(run(["."], () => ok, {}, null), 1);
});

test("embeddedDir prefers the shipped copy, then src/", () => {
  const seen = (hits) => (file) => hits.some((h) => file.includes(h));
  assert.match(embeddedDir(seen([path.join("npm", "python")])), /python$/);
  assert.match(embeddedDir(seen([path.join("src", "keepmeachangelog")])), /src$/);
  assert.strictEqual(embeddedDir(() => false), null);
});

test("sync copies only the Python sources", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "kml-"));
  const src = path.join(tmp, "src");
  fs.mkdirSync(path.join(src, "__pycache__"), { recursive: true });
  for (const f of ["cli.py", "linter.py", "notes.txt"]) fs.writeFileSync(path.join(src, f), "");
  const target = path.join(tmp, "out", "python", "keepmeachangelog");
  assert.deepStrictEqual(sync(src, target), ["cli.py", "linter.py"]);
  assert.deepStrictEqual(fs.readdirSync(target).sort(), ["cli.py", "linter.py"]);
  fs.rmSync(src, { recursive: true });
  fs.mkdirSync(src);
  assert.throws(() => sync(src, target), /no cli.py/);
  fs.rmSync(tmp, { recursive: true, force: true });
});

// End to end with the real interpreter, if there is a Python 3.11+.
const py = ["python3", "python"].find(
  (p) => spawnSync(p, ["-c", "import sys; sys.exit(sys.version_info < (3, 11))"]).status === 0
);

test("end to end: version, help and linting a changelog", { skip: !py }, () => {
  sync();
  const cli = path.join(__dirname, "bin", "cli.js");
  const exec = (...args) => spawnSync(process.execPath, [cli, ...args], { encoding: "utf8" });
  assert.strictEqual(exec("version").stdout.trim(), version);
  assert.match(exec("help").stdout, /usage: keepmeachangelog/);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "kml-"));
  const changelog = path.join(tmp, "CHANGELOG.md");
  fs.writeFileSync(changelog, "# Changelog\n\n## [Unreleased]\n\n[Unreleased]: https://x.io/o/r\n");
  assert.strictEqual(exec(tmp).status, 0); // a directory means its CHANGELOG.md
  fs.writeFileSync(changelog, "# Wrong\n");
  const bad = exec(tmp);
  assert.strictEqual(bad.status, 1);
  assert.match(bad.stdout, /title should be/);
  fs.rmSync(tmp, { recursive: true, force: true });
});
