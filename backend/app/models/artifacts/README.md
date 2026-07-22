# Offline ML artifacts (not loaded with torch at runtime)

JSON results from `scripts/train_lstm.py` may be committed so Compare Models
can show an LSTM row without installing torch on Render.

- `lstm_<TICKER>.json` — metrics + equity curve (safe to commit)
- `lstm_<TICKER>.pt` — weights for local reproduction (optional; large)

Production / Render installs `requirements.txt` only — never `torch`.
