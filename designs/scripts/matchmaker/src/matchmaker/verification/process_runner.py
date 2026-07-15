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


def _text_or_empty(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


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

    normalized_argv = tuple(str(argument) for argument in argv)
    try:
        completed = subprocess.run(
            list(normalized_argv),
            cwd=str(cwd) if cwd is not None else None,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            env=process_env,
            check=False,
        )
    except FileNotFoundError as error:
        return ProcessResult(
            argv=normalized_argv,
            returncode=127,
            stdout="",
            stderr=f"Executable not found: {normalized_argv[0]} ({error})",
        )
    except subprocess.TimeoutExpired as error:
        return ProcessResult(
            argv=normalized_argv,
            returncode=124,
            stdout=_text_or_empty(error.stdout),
            stderr=(
                _text_or_empty(error.stderr)
                + f"\nProcess timed out after {timeout_s} seconds"
            ).strip(),
        )

    return ProcessResult(
        argv=normalized_argv,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
