import { cp, mkdir, rm, stat } from "node:fs/promises";
import { resolve } from "node:path";

const sourceDist = resolve(process.cwd(), "dist");
const targetDist = resolve(process.cwd(), "..", "backend", "app", "static", "dist");

async function exists(path) {
    try {
        await stat(path);
        return true;
    } catch {
        return false;
    }
}

async function copyBuildToBackend() {
    if (!(await exists(sourceDist))) {
        throw new Error(`Frontend dist not found: ${sourceDist}`);
    }

    await rm(targetDist, { recursive: true, force: true });
    await mkdir(targetDist, { recursive: true });
    await cp(sourceDist, targetDist, { recursive: true, force: true });

    console.log(`[copy-to-backend] Copied ${sourceDist} -> ${targetDist}`);
}

copyBuildToBackend().catch((error) => {
    console.error("[copy-to-backend] Failed:", error.message);
    process.exit(1);
});
