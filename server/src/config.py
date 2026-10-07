import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("ETL_DATA_DIR", "data"))
