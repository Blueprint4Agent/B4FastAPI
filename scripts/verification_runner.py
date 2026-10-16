"""Bounded verification lanes with ordered frontend writers and complete logs."""

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
import subprocess
import tempfile
import time

from verification_cache import Receipt, git


def dependencies(commands):
    """Only isolated backend checks overlap the ordered frontend pipeline.

    Packaging waits for *all* earlier work: backend static-serving tests must
    finish before the packaged dist is replaced. Browser targets remain ordered
    because their reports and fixed ports can overlap, including branding copies.
    """
    last, result = {}, []
    for index, command in enumerate(commands):
        backend = (
            command[:1] == ["make"]
            and "-C" not in command
            and any(
                target in command for target in ("backend-test", "deployment-check")
            )
        )
        lane = "backend" if backend else "frontend"
        required = {last[lane]} if lane in last else set()
        if "frontend-package-verified" in command:
            required.update(range(index))
        result.append(required)
        last[lane] = index
    return result


def execute(root, commands, jobs=2, forced=False):
    if jobs < 1:
        raise ValueError("jobs must be positive")
    if not commands:
        return
    directory = (
        Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
        / "verification-logs"
    )
    directory.mkdir(exist_ok=True)
    logs = Path(tempfile.mkdtemp(prefix="run-", dir=directory))
    required = dependencies(commands)
    started = time.monotonic()

    def run(index):
        command = commands[index]
        receipt = Receipt(root, command)
        if not forced and receipt.reusable():
            print(
                "Reused matching local verification: " + " ".join(command), flush=True
            )
            return
        print("Receipt: " + receipt.miss_reason(), flush=True)
        receipt.invalidate()
        print("Running: " + " ".join(command), flush=True)
        log = logs / f"{index}.log"
        before = time.monotonic()
        with log.open("w") as output:
            completed = subprocess.run(
                command, cwd=root, stdout=output, stderr=subprocess.STDOUT
            )
        if completed.returncode:
            print(
                "\n".join(log.read_text(errors="replace").splitlines()[-80:]),
                flush=True,
            )
            print(f"Failed. Full log: {log}", flush=True)
            raise subprocess.CalledProcessError(completed.returncode, command)
        if not forced:
            receipt.save()
        print(f"Passed ({time.monotonic() - before:.1f}s). Log: {log}", flush=True)

    pending, done, running, failures = set(range(len(commands))), set(), {}, []
    # Drain running work on failure; never start downstream work after failure.
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        while pending or running:
            for index in sorted(pending):
                if len(running) >= jobs or failures:
                    break
                if required[index] <= done:
                    running[pool.submit(run, index)] = index
                    pending.remove(index)
            if not running:
                break
            completed, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in completed:
                index = running.pop(future)
                try:
                    future.result()
                    done.add(index)
                except Exception as error:
                    failures.append(error)
        if failures:
            raise failures[0]
    if pending:
        raise ValueError("Unresolved verification dependencies")
    print(
        f"Verification completed in {time.monotonic() - started:.1f}s; {len(commands)} commands, jobs={jobs}. Logs: {logs}",
        flush=True,
    )
