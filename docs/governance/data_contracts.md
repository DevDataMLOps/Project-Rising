# Data Contracts

Project RISING treats every incoming batch file and streaming event as a
contracted data product. Records that do not satisfy the contract are not
silently dropped; they are rejected, retried, quarantined, or routed to a
dead-letter queue.

## Batch Health Record Contract

Required fields:

- `country`: ASEAN country name after standardization
- `year`: observation year between 1900 and 2100
- `indicator`: normalized indicator code
- `value`: numeric observation value

Optional fields:

- `sub_indicator`: more specific measure, such as capital health expenditure
- `sex`: Male or Female where applicable
- `unit`: measurement unit

## Weather Event Contract

Required fields:

- `event_id`: unique event identifier
- `station_id`: station code such as `TH-BKK-01`
- `country`: ASEAN country name
- `timestamp`: event timestamp
- `temperature_c`: numeric temperature
- `humidity_pct`: numeric percentage from 0 to 100
- `rainfall_mm`: non-negative rainfall value

## Contract Handling

- Accepted records move to curated storage or warehouse facts.
- Invalid batch records are quarantined.
- Invalid streaming records are retried until retry limits are reached.
- Permanently failed events are written to the DLQ with failure context.
