from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


SUPPORTED_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "cp1252",
    "latin1",
]


def discover_csv_files(
    raw_data_path: str | Path,
) -> list[Path]:
    """
    Find every CSV file inside the raw-data folder.
    """
    raw_path = Path(raw_data_path)

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw data folder does not exist: {raw_path}"
        )

    if not raw_path.is_dir():
        raise NotADirectoryError(
            f"Raw data path is not a folder: {raw_path}"
        )

    csv_files = sorted(raw_path.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files were found inside: {raw_path}"
        )

    return csv_files


def extract_csv(
    file_path: str | Path,
) -> pd.DataFrame:
    """
    Read one CSV file using several common encodings.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    if path.suffix.lower() != ".csv":
        raise ValueError(
            f"Expected a CSV file: {path.name}"
        )

    if path.stat().st_size == 0:
        raise ValueError(
            f"CSV file is empty: {path.name}"
        )

    last_error: Exception | None = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            dataframe = pd.read_csv(
                path,
                encoding=encoding,
            )

            if dataframe.empty:
                raise ValueError(
                    f"Dataset contains no rows: {path.name}"
                )

            print(
                f"Extracted {len(dataframe)} rows "
                f"from {path.name} using {encoding}"
            )

            return dataframe

        except UnicodeDecodeError as error:
            last_error = error

        except EmptyDataError as error:
            raise ValueError(
                f"No columns or records found in {path.name}"
            ) from error

        except ParserError as error:
            raise ValueError(
                f"Could not parse CSV structure in {path.name}"
            ) from error

    raise ValueError(
        f"Could not decode {path.name} "
        "with the supported encodings."
    ) from last_error
