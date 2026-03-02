import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GamResult:
    exit_code: int
    stdout: str
    stderr: str


def run_gam(argv: List[str], timeout_seconds: int = 30, max_output_bytes: int = 200_000) -> GamResult:
    if not argv or argv[0].strip() == '':
        raise ValueError('argv must be a non-empty list')

    # Never use shell=True
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        shell=False,
    )

    stdout = proc.stdout or ''
    stderr = proc.stderr or ''

    # Clamp output to avoid huge payloads
    if len(stdout.encode('utf-8', errors='ignore')) > max_output_bytes:
        stdout = stdout.encode('utf-8', errors='ignore')[:max_output_bytes].decode('utf-8', errors='ignore')
    if len(stderr.encode('utf-8', errors='ignore')) > max_output_bytes:
        stderr = stderr.encode('utf-8', errors='ignore')[:max_output_bytes].decode('utf-8', errors='ignore')

    return GamResult(exit_code=int(proc.returncode), stdout=stdout, stderr=stderr)
