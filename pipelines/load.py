from pathlib import Path

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

    dataframe.to_csv(
        path,
        index=False,
    )

    print(
        f"Loaded {len(dataframe)} records "
        f"into {path}"
    )

    return path 