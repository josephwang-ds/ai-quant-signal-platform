# Offline ML artifacts (not loaded with torch / SB3 at runtime)

JSON results from offline trainers may be committed so Compare Models can show
rows without installing heavy ML stacks on Render:

- `scripts/train_cnn.py` → `cnn_<TICKER>.json`
- `scripts/train_lstm.py` → `lstm_<TICKER>.json`
- `scripts/train_rl.py` → `rl_<TICKER>.json` (**RL·离线·实验性·非收益承诺**)

Optional weight files (`.pt` / SB3 zips) stay local for reproduction.

Interview note: industry RL is mainly optimal execution / market making;
directional alpha is rare and overfit-prone — committed artifacts are constrained
experiments, not production alpha claims.

Production / Render installs `requirements.txt` only — never torch / gymnasium /
stable-baselines3. Runtime only reads JSON under `artifacts/` (no DL/RL imports).
