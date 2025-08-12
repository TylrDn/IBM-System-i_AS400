import argparse
import logging
from pathlib import Path

from .utils import load_config, setup_logger
from .workflow import run_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IBM i staging workflow")
    parser.add_argument("--file", required=True, help="Path to CSV or XLSX")
    parser.add_argument("--sync", action="store_true", help="Upload scripts before run")
    parser.add_argument("--fetch-outputs", action="store_true", help="Download result files")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--jobq")
    parser.add_argument("--outq")
    parser.add_argument("--lib-stg")
    parser.add_argument("--ifs-dir")
    parser.add_argument("--teardown", action="store_true", help="Drop staging schema")
    return parser.parse_args()


def main() -> int:
    setup_logger()
    args = parse_args()
    try:
        cfg = load_config()
        if args.jobq:
            cfg.jobq = args.jobq
        if args.outq:
            cfg.outq = args.outq
        if args.lib_stg:
            cfg.lib_stg = args.lib_stg
        if args.ifs_dir:
            cfg.ifs_dir = args.ifs_dir
        if args.teardown:
            from .workflow import teardown

            teardown(cfg, dry_run=args.dry_run)
        else:
            run_workflow(
                Path(args.file),
                cfg,
                sync=args.sync,
                fetch_outputs=args.fetch_outputs,
                timeout=args.timeout_seconds,
                dry_run=args.dry_run,
            )
    except Exception as exc:  # pragma: no cover - CLI wrapper
        logging.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
