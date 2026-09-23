import { readFile } from "node:fs/promises";
import { isDeepStrictEqual } from "node:util";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const frontend = resolve(root, process.argv[2] ?? "src/frontend");
const provider = JSON.parse(await readFile(resolve(root, "contracts/openapi.json"), "utf8"));
const consumer = JSON.parse(await readFile(resolve(frontend, "contracts/openapi.json"), "utf8"));
if (!isDeepStrictEqual(provider, consumer)) {
    console.error(
        "B4React contract differs from the backend baseline. Merge the coordinated B4React contract change, then update the submodule pin. Do not overwrite child files during builds.",
    );
    process.exitCode = 1;
} else {
    console.log("Backend and pinned B4React OpenAPI contracts match.");
}
