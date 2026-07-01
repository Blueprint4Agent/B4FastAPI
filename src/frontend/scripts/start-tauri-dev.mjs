import { spawn } from "node:child_process";

const devUrl = "http://localhost:5173";

async function inspectExistingServer() {
    try {
        const response = await fetch(devUrl, { signal: AbortSignal.timeout(1_500) });
        const body = await response.text();
        if (!response.ok || !body.includes('id="root"')) {
            throw new Error(`Port 5173 is occupied by a different server (${response.status}).`);
        }
        return true;
    } catch (error) {
        if (error instanceof Error && error.message.includes("occupied by a different server")) {
            throw error;
        }
        return false;
    }
}

if (await inspectExistingServer()) {
    console.log(`[tauri-dev] Reusing the browser dev server at ${devUrl}.`);
    process.exit(0);
}

const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const child = spawn(npmCommand, ["run", "dev"], {
    stdio: "inherit",
});

for (const signal of ["SIGINT", "SIGTERM"]) {
    process.on(signal, () => child.kill(signal));
}

child.on("exit", (code) => {
    process.exit(code ?? 1);
});
