import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { delimiter, join } from "node:path";

const tauriScriptPath = join(process.cwd(), "node_modules", "@tauri-apps", "cli", "tauri.js");
const executable = process.platform === "win32" ? process.execPath : "tauri";
const tauriPath =
    process.platform === "win32"
        ? tauriScriptPath
        : join(process.cwd(), "node_modules", ".bin", executable);

if (!existsSync(tauriPath)) {
    console.error("[tauri] CLI not found. Run `npm ci` in src/frontend first.");
    process.exit(1);
}

const env = { ...process.env };
const cargoBin = join(homedir(), ".cargo", "bin");
const pathKey = Object.keys(env).find((key) => key.toLowerCase() === "path") ?? "PATH";
const pathEntries = (env[pathKey] ?? "").split(delimiter).filter(Boolean);

if (existsSync(cargoBin) && !pathEntries.includes(cargoBin)) {
    env[pathKey] = [cargoBin, ...pathEntries].join(delimiter);
    console.log(`[tauri] Added ${cargoBin} to PATH for this command.`);
}

const command = process.platform === "win32" ? executable : tauriPath;
const args =
    process.platform === "win32" ? [tauriPath, ...process.argv.slice(2)] : process.argv.slice(2);

const child = spawn(command, args, {
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
