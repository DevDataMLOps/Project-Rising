from pathlib import Path

import pandas as pd


def discover_csv_files(raw_data_path: str | Path) -> list[Path]:
    """
    Find every CSV file inside the raw data folder.
    """
    raw_path = Path(raw_data_path)

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw data folder does not exist: {raw_path}"
        )

    csv_files = sorted(raw_path.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files were found inside: {raw_path}"
        )

    return csv_files


def extract_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Read one CSV file into a Pandas DataFrame.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    dataframe = pd.read_csv(path)

    if dataframe.empty:
        raise ValueError(f"Dataset is empty: {path.name}")

    print(
        f"Extracted {len(dataframe)} rows "
        f"from {path.name}"
    )

    return dataframe 