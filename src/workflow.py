import logging
import time
from pathlib import Path

from .ibmi_client import IBMiClient
from .utils import sha256_file, sniff_csv, xlsx_to_csv, timed


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

    remote_dirs = [
        config.ifs_dir,
        f"{config.ifs_dir}/in",
        f"{config.ifs_dir}/out",
        f"{config.ifs_dir}/run",
        f"{config.ifs_dir}/scripts",
    ]

    remote_csv = f"{config.ifs_dir}/in/{csv_path.name}"

    with IBMiClient(config, dry_run=dry_run) as client:
        client.ensure_remote_dirs(remote_dirs)

        if sync:
            for script in ("setup.sql", "apply.sql", "process.clp", "teardown.sql"):
                local_script = Path("ibmi") / script
                remote_script = f"{config.ifs_dir}/scripts/{script}"
                client.sftp_put(local_script, remote_script)

        client.sftp_put(csv_path, remote_csv)

        setup_cmd = (
            f"system \"RUNSQLSTM SRCSTMF('{config.ifs_dir}/scripts/setup.sql') "
            f"SETVAR((LIB_STG '{config.lib_stg}')) COMMIT(*NONE) NAMING(*SQL)\""
        )
        client.ssh_run(setup_cmd)

        submit_cmd = (
            f"system \"SBMJOB CMD(CALL PGM({config.lib_stg}/PROCESS) PARM('{config.lib_stg}' "
            f"'{config.ifs_dir}' '{config.outq}')) JOBQ({config.jobq})\""
        )
        client.ssh_run(submit_cmd)

        marker_dir = f"{config.ifs_dir}/run"
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
                result_remote = f"{config.ifs_dir}/out/{csv_path.stem}_result.csv"
                result_local = out_dir / f"{csv_path.stem}_result.csv"
                try:
                    client.sftp_get(result_remote, result_local)
                except Exception as exc:  # pragma: no cover - remote optional
                    log.warning("Could not fetch result CSV: %s", exc)

    log.info("Workflow complete")


@timed
def teardown(config, *, dry_run: bool = False) -> None:
    """Drop staging schema and objects."""
    cmd = (
        f"system \"RUNSQLSTM SRCSTMF('{config.ifs_dir}/scripts/teardown.sql') "
        f"SETVAR((LIB_STG '{config.lib_stg}')) COMMIT(*NONE) NAMING(*SQL)\""
    )
    with IBMiClient(config, dry_run=dry_run) as client:
        client.ssh_run(cmd)
