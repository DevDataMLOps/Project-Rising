# Demo Recording Checklist

## One Day Before

- [ ] Replace README team-role `TBD` values.
- [ ] Add the public Streamlit deployment URL.
- [ ] Confirm the public API and `/docs` URLs load in an incognito window.
- [ ] Replace the dashboard screenshot with the current decision-support panel.
- [ ] Run `python -m pytest -q` and confirm GitHub Actions is green.
- [ ] Rehearse the script twice and keep the final take between 3 and 5 minutes.

## Before Recording

- [ ] Use a clean browser profile and hide bookmarks, notifications, and secrets.
- [ ] Set browser zoom so the prediction score and evidence fit on screen.
- [ ] Open README architecture, Streamlit, Swagger UI, and a terminal in demo order.
- [ ] Start the API with `python -m uvicorn main:app`.
- [ ] Start the dashboard with `python -m streamlit run demo/pipeline_operations_dashboard.py`.
- [ ] Run `python demo/run_streaming_demo.py` once to verify permissions.
- [ ] Confirm microphone level, 1080p capture, and readable terminal font.

## Required Proof Points On Screen

- [ ] Valid event accepted.
- [ ] Duplicate event blocked.
- [ ] Malformed event routed to DLQ.
- [ ] Failed event recovered after retry.
- [ ] Disease-risk score, level, factors, evidence, and recommendations visible.
- [ ] Swagger sample endpoint returns computed JSON.
- [ ] Responsible-use disclaimer visible or spoken.

## Final Review

- [ ] Runtime is 3–5 minutes.
- [ ] No passwords, tokens, personal data, or unrelated tabs appear.
- [ ] Audio is clear and code/output is legible.
- [ ] Captions and project name are spelled correctly.
- [ ] Video link works without sign-in.
- [ ] Add the video URL to README and the hackathon submission.
