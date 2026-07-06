/**
 * Dev launcher for the frontend.
 *
 * Fixes RAM/process accumulation on Windows where a force-closed `next dev`
 * leaves orphaned Turbopack/worker node processes behind. Those orphans pile
 * up across restarts and eat memory.
 *
 * What this does:
 *  1. Before starting, kills any stale node processes belonging to THIS
 *     project's Next dev server (scoped by this frontend directory path, so
 *     it never touches unrelated node processes like the editor or other apps).
 *  2. Starts `next dev` with a bounded heap (--max-old-space-size) so a
 *     compile spike can't balloon unchecked.
 *  3. On Ctrl+C / exit, kills the whole child process tree so nothing is left
 *     orphaned.
 *
 * Usage: `npm run dev` (optionally pass extra next flags, e.g. `-- --webpack`).
 */
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(__dirname, "..");
const isWin = process.platform === "win32";
const MAX_OLD_SPACE_MB = 2048;

function killStaleNextWorkers() {
  const dirLower = frontendDir.toLowerCase();
  let killed = 0;
  try {
    if (isWin) {
      const res = spawnSync(
        "powershell",
        [
          "-NoProfile",
          "-Command",
          "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | " +
            "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
        ],
        { encoding: "utf8" }
      );
      let list = [];
      try {
        const parsed = JSON.parse(res.stdout || "[]");
        list = Array.isArray(parsed) ? parsed : [parsed];
      } catch {
        list = [];
      }
      for (const p of list) {
        if (!p || !p.CommandLine || p.ProcessId === process.pid) continue;
        const cmd = String(p.CommandLine).toLowerCase();
        // Scope strictly to this project's Next dev server.
        if (cmd.includes(dirLower) && cmd.includes("next")) {
          spawnSync("taskkill", ["/PID", String(p.ProcessId), "/T", "/F"], {
            stdio: "ignore",
          });
          killed++;
        }
      }
    } else {
      const res = spawnSync("ps", ["-eo", "pid=,args="], { encoding: "utf8" });
      for (const line of (res.stdout || "").split("\n")) {
        if (line.includes(frontendDir) && line.includes("next")) {
          const pid = parseInt(line.trim().split(/\s+/)[0], 10);
          if (pid && pid !== process.pid) {
            try {
              process.kill(pid, "SIGKILL");
            } catch {}
          }
        }
      }
    }
  } catch {
    // best-effort cleanup; never block startup
  }
  if (killed) console.log(`[dev] cleaned up ${killed} stale Next worker(s)`);
}

killStaleNextWorkers();

const nextEntry = path.join(frontendDir, "node_modules", "next", "dist", "bin", "next");
const extraArgs = process.argv.slice(2);
const nodeOptions = `${process.env.NODE_OPTIONS ?? ""} --max-old-space-size=${MAX_OLD_SPACE_MB}`.trim();

const child = spawn(process.execPath, [nextEntry, "dev", ...extraArgs], {
  stdio: "inherit",
  cwd: frontendDir,
  env: { ...process.env, NODE_OPTIONS: nodeOptions },
});

function killChildTree() {
  if (!child.pid) return;
  if (isWin) {
    spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
  } else {
    try {
      process.kill(child.pid, "SIGTERM");
    } catch {}
  }
}

process.on("SIGINT", () => {
  killChildTree();
  process.exit(0);
});
process.on("SIGTERM", () => {
  killChildTree();
  process.exit(0);
});
child.on("exit", (code) => process.exit(code ?? 0));
