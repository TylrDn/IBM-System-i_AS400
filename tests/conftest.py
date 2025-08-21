import sys
import types
import csv as _csv
from pathlib import Path

# Ensure repository root is on sys.path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

try:  # pragma: no cover - exercised only when dependency missing
    import defusedcsv  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - executed when package unavailable
    def _sanitize(value):
        if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@"):
            return f"'{value}"
        return value

    class _Writer:
        def __init__(self, csvfile, *args, **kwargs):
            self._writer = _csv.writer(csvfile, *args, **kwargs)

        def writerow(self, row):
            self._writer.writerow([_sanitize(col) for col in row])

        def writerows(self, rows):
            for row in rows:
                self.writerow(row)

    def writer(csvfile, *args, **kwargs):
        return _Writer(csvfile, *args, **kwargs)

    module = types.ModuleType("defusedcsv")
    module.writer = writer
    module.QUOTE_MINIMAL = _csv.QUOTE_MINIMAL
    module.QUOTE_ALL = _csv.QUOTE_ALL
    module.QUOTE_NONNUMERIC = _csv.QUOTE_NONNUMERIC
    module.QUOTE_NONE = _csv.QUOTE_NONE
    sys.modules["defusedcsv"] = module
