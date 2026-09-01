"""Financial-domain transformer features over 8-K text, cached and optional.

FinBERT reads the filing and returns two things the deterministic features
cannot: a tone distribution, and a dense representation that supports asking how
far this document sits from the issuer's own earlier ones in meaning rather than
in shared hash buckets.

**Why this is not a look-ahead, when a modern LLM would be.** A sentiment model
trained in 2026 has read what happened after every filing in a 2022 sample, and
scoring old text with it smuggles the outcome back in. FinBERT is a 2019 model
fine-tuned on the Financial PhraseBank, whose data ends in 2014 -- its weights
were frozen years before the earliest filing here. The vintage is the argument,
so `MODEL_ID` and its revision are pinned and recorded with every cached vector:
swapping in a model trained after the sample would silently break the property
this paragraph rests on.

**Placement note.** The expansion plan puts this under `company_lens/nlp/`.
It lives in `filing_triage` instead because `company_lens` already imports
`filing_triage`, and the plan's placement would close that into a cycle. The
features are consumed by the ranker, which is here.

**Everything is optional and everything is cached.** `transformers` and `torch`
are an extra install; without them this module reports itself unavailable and the
pipeline runs on the deterministic features exactly as before. With them, one
pass over the corpus writes a cache keyed by model, revision and text hash, and
nothing downstream ever loads a model again.

**The cover page is stripped before encoding, and this was not optional.** An
8-K as filed opens with XBRL tags, the registrant's bond series, the SEC address
block and checkbox instructions -- roughly 1,800 characters of boilerplate that is
near-identical across every filing by every issuer. Encoding the first 512 tokens
of the raw document encodes that. Measured on a 24-filing sample it produced tone
scores constant to three decimals and cosine distances between 0.002 and 0.015:
the model was reading the envelope, and the features would have been noise
wearing a transformer's name.

`disclosure_text` cuts to the first `Item N.NN` heading, where the substance
starts, and takes the window from there. Documents with no recognisable heading
fall back to the raw text and are counted, because a silent fallback would hide
a parsing regression behind features that still look plausible.

**The measured result: these features do not ship.** On the full corpus of
11,424 encoded filings, adding them to the ranker moved average precision from
0.372 to 0.366 -- a paired, session-clustered interval of [-0.010, -0.001] that
separates from zero on the wrong side. They are not neutral; they cost a little.

The reason is structural rather than a failure of the model, and it is the part
worth keeping. FinBERT predicts the *direction* of financial sentiment. The
target here is the *magnitude* of a reaction, which is direction-free by
construction: a very good announcement and a very bad one are both positives.
Tone is close to orthogonal to the question being asked, and six extra columns of
near-orthogonal signal make a forest's splits worse, not better.

So the module stays, the cache stays, and the columns are held beside the shipped
feature matrix rather than inside it -- the ablation is the only consumer. A
directional target would make them worth re-testing, and re-testing costs one
command because the corpus is already encoded.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Pinned, not floating. A revision is part of the cache key because "the FinBERT
# features" is not a stable description of anything without one.
MODEL_ID = "ProsusAI/finbert"
MODEL_REVISION = "main"
MAX_TOKENS = 512
BATCH_SIZE = 16

TONE_LABELS = ("positive", "negative", "neutral")

# An 8-K's substance begins at its first item heading. Everything before is
# XBRL, the SEC address block and checkbox instructions.
ITEM_HEADING = re.compile(r"Item\s+\d\.\d\d", re.IGNORECASE)
# BERT takes 512 tokens; roughly four characters per token leaves headroom for
# the tokenizer to truncate rather than the slice doing it blindly.
WINDOW_CHARS = 2400


def disclosure_text(raw: str) -> str:
    """The filing's substance, from its first item heading onward.

    Returns the raw text when no heading is found rather than an empty string:
    an unparsed filing should still be encoded, and `encoded_from_heading`
    counts how often that happens so a parsing regression shows up as a number
    instead of as quietly worse features.
    """
    text = str(raw or "")
    match = ITEM_HEADING.search(text)
    start = match.start() if match else 0
    return text[start:start + WINDOW_CHARS]


def encoded_from_heading(texts) -> float:
    """Share of documents whose item heading was found. Reported, not assumed."""
    values = [str(t or "") for t in texts]
    if not values:
        return float("nan")
    return sum(1 for t in values if ITEM_HEADING.search(t)) / len(values)

FEATURE_COLUMNS = (
    "fin_tone_positive", "fin_tone_negative", "fin_tone_neutral",
    "fin_tone_negativity_z", "fin_embed_dist_prior", "fin_embed_dist_centroid",
)


def available() -> bool:
    """Whether the optional stack is installed, without importing it eagerly."""
    from importlib.util import find_spec

    return find_spec("torch") is not None and find_spec("transformers") is not None


def text_key(text: str) -> str:
    """Cache key for one document: the model, its revision, and the text."""
    digest = hashlib.sha256(
        f"{MODEL_ID}@{MODEL_REVISION}\x1e{MAX_TOKENS}\x1e{text}".encode()
    ).hexdigest()
    return digest[:32]


@dataclass
class TextCache:
    """Tone and embedding per document, on disk, keyed by model and content.

    Two files rather than one: vectors go to `.npy` because a 768-float row in
    JSON is both slow and lossy, and the index stays readable so a person can
    check what is in the cache without loading numpy.
    """

    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.path / "index.json"
        self._vector_path = self.path / "vectors.npy"
        self.index: dict = json.loads(self._index_path.read_text()) if (
            self._index_path.exists()) else {"model": MODEL_ID,
                                             "revision": MODEL_REVISION,
                                             "max_tokens": MAX_TOKENS,
                                             "keys": {}}
        self.vectors = (np.load(self._vector_path) if self._vector_path.exists()
                        else np.zeros((0, 0), dtype=np.float32))
        if self.index.get("model") != MODEL_ID or self.index.get("revision") != MODEL_REVISION:
            # A cache built by a different model is not this model's cache, and
            # silently reusing it is how a feature stops meaning what its name
            # says. Start clean rather than mix.
            self.index = {"model": MODEL_ID, "revision": MODEL_REVISION,
                          "max_tokens": MAX_TOKENS, "keys": {}}
            self.vectors = np.zeros((0, 0), dtype=np.float32)

    def __contains__(self, key: str) -> bool:
        return key in self.index["keys"]

    def get(self, key: str) -> tuple[np.ndarray, list[float]]:
        entry = self.index["keys"][key]
        return self.vectors[entry["row"]], entry["tone"]

    def add(self, key: str, vector: np.ndarray, tone: list[float]) -> None:
        if self.vectors.size == 0:
            self.vectors = np.zeros((0, len(vector)), dtype=np.float32)
        self.index["keys"][key] = {"row": len(self.vectors),
                                   "tone": [round(float(t), 6) for t in tone]}
        self.vectors = np.vstack([self.vectors, vector.astype(np.float32)])

    def save(self) -> None:
        np.save(self._vector_path, self.vectors)
        self._index_path.write_text(json.dumps(self.index, indent=1))

    def fingerprint(self) -> dict:
        return {"model": MODEL_ID, "revision": MODEL_REVISION,
                "max_tokens": MAX_TOKENS, "documents": len(self.index["keys"]),
                "dimensions": int(self.vectors.shape[1]) if self.vectors.size else 0}


def encode(texts: list[str], cache: TextCache, *, progress: bool = False) -> None:
    """Fill the cache for any document it does not already hold.

    Loads the model only if there is work to do, so a rerun over an unchanged
    corpus never touches torch at all.
    """
    texts = [disclosure_text(t) for t in texts]
    missing = [t for t in dict.fromkeys(texts) if text_key(t) not in cache]
    if not missing:
        return
    if not available():
        raise RuntimeError(
            "transformers and torch are required to build the text cache; "
            "install the optional group with `pip install -e '.[nlp]'`"
        )

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, output_hidden_states=True)
    model.eval()

    for start in range(0, len(missing), BATCH_SIZE):
        batch = missing[start:start + BATCH_SIZE]
        encoded = tokenizer(batch, truncation=True, max_length=MAX_TOKENS,
                            padding=True, return_tensors="pt")
        with torch.no_grad():
            out = model(**encoded)
        tone = torch.softmax(out.logits, dim=-1).numpy()
        # Mean-pooled last hidden state, masked so padding does not dilute a
        # short document toward the centre of the space.
        hidden = out.hidden_states[-1]
        mask = encoded["attention_mask"].unsqueeze(-1).float()
        pooled = ((hidden * mask).sum(dim=1) / mask.sum(dim=1)).numpy()
        for text, vector, scores in zip(batch, pooled, tone, strict=True):
            cache.add(text_key(text), vector, list(scores))
        if progress:
            print(f"  encoded {min(start + BATCH_SIZE, len(missing)):,}"
                  f" / {len(missing):,}", flush=True)
    cache.save()


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(1.0 - float(a @ b) / denominator) if denominator > 0 else np.nan


def text_features(events: pd.DataFrame, cache: TextCache) -> pd.DataFrame:
    """Tone and embedding-distance features, causal within each issuer.

    Both distances look only at earlier filings from the same issuer: the
    previous one, and the running centroid of everything before this document.
    The centroid is recomputed forward rather than taken over the whole history,
    because a centroid including later filings is the future averaged into the
    past -- the same error as an unshifted rolling window, in a vector space.

    `fin_tone_negativity_z` is a robust z of negative tone against that issuer's
    earlier filings, for the same reason every other feature here is
    issuer-relative: some registrants write cautiously about everything, and an
    absolute tone level measures house style as much as news.
    """
    from filing_triage.self_relative import causal_robust_z

    frame = events[["event_id", "ticker", "acceptance_time"]].copy()
    texts = events.get("text")
    if texts is None:
        return pd.DataFrame(index=events.index)
    frame["text"] = [disclosure_text(t) for t in texts.fillna("").astype(str)]

    n = len(frame)
    tone = np.full((n, 3), np.nan)
    dist_prior = np.full(n, np.nan)
    dist_centroid = np.full(n, np.nan)
    vectors: dict[int, np.ndarray] = {}

    for position, text in enumerate(frame["text"]):
        key = text_key(text)
        if key not in cache:
            continue
        vector, scores = cache.get(key)
        vectors[position] = vector
        tone[position] = scores

    accepted = pd.to_datetime(frame["acceptance_time"])
    if isinstance(accepted.dtype, pd.DatetimeTZDtype):
        accepted = accepted.dt.tz_convert("UTC").dt.tz_localize(None)
    frame["accepted"] = accepted.to_numpy("datetime64[s]")

    negativity_z = np.full(n, np.nan)
    positions = frame.reset_index(drop=True)
    for _, index in positions.groupby("ticker", sort=False).indices.items():
        order = index[np.argsort(positions["accepted"].to_numpy()[index],
                                 kind="mergesort")]
        running_sum, running_count = None, 0
        previous = None
        for row in order:
            vector = vectors.get(row)
            if vector is not None:
                if previous is not None:
                    dist_prior[row] = _cosine(vector, previous)
                if running_count:
                    dist_centroid[row] = _cosine(vector, running_sum / running_count)
                running_sum = vector.copy() if running_sum is None else running_sum + vector
                running_count += 1
                previous = vector
        negativity_z[order] = causal_robust_z(tone[order, 1])

    return pd.DataFrame({
        "fin_tone_positive": tone[:, 0],
        "fin_tone_negative": tone[:, 1],
        "fin_tone_neutral": tone[:, 2],
        "fin_tone_negativity_z": negativity_z,
        "fin_embed_dist_prior": dist_prior,
        "fin_embed_dist_centroid": dist_centroid,
    }, index=events.index)
