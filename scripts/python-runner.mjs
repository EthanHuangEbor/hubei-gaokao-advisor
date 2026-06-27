import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const bundledPython =
  "C:/Users/Ethan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";

const candidates = [
  process.env.PYTHON,
  existsSync(bundledPython) ? bundledPython : undefined,
  "python",
  "python3",
  "py",
].filter(Boolean);

function canRun(command) {
  const result = spawnSync(command, ["--version"], { encoding: "utf8", shell: false });
  return !result.error && result.status === 0;
}

const python = candidates.find(canRun);
if (!python) {
  console.error("No Python runtime found. Set PYTHON to a Python 3.11+ executable.");
  process.exit(1);
}

const result = spawnSync(python, process.argv.slice(2), { stdio: "inherit", shell: false });
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
