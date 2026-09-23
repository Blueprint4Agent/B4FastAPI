import { cp, mkdir, realpath, rm, stat } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const source = await realpath(resolve(root, process.argv[2] ?? "src/frontend/dist"));
const destination = resolve(root, process.argv[3] ?? "src/backend/app/static/dist");
// Check source and destination before replacing the previously packaged build.
await stat(resolve(source, "index.html"));
await mkdir(dirname(destination), { recursive: true });
const parent = await realpath(dirname(destination));
const target = resolve(parent, "dist");
if (destination !== target)
    throw new Error("Destination must be a real parent directory ending in /dist");
const inside = (a, b) => {
    const path = relative(a, b);
    return path === "" || (!isAbsolute(path) && path !== ".." && !path.startsWith(`..${sep}`));
};
if (inside(source, target) || inside(target, source))
    throw new Error("Source and destination must not overlap");
await rm(target, { recursive: true, force: true });
await cp(source, target, { recursive: true });
console.log(`Packaged frontend into ${target}`);
