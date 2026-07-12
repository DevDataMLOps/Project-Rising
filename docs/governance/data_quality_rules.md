# Data Quality Rules

Project RISING applies quality rules before data is trusted by analytics,
AI models, or dashboards.

## Required Rules

- Country must be a supported ASEAN country.
- Year must be between 1900 and 2100.
- Indicator must be present and non-empty.
- Value must be numeric and non-null.
- Weather humidity must be between 0 and 100.
- Weather rainfall must be greater than or equal to 0.
- Event IDs must be unique for streaming records.

## Duplicate Rules

Health observations are unique by:

- `country`
- `year`
- `indicator`
- `sub_indicator`
- `sex`

Weather observations are unique by:

- `event_id`

## Failure Handling

- Schema failures are rejected before load.
- Retryable streaming failures are sent to retry handling.
- Exhausted retry failures are routed to the DLQ.
- Pipeline metrics record accepted, rejected, and DLQ counts.
