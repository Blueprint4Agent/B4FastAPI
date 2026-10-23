import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const frontend = resolve(root, process.argv[2] ?? "src/frontend");
const result = spawnSync(
    "python3",
    [
        resolve(root, "scripts/verification_contract.py"),
        resolve(root, "contracts/openapi.json"),
        resolve(frontend, "contracts/openapi.json"),
    ],
    { stdio: "inherit" },
);
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
