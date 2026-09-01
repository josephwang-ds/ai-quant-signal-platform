"""FinBERT features over filing text, and the three things that make them usable.

A transformer is easy to add and hard to add honestly. Three properties decide
whether these features mean anything: the model must predate the sample, the
cache must be keyed by which model produced it, and the text fed to it must be
the disclosure rather than the envelope it arrived in.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from filing_triage.text_model import (
    FEATURE_COLUMNS,
    MODEL_ID,
    MODEL_REVISION,
    TextCache,
    available,
    disclosure_text,
    encoded_from_heading,
    text_features,
    text_key,
)

COVER = ("aapl-20260730 false 0000320193 us-gaap:CommonStockMember 2026-07-30 "
         "UNITED STATES SECURITIES AND EXCHANGE COMMISSION Washington, D.C. 20549 "
         "FORM 8-K CURRENT REPORT Pursuant to Section 13 ")
BODY = "Item 2.02 Results of Operations. The company reported record revenue."


class TestTheEnvelopeIsStripped:
    def test_extraction_starts_at_the_item_heading(self):
        """The first 1,800 characters of a filed 8-K are XBRL, the SEC address
        block and checkbox instructions -- near-identical across every issuer.
        Encoding them encodes the envelope."""
        assert disclosure_text(COVER + BODY).startswith("Item 2.02")

    def test_text_without_a_heading_is_kept_not_dropped(self):
        """An unparsed filing should still be encoded; it should just be
        counted, so a parsing regression is a number rather than quietly worse
        features."""
        assert disclosure_text("no heading here") == "no heading here"

    def test_the_parse_rate_is_measurable(self):
        rate = encoded_from_heading([COVER + BODY, "no heading here"])
        assert rate == pytest.approx(0.5)

    def test_an_empty_document_does_not_raise(self):
        assert disclosure_text(None) == ""
        assert disclosure_text("") == ""

    def test_the_window_is_bounded(self):
        """BERT takes 512 tokens; a slice far longer would be truncated blindly
        by the tokenizer instead of deliberately here."""
        assert len(disclosure_text(BODY + "x" * 50_000)) <= 2400


class TestTheCacheKnowsWhichModelMadeIt:
    def test_the_key_covers_model_revision_and_text(self):
        assert text_key("a") != text_key("b")

    def test_a_cache_from_another_model_is_discarded_not_mixed(self, tmp_path):
        """Reusing another model's vectors is how a feature stops meaning what
        its name says, without anything failing."""
        (tmp_path / "index.json").write_text(json.dumps(
            {"model": "some/other-model", "revision": "main",
             "max_tokens": 512, "keys": {"abc": {"row": 0, "tone": [0, 0, 1]}}}))
        cache = TextCache(tmp_path)
        assert cache.index["model"] == MODEL_ID
        assert cache.index["keys"] == {}

    def test_the_fingerprint_names_the_model_and_revision(self, tmp_path):
        fingerprint = TextCache(tmp_path).fingerprint()
        assert fingerprint["model"] == MODEL_ID
        assert fingerprint["revision"] == MODEL_REVISION

    def test_a_round_trip_preserves_the_vector(self, tmp_path):
        cache = TextCache(tmp_path)
        cache.add(text_key("x"), np.arange(4, dtype=np.float32), [0.1, 0.2, 0.7])
        cache.save()
        reopened = TextCache(tmp_path)
        vector, tone = reopened.get(text_key("x"))
        assert np.allclose(vector, np.arange(4))
        assert tone == pytest.approx([0.1, 0.2, 0.7])


class TestTheModelPredatesTheSample:
    def test_the_model_is_pinned_with_a_revision(self):
        """FinBERT is a 2019 model fine-tuned on data ending in 2014, which is
        what makes scoring 2022-2026 filings with it causal. A floating model
        id would silently break that."""
        assert MODEL_ID == "ProsusAI/finbert"
        assert MODEL_REVISION


class TestFeaturesDegradeRatherThanFail:
    def test_an_empty_cache_yields_missing_not_zero(self, tmp_path):
        """Zero tone would read as a confident neutral rather than as an
        unencoded document."""
        events = pd.DataFrame({
            "event_id": ["a", "b"], "ticker": ["AAPL", "AAPL"],
            "acceptance_time": pd.to_datetime(["2024-01-01T12:00:00Z", "2024-04-01T12:00:00Z"]),
            "text": [COVER + BODY, COVER + BODY]})
        features = text_features(events, TextCache(tmp_path))
        assert set(FEATURE_COLUMNS) <= set(features.columns)
        assert features["fin_tone_positive"].isna().all()

    def test_events_without_text_return_no_columns(self, tmp_path):
        events = pd.DataFrame({"event_id": ["a"], "ticker": ["AAPL"],
                               "acceptance_time": pd.to_datetime(["2024-01-01T12:00:00Z"])})
        assert text_features(events, TextCache(tmp_path)).empty

    def test_availability_is_reported_without_importing_torch(self):
        assert isinstance(available(), bool)


class TestDistancesAreCausal:
    def test_the_first_filing_has_no_prior_distance(self, tmp_path):
        """Nothing precedes it, so there is no earlier document to be far from."""
        cache = TextCache(tmp_path)
        events = pd.DataFrame({
            "event_id": ["a", "b", "c"], "ticker": ["AAPL"] * 3,
            "acceptance_time": pd.to_datetime(
                ["2024-01-01T12:00:00Z", "2024-04-01T12:00:00Z", "2024-07-01T12:00:00Z"]),
            "text": ["Item 1.01 alpha", "Item 2.02 beta", "Item 8.01 gamma"]})
        for i, text in enumerate(events["text"]):
            vector = np.zeros(4, dtype=np.float32)
            vector[i % 4] = 1.0
            cache.add(text_key(disclosure_text(text)), vector, [0.1, 0.2, 0.7])
        features = text_features(events, cache)
        assert np.isnan(features["fin_embed_dist_prior"].iloc[0])
        assert np.isnan(features["fin_embed_dist_centroid"].iloc[0])
        assert np.isfinite(features["fin_embed_dist_prior"].iloc[1])

    def test_a_later_filing_cannot_change_an_earlier_distance(self, tmp_path):
        """The centroid runs forward rather than being taken over the whole
        history: a centroid including later filings is the future averaged into
        the past, which is an unshifted rolling window in a vector space."""
        cache = TextCache(tmp_path)
        texts = ["Item 1.01 alpha", "Item 2.02 beta", "Item 8.01 gamma",
                 "Item 5.02 delta"]
        for i, text in enumerate(texts):
            vector = np.zeros(4, dtype=np.float32)
            vector[i] = 1.0
            cache.add(text_key(disclosure_text(text)), vector, [0.1, 0.2, 0.7])

        def build(n):
            events = pd.DataFrame({
                "event_id": [f"e{i}" for i in range(n)], "ticker": ["AAPL"] * n,
                "acceptance_time": pd.to_datetime(
                    [f"2024-0{i + 1}-01T12:00:00Z" for i in range(n)]),
                "text": texts[:n]})
            return text_features(events, cache)

        full = build(4)
        partial = build(3)
        assert np.allclose(full["fin_embed_dist_centroid"].to_numpy()[:3],
                           partial["fin_embed_dist_centroid"].to_numpy(),
                           equal_nan=True)


class TestFailedAblationColumnsCannotShip:
    """The transformer features measured *worse* than not having them, and a
    feature that fails its own ablation must not reach the model that writes the
    cards. That is enforced by structure -- the export keeps them in a frame
    beside the shipped matrix rather than joined into it -- and structure is what
    a later edit quietly undoes, so it is asserted here."""

    def test_the_export_never_joins_them_into_the_shipped_matrix(self):
        import ast
        from pathlib import Path

        source = Path("scripts/export_self_relative_evidence.py").read_text()
        tree = ast.parse(source)
        builder = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef)
                       and node.name == "build_inputs")
        # `features` is the shipped matrix; the text frame must never be an
        # argument to a join or concat that produces it.
        assigns_to_features = [
            node for node in ast.walk(builder)
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "features"
                    for t in node.targets)]
        rendered = [ast.unparse(node.value) for node in assigns_to_features]
        assert not any("text" in expression for expression in rendered), rendered

    def test_the_shipped_evidence_carries_no_transformer_columns(self):
        import csv
        from pathlib import Path

        path = Path("evidence/real_run/oos_importance.csv")
        if not path.exists():
            pytest.skip("evidence package not built")
        with path.open() as handle:
            names = [row["feature"] for row in csv.DictReader(handle)]
        assert not [n for n in names if n.startswith("fin_")]
