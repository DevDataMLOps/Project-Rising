from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from warehouse.db import get_engine  # noqa: E402


STREAMING_DIR = PROJECT_ROOT / "data" / "streaming"
INPUT_PATH = STREAMING_DIR / "weather_events.jsonl"
ACCEPTED_PATH = STREAMING_DIR / "accepted_weather_events.jsonl"
DLQ_PATH = STREAMING_DIR / "weather_events_dlq.jsonl"
CHECKPOINT_PATH = STREAMING_DIR / "checkpoints.txt"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    return records


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0

    return len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])


def get_warehouse_weather_count() -> tuple[int | None, str]:
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT COUNT(*) FROM fact_weather_observation")
            )
            return int(result.scalar_one()), "Connected"
    except SQLAlchemyError:
        return None, "Not connected"


def status_label(is_healthy: bool) -> str:
    return "Healthy" if is_healthy else "Needs attention"


def build_event_dataframe(events: list[dict]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame()

    dataframe = pd.DataFrame(events)
    if "timestamp" in dataframe.columns:
        dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], errors="coerce")

    return dataframe


def main() -> None:
    st.set_page_config(
        page_title="Project RISING Operations",
        page_icon="R",
        layout="wide",
    )

    st.title("Project RISING Pipeline Operations")
    st.caption(
        "Resilient Intelligent Surveillance & Integrated Next-Generation Healthcare"
    )

    st.markdown(
        """
        This dashboard monitors the resilience proof points for the Project RISING
        hybrid data pipeline: accepted records, DLQ isolation, checkpointing,
        retry recovery, and warehouse synchronization.
        """
    )

    input_events = read_jsonl(INPUT_PATH)
    accepted_events = read_jsonl(ACCEPTED_PATH)
    dlq_events = read_jsonl(DLQ_PATH)
    checkpoint_count = count_lines(CHECKPOINT_PATH)
    warehouse_count, warehouse_status = get_warehouse_weather_count()

    input_count = len(input_events)
    accepted_count = len(accepted_events)
    dlq_count = len(dlq_events)
    recovered_after_retry = max(accepted_count - input_count, 0)
    zero_data_loss = accepted_count >= input_count and dlq_count >= 1

    st.subheader("Pipeline Status")

    status_cols = st.columns(4)
    status_cols[0].metric("Batch Pipeline", "Ready")
    status_cols[1].metric("Streaming Pipeline", status_label(accepted_count > 0))
    status_cols[2].metric("Warehouse", warehouse_status)
    status_cols[3].metric("Zero Data Loss", "YES" if zero_data_loss else "Pending")

    st.subheader("Operational Metrics")

    metric_cols = st.columns(5)
    metric_cols[0].metric("Generated Inputs", input_count)
    metric_cols[1].metric("Accepted Events", accepted_count)
    metric_cols[2].metric("DLQ Events", dlq_count)
    metric_cols[3].metric("Checkpoints", checkpoint_count)
    metric_cols[4].metric("Recovered After Retry", recovered_after_retry)

    if warehouse_count is not None:
        st.metric("Warehouse Weather Facts", warehouse_count)
    else:
        st.info(
            "Warehouse is not connected. Start PostgreSQL with "
            "`docker compose up -d postgres` to show warehouse counts."
        )

    st.subheader("Record Routing")

    routing_dataframe = pd.DataFrame(
        {
            "route": ["Generated", "Accepted", "DLQ", "Recovered After Retry"],
            "records": [
                input_count,
                accepted_count,
                dlq_count,
                recovered_after_retry,
            ],
        }
    )
    chart = px.bar(
        routing_dataframe,
        x="route",
        y="records",
        color="route",
        text="records",
        title="Pipeline record movement",
    )
    chart.update_layout(showlegend=False)
    st.plotly_chart(chart, use_container_width=True)

    accepted_dataframe = build_event_dataframe(accepted_events)
    dlq_dataframe = build_event_dataframe(dlq_events)

    tab_accepted, tab_dlq, tab_checkpoints, tab_demo = st.tabs(
        ["Accepted Events", "DLQ", "Checkpoints", "How To Demo"]
    )

    with tab_accepted:
        st.write("Validated records that survived the pipeline and can be trusted.")
        if accepted_dataframe.empty:
            st.warning(
                "No accepted events found. Run `py demo\\run_streaming_demo.py` first."
            )
        else:
            st.dataframe(accepted_dataframe, use_container_width=True)

    with tab_dlq:
        st.write("Malformed or permanently failed records isolated from trusted data.")
        if dlq_dataframe.empty:
            st.warning("No DLQ records found yet.")
        else:
            st.dataframe(dlq_dataframe, use_container_width=True)

    with tab_checkpoints:
        st.write("Fingerprints used to prevent duplicate event processing.")
        if not CHECKPOINT_PATH.exists():
            st.warning("No checkpoint file found yet.")
        else:
            checkpoints = [
                {"fingerprint": line}
                for line in CHECKPOINT_PATH.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            st.dataframe(pd.DataFrame(checkpoints), use_container_width=True)

    with tab_demo:
        st.markdown(
            """
            Run the resilience demo:

            ```powershell
            py demo\\run_streaming_demo.py
            ```

            Run the warehouse-backed demo:

            ```powershell
            docker compose up -d postgres
            py demo\\run_streaming_demo.py --load-postgres
            ```

            Refresh this dashboard after each run.
            """
        )


if __name__ == "__main__":
    main()
