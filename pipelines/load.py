from pathlib import Path
import os
import tempfile

import pandas as pd


def load_processed_csv(
    dataframe: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """
    Save a processed DataFrame as a CSV file.
    """
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Write beside the destination, then atomically replace it. A failed ETL
    # therefore cannot leave the API serving a partially written CSV.
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        dataframe.to_csv(temporary_path, index=False, encoding="utf-8")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)

    print(
        f"Loaded {len(dataframe)} records "
        f"into {path}"
    )

    return path
