import logging
import re
import tempfile
import time
from pathlib import Path

from .ibmi_client import IBMiClient
from .utils import sha256_file, sniff_csv, timed, xlsx_to_csv

_SAFE_NAME = re.compile(r"^[A-Za-z0-9_./]+$")


def _ensure_safe(value: str, field: str) -> str:
    if not _SAFE_NAME.match(value):
        raise ValueError(f"Invalid characters in {field}")
    return value


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
    if src.suffix.lower() == ".xlsx":
        csv_path = src.with_suffix(".csv")
        xlsx_to_csv(src, csv_path)
    else:
        csv_path = src

    sniff_csv(csv_path)
    digest = sha256_file(csv_path)
    log.info("Local SHA256=%s", digest)

    ifs_dir = _ensure_safe(config.ifs_dir, "ifs_dir")
    lib_stg = _ensure_safe(config.lib_stg, "lib_stg")
    outq = _ensure_safe(config.outq, "outq")
    jobq = _ensure_safe(config.jobq, "jobq")

    remote_dirs = [
        ifs_dir,
        f"{ifs_dir}/in",
        f"{ifs_dir}/out",
        f"{ifs_dir}/run",
        f"{ifs_dir}/scripts",
    ]

    csv_name = _ensure_safe(csv_path.name, "csv file name")
    remote_csv = f"{ifs_dir}/in/{csv_name}"

    with IBMiClient(config, dry_run=dry_run) as client:
        client.ensure_remote_dirs(remote_dirs)

        if sync:
            for script in ("setup.sql", "apply.sql", "process.clp", "teardown.sql"):
                local_script = Path("ibmi") / script
                text = local_script.read_text()
                text = text.replace("LIB_STG_PLACEHOLDER", lib_stg)
                with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                    tmp.write(text)
                    tmp_path = Path(tmp.name)
                remote_script = f"{ifs_dir}/scripts/{script}"
                client.sftp_put(tmp_path, remote_script)
                tmp_path.unlink()

        client.sftp_put(csv_path, remote_csv)

        setup_cmd = (
            f"system \"RUNSQLSTM SRCSTMF('{ifs_dir}/scripts/setup.sql') "
            f"SETVAR((LIB_STG '{lib_stg}')) COMMIT(*NONE) NAMING(*SQL)\""
        )
        client.ssh_run(setup_cmd)

        submit_cmd = (
            f"system \"SBMJOB CMD(CALL PGM({lib_stg}/PROCESS) PARM('{lib_stg}' "
            f"'{ifs_dir}' '{outq}')) JOBQ({jobq})\""
        )
        client.ssh_run(submit_cmd)

        marker_dir = f"{ifs_dir}/run"
        if not dry_run:
            end = time.time() + timeout
            status_file = None
            while time.time() < end:
                entries = client.sftp.listdir(marker_dir)
                for name in entries:
                    if name.endswith(".status"):
                        status_file = name
                        break
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
