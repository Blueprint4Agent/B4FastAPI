import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { delimiter, join } from "node:path";

const executable = process.platform === "win32" ? "tauri.cmd" : "tauri";
const tauriPath = join(process.cwd(), "node_modules", ".bin", executable);

if (!existsSync(tauriPath)) {
    console.error("[tauri] CLI not found. Run `npm ci` in src/frontend first.");
    process.exit(1);
}

const env = { ...process.env };
const cargoBin = join(homedir(), ".cargo", "bin");
const pathEntries = (env.PATH ?? "").split(delimiter).filter(Boolean);

if (existsSync(cargoBin) && !pathEntries.includes(cargoBin)) {
    env.PATH = [cargoBin, ...pathEntries].join(delimiter);
    console.log(`[tauri] Added ${cargoBin} to PATH for this command.`);
}

const child = spawn(tauriPath, process.argv.slice(2), {
    env,
    stdio: "inherit",
});

for (const signal of ["SIGINT", "SIGTERM"]) {
    process.on(signal, () => child.kill(signal));
}

child.on("error", (error) => {
    console.error(`[tauri] Failed to start: ${error.message}`);
    process.exit(1);
});

child.on("exit", (code, signal) => {
    if (signal) {
        process.kill(process.pid, signal);
        return;
    }
    process.exit(code ?? 1);
});
