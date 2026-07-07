from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined_output(self) -> str:
        if self.stderr:
            return f"{self.stdout}\n{self.stderr}".strip()
        return self.stdout


def run_process(
    argv: Sequence[str],
    cwd: Path | None = None,
    timeout_s: float = 300.0,
    input_text: str | None = None,
    env: Mapping[str, str] | None = None,
) -> ProcessResult:
    process_env = os.environ.copy()
    if env is not None:
        process_env.update(env)

    completed = subprocess.run(
        [str(argument) for argument in argv],
        cwd=str(cwd) if cwd is not None else None,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_s,
        env=process_env,
        check=False,
    )

    return ProcessResult(
        argv=tuple(str(argument) for argument in argv),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
