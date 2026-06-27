import { spawn } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const isWindows = process.platform === "win32";
const repoRoot = path.resolve(process.cwd(), "../..");
const bundledPython = "C:/Users/Ethan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const python = process.env.E2E_PYTHON ?? (isWindows && existsSync(bundledPython) ? bundledPython : "python");
const children = [];
let logs = "";
let apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
let webBase = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

function resetE2eState() {
  rmSync(path.join(repoRoot, ".tmp", "jobs"), { recursive: true, force: true });
}

async function probe(url) {
  try {
    const response = await fetch(url);
    return response.ok;
  } catch {
    return false;
  }
}

async function isExpectedApi(baseUrl) {
  try {
    const response = await fetch(`${baseUrl}/openapi.json`);
    if (!response.ok) return false;
    const payload = await response.json();
    return payload?.info?.title === "Hubei Gaokao Advisor";
  } catch {
    return false;
  }
}

function start(name, command, cwd, extraEnv = {}) {
  const child = spawn(command, {
    cwd,
    env: {
      ...process.env,
      NEXT_TELEMETRY_DISABLED: "1",
      NEXT_PUBLIC_API_BASE_URL: apiBase,
      PLAYWRIGHT_BASE_URL: webBase,
      ...extraEnv,
    },
    stdio: ["ignore", "pipe", "pipe"],
    shell: true,
  });
  children.push(child);
  child.stdout.on("data", (chunk) => {
    logs += `[${name}] ${chunk.toString()}`;
  });
  child.stderr.on("data", (chunk) => {
    logs += `[${name}] ${chunk.toString()}`;
  });
  child.on("exit", (code) => {
    logs += `[${name}] exited ${code}\n`;
  });
  return child;
}

async function waitFor(url, name) {
  const deadline = Date.now() + 45_000;
  while (Date.now() < deadline) {
    if (await probe(url)) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`${name} did not become ready. Logs:\n${logs}`);
}

async function firstFreePort(startPort) {
  for (let port = startPort; port < startPort + 20; port += 1) {
    if (!(await probe(`http://127.0.0.1:${port}/health`)) && !(await probe(`http://127.0.0.1:${port}/input`))) {
      return port;
    }
  }
  throw new Error(`No free local port found from ${startPort}`);
}

async function ensureApi() {
  if (await isExpectedApi(apiBase)) return;
  const preferredPort = Number(new URL(apiBase).port || "8000");
  const port = await firstFreePort(preferredPort === 8000 ? 8010 : preferredPort);
  apiBase = `http://127.0.0.1:${port}`;
  const quotedPython = isWindows ? `"${python}"` : python;
  start("api", `${quotedPython} -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port ${port}`, repoRoot);
  await waitFor(`${apiBase}/health`, "API");
  if (!(await isExpectedApi(apiBase))) {
    throw new Error(`API on ${apiBase} is not Hubei Gaokao Advisor. Logs:\n${logs}`);
  }
}

async function ensureWeb() {
  const requestedPort = Number(new URL(webBase).port || "3000");
  const port = (await probe(`${webBase}/input`)) ? await firstFreePort(requestedPort + 1) : requestedPort;
  webBase = `http://127.0.0.1:${port}`;
  start("web", `npx next dev -H 127.0.0.1 -p ${port}`, process.cwd());
  await waitFor(`${webBase}/input`, "Web");
}

function runPlaywright() {
  return new Promise((resolve) => {
    const child = spawn("npx playwright test --reporter=line", {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PLAYWRIGHT_EXTERNAL_SERVER: "1",
        PLAYWRIGHT_BASE_URL: webBase,
        NEXT_PUBLIC_API_BASE_URL: apiBase,
      },
      stdio: "inherit",
      shell: true,
    });
    child.on("exit", (code) => resolve(code ?? 1));
  });
}

function stopChildren() {
  return Promise.all(
    children.map(
      (child) =>
        new Promise((resolve) => {
          if (child.killed) return resolve();
          if (isWindows) {
            const killer = spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
            killer.on("exit", () => resolve());
          } else {
            child.kill("SIGTERM");
            child.on("exit", () => resolve());
            setTimeout(resolve, 2000);
          }
        }),
    ),
  );
}

let exitCode = 1;
try {
  resetE2eState();
  await ensureApi();
  await ensureWeb();
  exitCode = await runPlaywright();
} catch (error) {
  console.error(error);
} finally {
  await stopChildren();
}
process.exit(exitCode);