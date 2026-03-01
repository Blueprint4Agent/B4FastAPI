import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const frontendRoot = resolve(__dirname, "..");
const openapiTsPath = resolve(frontendRoot, "src", "api", "generated", "openapi.ts");

function runGenerateApi() {
  return new Promise((resolvePromise, rejectPromise) => {
    const npmExecPath = process.env.npm_execpath;
    const command = npmExecPath ? process.execPath : "npm";
    const args = npmExecPath ? [npmExecPath, "run", "generate:api"] : ["run", "generate:api"];

    const child = spawn(command, args, {
      cwd: frontendRoot,
      stdio: "inherit",
      shell: !npmExecPath
    });

    child.on("error", rejectPromise);
    child.on("exit", (code) => {
      if (code === 0) {
        resolvePromise();
        return;
      }
      rejectPromise(new Error(`generate:api failed with exit code ${code ?? "unknown"}`));
    });
  });
}

async function main() {
  try {
    await runGenerateApi();
  } catch (error) {
    if (existsSync(openapiTsPath)) {
      console.warn("[generate:api:optional] Failed to refresh openapi.ts. Using existing file.");
      console.warn(`[generate:api:optional] ${error instanceof Error ? error.message : String(error)}`);
      return;
    }
    throw error;
  }
}

main().catch((error) => {
  console.error("[generate:api:optional] openapi.ts generation failed.");
  console.error(error);
  process.exit(1);
});
