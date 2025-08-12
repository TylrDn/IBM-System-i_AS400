# IBM i Staging Workflow

```
Local            SSH/SFTP              IBM i
-----            --------              -----
file.csv/.xlsx  --->  /IFS/staging/in          (upload)
                        |
                        v
                 setup.sql via RUNSQLSTM
                        |
                        v
                 SBMJOB CALL PROCESS
                        |
               +--------+--------+
               |                 |
           STG tables       run marker
               |
               v
           apply.sql -> SHADOW_*
               |
               +--> result.csv /out
```

## Runbook
1. `make install`
2. `python -m src.runner --file tests/smoke_local.csv --dry-run`
3. Remove `--dry-run` when ready and supply a real IBM i host.
4. Optional: `--sync` uploads `ibmi/` scripts to the remote `scripts` directory.
5. Output CSVs and marker files land in `outputs/` when fetched.
