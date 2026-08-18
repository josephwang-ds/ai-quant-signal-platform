# Notebooks

Runnable walkthroughs of the machinery that **actually exists** in this repo.
There is deliberately no notebook for unbuilt work: an empty notebook opened in
an interview is worse than no notebook.

| Notebook | What it shows |
| --- | --- |
| [`01_timestamp_discipline.ipynb`](01_timestamp_discipline.ipynb) | The five instants a text signal has, why two of them are derived and cannot be supplied, fail-closed calendars, the look-ahead guard, and the gap metrics that belong in an evidence package. |
| [`02_edgar_and_the_utc_discovery.ipynb`](02_edgar_and_the_utc_discovery.ipynb) | EDGAR collection and the observed-vs-simulated provenance split — then re-derives, from real SEC payloads, that `acceptanceDateTime` is UTC rather than Eastern. |
| [`03_hac_inference.ipynb`](03_hac_inference.ipynb) | Why a mean without a standard error is not a result: naive vs HAC t-statistics, the pre-registered bandwidth rule, incremental signal value, and break-even capital. |

## Running them

Jupyter is **not** installed in `backend/.venv` — it is a development tool, not a
runtime dependency of the service, so it is intentionally absent from
`requirements.txt`. Two ways to run:

**VS Code / Cursor** — open any `.ipynb` and select `backend/.venv` as the
kernel. Nothing to install if you already have the Python extension.

**Jupyter in the browser**

```bash
cd backend && .venv/bin/python -m pip install jupyter && cd ..
backend/.venv/bin/python -m jupyter lab notebooks/
```

Either way, use the interpreter at `backend/.venv/bin/python` — the notebooks
import from `app.*`.

## Design notes

Three properties worth knowing before you edit them:

**They run offline.** Every cell works against saved real SEC payloads in
`backend/tests/fixtures/edgar/`. Notebook 02 ends with an optional, commented-out
live cell; it needs your own name and email, because SEC requires a genuine
contact from automated clients.

**The path bootstrap is location-independent.** The first cell walks up from the
working directory until it finds `backend/app`, so the notebooks work whether
Jupyter was launched from the repo root, from `notebooks/`, or from an editor.

**No result numbers are written into the prose.** Every figure in the narrative
is computed and printed by the cell above it. This is deliberate: pre-writing
plausible-looking numbers anchors the reader — and the author — before the
evidence exists, which is the exact failure the text-signals track is built to
measure in Experiment C.

To verify a notebook still runs after editing, without launching Jupyter:

```bash
cd notebooks && ../backend/.venv/bin/python -c "
import json, sys
cells = json.load(open(sys.argv[1]))['cells']
exec(compile('\n'.join(''.join(c['source']) for c in cells if c['cell_type']=='code'), sys.argv[1], 'exec'), {'__name__':'__main__'})
" 01_timestamp_discipline.ipynb
```
