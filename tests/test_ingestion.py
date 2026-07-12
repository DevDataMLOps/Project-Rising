import pytest

from pipelines.extract import discover_csv_files, extract_csv


def test_discover_csv_files_returns_sorted_csv_paths(tmp_path):
    first_file = tmp_path / "b_dataset.csv"
    second_file = tmp_path / "a_dataset.csv"
    ignored_file = tmp_path / "notes.txt"

    first_file.write_text("country,year,value\nBrunei,2020,1\n")
    second_file.write_text("country,year,value\nCambodia,2020,2\n")
    ignored_file.write_text("not a csv")

    csv_files = discover_csv_files(tmp_path)

    assert [path.name for path in csv_files] == [
        "a_dataset.csv",
        "b_dataset.csv",
    ]


def test_discover_csv_files_raises_for_missing_folder(tmp_path):
    missing_path = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        discover_csv_files(missing_path)


def test_discover_csv_files_raises_for_non_directory(tmp_path):
    file_path = tmp_path / "raw.csv"
    file_path.write_text("country,year,value\nBrunei,2020,1\n")

    with pytest.raises(NotADirectoryError):
        discover_csv_files(file_path)


def test_extract_csv_reads_valid_csv(tmp_path):
    csv_path = tmp_path / "health.csv"
    csv_path.write_text(
        "country,year,value\nBrunei,2020,1\n",
        encoding="utf-8",
    )

    dataframe = extract_csv(csv_path)

    assert list(dataframe.columns) == [
        "country",
        "year",
        "value",
    ]
    assert len(dataframe) == 1


def test_extract_csv_reads_cp1252_file(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    csv_path.write_bytes(
        b"indicator,description\n"
        b"life_expectancy,child\x92s birth\n"
    )

    dataframe = extract_csv(csv_path)

    expected_description = "child" + chr(8217) + "s birth"

    assert dataframe.loc[0, "description"] == expected_description


def test_extract_csv_rejects_non_csv_file(tmp_path):
    text_path = tmp_path / "health.txt"
    text_path.write_text("country,year,value\nBrunei,2020,1\n")

    with pytest.raises(ValueError, match="Expected a CSV file"):
        extract_csv(text_path)
