import logging
import re
import time
from pathlib import Path

from .ibmi_client import IBMiClient
from .utils import sha256_file, sniff_csv, timed, xlsx_to_csv

_SAFE_NAME = re.compile(r"^[A-Za-z0-9_./]+$")


def _ensure_safe(value: str, field: str) -> str:
    if not _SAFE_NAME.match(value):
        raise ValueError(f"Invalid characters in {field}")
    return value


def _prepare_csv(src: Path, log: logging.Logger) -> Path:
    if src.suffix.lower() == ".xlsx":
        csv_path = src.with_suffix(".csv")
        xlsx_to_csv(src, csv_path)
    else:
        csv_path = src
    sniff_csv(csv_path)
    digest = sha256_file(csv_path)
    log.info("Local SHA256=%s", digest)
    return csv_path


def _remote_dirs(ifs_dir: str) -> list[str]:
    return [
        ifs_dir,
        f"{ifs_dir}/in",
        f"{ifs_dir}/out",
        f"{ifs_dir}/run",
        f"{ifs_dir}/scripts",
    ]


def _sync_scripts(client: IBMiClient, ifs_dir: str) -> None:
    for script in ("setup.sql", "apply.sql", "process.clp", "teardown.sql"):
        local_script = Path("ibmi") / script
        remote_script = f"{ifs_dir}/scripts/{script}"
        client.sftp_put(local_script, remote_script)


def _run_setup(client: IBMiClient, ifs_dir: str, lib_stg: str) -> None:
    setup_cmd = (
        f"system \"RUNSQLSTM SRCSTMF('{ifs_dir}/scripts/setup.sql') "
        f"SETVAR((LIB_STG '{lib_stg}')) COMMIT(*NONE) NAMING(*SQL)\""
    )
    client.ssh_run(setup_cmd)


def _submit_job(client: IBMiClient, lib_stg: str, ifs_dir: str, outq: str, jobq: str) -> None:
    submit_cmd = (
        f"system \"SBMJOB CMD(CALL PGM({lib_stg}/PROCESS) PARM('{lib_stg}' "
        f"'{ifs_dir}' '{outq}')) JOBQ({jobq})\""
    )
    client.ssh_run(submit_cmd)


def _wait_for_marker(
    client: IBMiClient,
    ifs_dir: str,
    csv_path: Path,
    *,
    fetch_outputs: bool,
    log: logging.Logger,
    timeout: int,
) -> None:
    marker_dir = f"{ifs_dir}/run"
    end = time.time() + timeout
    status_file = None
    while time.time() < end:
        entries = client.sftp.listdir(marker_dir)
        status_file = next((name for name in entries if name.endswith(".status")), None)
        if status_file:
            break
        time.sleep(5)
    if not status_file:
        raise TimeoutError("Timed out waiting for marker file")
    local_marker = Path("outputs") / status_file
    client.sftp_get(f"{marker_dir}/{status_file}", local_marker)
    result = local_marker.read_text().strip()
    if "FAILED" in result:
        raise RuntimeError(f"Remote job failed: {result}")
    if fetch_outputs:
        out_dir = Path("outputs")
        out_dir.mkdir(exist_ok=True)
        result_remote = f"{ifs_dir}/out/{csv_path.stem}_result.csv"
        result_local = out_dir / f"{csv_path.stem}_result.csv"
        try:
            client.sftp_get(result_remote, result_local)
        except Exception as exc:  # pragma: no cover - remote optional
            log.warning("Could not fetch result CSV: %s", exc)


@timed
def run_workflow(
    file_path: Path,
    config,
    *,
    sync: bool = False,
    fetch_outputs: bool = False,
    timeout: int = 600,
    dry_run: bool = False,
) -> None:
    """High level ingest/apply workflow."""
    log = logging.getLogger(__name__)

    src = Path(file_path)
    csv_path = _prepare_csv(src, log)

    ifs_dir = _ensure_safe(config.ifs_dir, "ifs_dir")
    lib_stg = _ensure_safe(config.lib_stg, "lib_stg")
    outq = _ensure_safe(config.outq, "outq")
    jobq = _ensure_safe(config.jobq, "jobq")

    remote_dirs = _remote_dirs(ifs_dir)

    csv_name = _ensure_safe(csv_path.name, "csv file name")
    remote_csv = f"{ifs_dir}/in/{csv_name}"

    with IBMiClient(config, dry_run=dry_run) as client:
        client.ensure_remote_dirs(remote_dirs)

        if sync:
            _sync_scripts(client, ifs_dir)

        client.sftp_put(csv_path, remote_csv)
        _run_setup(client, ifs_dir, lib_stg)
        _submit_job(client, lib_stg, ifs_dir, outq, jobq)

        if not dry_run:
            _wait_for_marker(
                client,
                ifs_dir,
                csv_path,
                fetch_outputs=fetch_outputs,
                log=log,
                timeout=timeout,
            )

    log.info("Workflow complete")


@timed
def teardown(config, *, dry_run: bool = False) -> None:
    """Drop staging schema and objects."""
    ifs_dir = _ensure_safe(config.ifs_dir, "ifs_dir")
    lib_stg = _ensure_safe(config.lib_stg, "lib_stg")
    cmd = (
        f"system \"RUNSQLSTM SRCSTMF('{ifs_dir}/scripts/teardown.sql') "
        f"SETVAR((LIB_STG '{lib_stg}')) COMMIT(*NONE) NAMING(*SQL)\""
    )
    with IBMiClient(config, dry_run=dry_run) as client:
        client.ssh_run(cmd)
