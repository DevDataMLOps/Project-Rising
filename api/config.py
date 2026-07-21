from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
HEALTH_DATA_PATH = PROCESSED_DATA_DIR / "asean_health_indicators.csv"
INDICATOR_METADATA_PATH = PROCESSED_DATA_DIR / "indicator_metadata.csv"
API_VERSION = "2.0.0"
