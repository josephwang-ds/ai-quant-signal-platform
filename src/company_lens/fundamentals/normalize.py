"""Select annual fundamentals from SEC Company Facts by period context."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from itertools import pairwise
from typing import Any, Literal

from company_lens.contracts import (
    FundamentalCitation,
    FundamentalObservation,
    FundamentalSeries,
)
from company_lens.fundamentals.concepts import (
    CONCEPT_REGISTRY_VERSION,
    REPORTED_CONCEPTS,
    TAXONOMY,
    TEMPLATE_ID,
    ReportedConcept,
    UnitFamily,
)

ANNUAL_DURATION_DAYS = (350, 380)
SHARE_BASIS_RATIO_BOUNDS = (2.0 / 3.0, 1.5)
SeriesBasis = Literal["latest_restated", "as_reported"]


@dataclass(frozen=True)
class SubmissionMeta:
    accession: str
    form: str
    filing_date: str
    report_date: str
    acceptance_datetime: str | None
    primary_document: str | None


@dataclass(frozen=True)
class NormalizationResult:
    ticker: str
    cik: int
    company_name: str
    template: str
    requested_years: int
    annual_periods: tuple[dict[str, Any], ...]
    reported_series: tuple[FundamentalSeries, ...]
    as_reported_series: tuple[FundamentalSeries, ...]
    coverage: dict[str, Any]
    warnings: tuple[str, ...]
    knowledge_at: str | None
    provenance: dict[str, Any]


def normalize_annual_fundamentals(
    company_facts: dict[str, Any],
    *,
    ticker: str,
    submissions: dict[str, Any] | None = None,
    requested_years: int = 10,
    fiscal_years: tuple[int, ...] | None = None,
) -> NormalizationResult:
    """Normalize reviewed us-gaap annual facts into latest-restated research series.

    Displayed fiscal years are derived from each observation's period_end. Filing
    fy/fp values are preserved only as document metadata. As-reported / first-known
    facts are retained separately for future point-in-time valuation backtests.
    """
    cik = int(company_facts.get("cik") or company_facts.get("entity", {}).get("cik") or 0)
    if not cik and "cik" in str(company_facts):
        cik = int(str(company_facts.get("cik", "0")).lstrip("0") or "0")
    company_name = str(
        company_facts.get("entityName")
        or company_facts.get("entity", {}).get("name")
        or ticker.upper()
    )
    facts = company_facts.get("facts", {}).get(TAXONOMY, {})
    submission_index = _submission_index(submissions) if submissions else {}
    years = fiscal_years or _default_fiscal_years(facts, requested_years)

    restated_series: list[FundamentalSeries] = []
    as_reported_series: list[FundamentalSeries] = []
    coverage_flags: dict[str, list[dict[str, Any]]] = {
        "duplicate_context": [],
        "restated_value": [],
        "tag_substitution": [],
        "missing_period": [],
        "unexpected_unit": [],
        "duration_outlier": [],
        "acceptance_unresolved": [],
        "share_basis_discontinuity": [],
    }
    warnings: list[str] = []
    period_index: dict[int, dict[str, Any]] = {}

    for concept in REPORTED_CONCEPTS:
        restated, as_reported, concept_flags = _normalize_concept(
            concept,
            facts,
            cik=cik,
            submission_index=submission_index,
            fiscal_years=years,
        )
        if concept.metric_id == "diluted_shares":
            restated, discontinuities = _mark_share_basis_comparability(restated)
            as_reported, _ = _mark_share_basis_comparability(as_reported)
            concept_flags["share_basis_discontinuity"] = discontinuities
        for key, rows in concept_flags.items():
            coverage_flags.setdefault(key, []).extend(rows)
        missing = [year for year in years if year not in {obs.fiscal_year for obs in restated}]
        for year in missing:
            coverage_flags["missing_period"].append(
                {"metric_id": concept.metric_id, "fiscal_year": year}
            )
        coverage_status = (
            "complete"
            if not missing and restated
            else "partial"
            if restated
            else "missing"
        )
        restated_series.append(
            FundamentalSeries(
                metric_id=concept.metric_id,
                label=concept.label,
                definition=concept.definition,
                expected_unit=concept.unit_family,
                observations=tuple(restated),
                concept_priority=concept.aliases,
                coverage_status=coverage_status,
            )
        )
        as_reported_series.append(
            FundamentalSeries(
                metric_id=concept.metric_id,
                label=concept.label,
                definition=concept.definition,
                expected_unit=concept.unit_family,
                observations=tuple(as_reported),
                concept_priority=concept.aliases,
                coverage_status=coverage_status,
            )
        )
        for observation in restated:
            period_index.setdefault(
                observation.fiscal_year,
                {
                    "fiscal_year": observation.fiscal_year,
                    "fiscal_period": "FY",
                    "period_start": observation.period_start,
                    "period_end": observation.period_end,
                    "knowledge_at": observation.knowledge_at,
                },
            )

    annual_periods = tuple(
        period_index[year] for year in sorted(period_index) if year in set(years)
    )
    knowledge_candidates = [
        period["knowledge_at"] for period in annual_periods if period.get("knowledge_at")
    ]
    knowledge_at = max(knowledge_candidates) if knowledge_candidates else None

    if coverage_flags["restated_value"]:
        warnings.append(
            "Later-filed values differ from the first-known eligible 10-K fact for at "
            "least one fiscal period; the research series uses the latest restated value."
        )
    if coverage_flags["tag_substitution"]:
        warnings.append(
            "At least one observation used a lower-priority us-gaap concept alias."
        )
    if coverage_flags["acceptance_unresolved"]:
        warnings.append(
            "Some facts lack a submissions acceptance timestamp; filed date was used."
        )
    if coverage_flags["share_basis_discontinuity"]:
        warnings.append(
            "Diluted-share history contains a possible split or reporting-basis "
            "discontinuity; earlier per-share observations are excluded from "
            "cross-period comparisons."
        )
    if any(series.coverage_status != "complete" for series in restated_series):
        warnings.append("One or more requested fiscal years are missing for a reported series.")

    return NormalizationResult(
        ticker=ticker.upper(),
        cik=cik,
        company_name=company_name,
        template=TEMPLATE_ID,
        requested_years=requested_years,
        annual_periods=annual_periods,
        reported_series=tuple(restated_series),
        as_reported_series=tuple(as_reported_series),
        coverage={key: rows for key, rows in coverage_flags.items() if rows},
        warnings=tuple(warnings),
        knowledge_at=knowledge_at,
        provenance={
            "source": "sec.companyfacts",
            "taxonomy": TAXONOMY,
            "concept_registry": CONCEPT_REGISTRY_VERSION,
            "cik": f"{cik:010d}",
            "submissions_joined": bool(submission_index),
            "series_basis": "latest_restated",
            "period_grouping": "start_end",
            "fiscal_year_rule": "period_end_year",
        },
    )


def _normalize_concept(
    concept: ReportedConcept,
    facts: dict[str, Any],
    *,
    cik: int,
    submission_index: dict[str, SubmissionMeta],
    fiscal_years: tuple[int, ...],
) -> tuple[
    list[FundamentalObservation],
    list[FundamentalObservation],
    dict[str, list[dict[str, Any]]],
]:
    flags: dict[str, list[dict[str, Any]]] = {
        "duplicate_context": [],
        "restated_value": [],
        "tag_substitution": [],
        "unexpected_unit": [],
        "duration_outlier": [],
        "acceptance_unresolved": [],
    }
    candidates_by_period: dict[tuple[str | None, str], list[_FactCandidate]] = {}
    year_set = set(fiscal_years)

    for priority, alias in enumerate(concept.aliases):
        node = facts.get(alias)
        if not node:
            continue
        units = node.get("units", {})
        for unit_name, rows in units.items():
            family = _unit_family(unit_name)
            if family is None or family != concept.unit_family:
                for row in rows:
                    if _is_fy_form(str(row.get("form", ""))):
                        flags["unexpected_unit"].append(
                            {
                                "metric_id": concept.metric_id,
                                "concept": alias,
                                "unit": unit_name,
                                "document_fy": row.get("fy"),
                            }
                        )
                continue
            for row in rows:
                candidate = _candidate_from_row(
                    concept=concept,
                    alias=alias,
                    alias_priority=priority,
                    unit=family,
                    row=row,
                    cik=cik,
                    submission_index=submission_index,
                    flags=flags,
                )
                if candidate is None:
                    continue
                if candidate.fiscal_year not in year_set:
                    continue
                period_key = (candidate.start, candidate.end)
                candidates_by_period.setdefault(period_key, []).append(candidate)

    restated_observations: list[FundamentalObservation] = []
    as_reported_observations: list[FundamentalObservation] = []
    for period_key in sorted(candidates_by_period, key=lambda item: item[1]):
        group = candidates_by_period[period_key]
        restated, as_reported, period_flags = _select_period_series(
            concept.metric_id, group
        )
        for key, rows in period_flags.items():
            flags.setdefault(key, []).extend(rows)
        if restated is not None:
            restated_observations.append(
                _observation_from_candidate(concept.metric_id, restated)
            )
        if as_reported is not None:
            as_reported_observations.append(
                _observation_from_candidate(concept.metric_id, as_reported)
            )
    restated_observations.sort(key=lambda item: item.fiscal_year)
    as_reported_observations.sort(key=lambda item: item.fiscal_year)
    return restated_observations, as_reported_observations, flags


@dataclass(frozen=True)
class _FactCandidate:
    alias: str
    alias_priority: int
    unit: str
    value: float
    start: str | None
    end: str
    accession: str
    form: str
    filed: str
    document_fy: int | None
    document_fp: str | None
    accepted_at: str | None
    source_url: str
    knowledge_at: str
    quality_flags: tuple[str, ...]
    fiscal_year: int


def _candidate_from_row(
    *,
    concept: ReportedConcept,
    alias: str,
    alias_priority: int,
    unit: UnitFamily,
    row: dict[str, Any],
    cik: int,
    submission_index: dict[str, SubmissionMeta],
    flags: dict[str, list[dict[str, Any]]],
) -> _FactCandidate | None:
    form = str(row.get("form") or "")
    if not _is_fy_form(form):
        return None
    end = _as_date_str(row.get("end"))
    if not end:
        return None
    start = _as_date_str(row.get("start"))
    if concept.period_kind == "duration":
        if not start:
            return None
        duration = (_parse_date(end) - _parse_date(start)).days
        if duration < ANNUAL_DURATION_DAYS[0] or duration > ANNUAL_DURATION_DAYS[1]:
            flags["duration_outlier"].append(
                {
                    "metric_id": concept.metric_id,
                    "concept": alias,
                    "start": start,
                    "end": end,
                    "days": duration,
                }
            )
            return None
    else:
        # Instant facts are keyed only by the balance-sheet date.
        start = None

    accession = str(row.get("accn") or "")
    filed = _as_date_str(row.get("filed")) or ""
    document_fy = int(row["fy"]) if row.get("fy") is not None else None
    document_fp = str(row.get("fp")) if row.get("fp") is not None else None
    fiscal_year = fiscal_year_from_period_end(end)

    quality: list[str] = []
    if alias_priority > 0:
        quality.append("tag_substitution")
        flags["tag_substitution"].append(
            {
                "metric_id": concept.metric_id,
                "fiscal_year": fiscal_year,
                "concept": alias,
                "preferred": concept.aliases[0],
            }
        )

    meta = submission_index.get(accession)
    accepted_at = None
    if meta and meta.acceptance_datetime:
        accepted_at = _normalize_acceptance(meta.acceptance_datetime)
    if accepted_at is None:
        quality.append("acceptance_unresolved")
        flags["acceptance_unresolved"].append(
            {
                "metric_id": concept.metric_id,
                "fiscal_year": fiscal_year,
                "accession": accession,
            }
        )
        knowledge_at = filed
    else:
        knowledge_at = accepted_at

    primary_doc = meta.primary_document if meta else None
    source_url = _source_url(cik, accession, primary_doc)

    try:
        value = float(row["val"])
    except (KeyError, TypeError, ValueError):
        return None

    return _FactCandidate(
        alias=alias,
        alias_priority=alias_priority,
        unit=unit,
        value=value,
        start=start,
        end=end,
        accession=accession,
        form=form,
        filed=filed,
        document_fy=document_fy,
        document_fp=document_fp,
        accepted_at=accepted_at,
        source_url=source_url,
        knowledge_at=knowledge_at,
        quality_flags=tuple(quality),
        fiscal_year=fiscal_year,
    )


def fiscal_year_from_period_end(period_end: str) -> int:
    """Derive the displayed fiscal year from the issuer period end date."""
    return _parse_date(period_end).year


def _select_period_series(
    metric_id: str, candidates: list[_FactCandidate]
) -> tuple[_FactCandidate | None, _FactCandidate | None, dict[str, list[dict[str, Any]]]]:
    flags: dict[str, list[dict[str, Any]]] = {
        "duplicate_context": [],
        "restated_value": [],
    }
    if not candidates:
        return None, None, flags

    seen_keys: dict[tuple[str, str, str | None, str], list[_FactCandidate]] = {}
    for item in candidates:
        key = (item.accession, item.end, item.start, item.alias)
        seen_keys.setdefault(key, []).append(item)
    for key, group in seen_keys.items():
        if len(group) > 1:
            flags["duplicate_context"].append(
                {
                    "metric_id": metric_id,
                    "fiscal_year": group[0].fiscal_year,
                    "period_end": group[0].end,
                    "accession": key[0],
                    "count": len(group),
                }
            )

    as_reported = min(
        candidates,
        key=lambda item: (item.knowledge_at, item.filed, item.accession, item.alias_priority),
    )
    best_priority = min(item.alias_priority for item in candidates)
    pool = [item for item in candidates if item.alias_priority == best_priority]
    restated = max(pool, key=lambda item: (item.filed, item.accession, item.end))

    if restated.value != as_reported.value:
        flags["restated_value"].append(
            {
                "metric_id": metric_id,
                "fiscal_year": as_reported.fiscal_year,
                "period_end": as_reported.end,
                "original_value": as_reported.value,
                "later_value": restated.value,
                "later_accession": restated.accession,
                "later_filed": restated.filed,
            }
        )
        restated = _with_flag(restated, "restated_value")
        as_reported = _with_flag(as_reported, "restated_value")

    if flags["duplicate_context"]:
        restated = _with_flag(restated, "duplicate_context")
        as_reported = _with_flag(as_reported, "duplicate_context")
    return restated, as_reported, flags


def _mark_share_basis_comparability(
    observations: list[FundamentalObservation],
) -> tuple[list[FundamentalObservation], list[dict[str, Any]]]:
    """Mark older share observations that are not on the latest visible basis.

    Company Facts does not always carry split-restated comparatives far enough back
    for a ten-year window. A large adjacent jump is therefore treated as a basis
    boundary, not as dilution. Values on and after the last boundary remain usable;
    earlier values stay available for audit but are excluded from per-share trends.
    """
    ordered = sorted(observations, key=lambda item: item.fiscal_year)
    discontinuities: list[dict[str, Any]] = []
    boundary_years: list[int] = []
    low, high = SHARE_BASIS_RATIO_BOUNDS
    for prior, current in pairwise(ordered):
        if prior.value <= 0 or current.value <= 0:
            continue
        ratio = current.value / prior.value
        if low <= ratio <= high:
            continue
        boundary_years.append(current.fiscal_year)
        discontinuities.append(
            {
                "metric_id": "diluted_shares",
                "prior_fiscal_year": prior.fiscal_year,
                "fiscal_year": current.fiscal_year,
                "prior_value": prior.value,
                "value": current.value,
                "ratio": ratio,
            }
        )
    if not boundary_years:
        return ordered, discontinuities

    latest_boundary = max(boundary_years)
    marked: list[FundamentalObservation] = []
    for observation in ordered:
        flags = list(observation.quality_flags)
        if observation.fiscal_year < latest_boundary:
            flags.append("share_basis_noncomparable")
        if observation.fiscal_year in boundary_years:
            flags.append("share_basis_discontinuity")
        marked.append(replace(observation, quality_flags=tuple(dict.fromkeys(flags))))
    return marked, discontinuities


def _with_flag(candidate: _FactCandidate, flag: str) -> _FactCandidate:
    if flag in candidate.quality_flags:
        return candidate
    return _FactCandidate(
        alias=candidate.alias,
        alias_priority=candidate.alias_priority,
        unit=candidate.unit,
        value=candidate.value,
        start=candidate.start,
        end=candidate.end,
        accession=candidate.accession,
        form=candidate.form,
        filed=candidate.filed,
        document_fy=candidate.document_fy,
        document_fp=candidate.document_fp,
        accepted_at=candidate.accepted_at,
        source_url=candidate.source_url,
        knowledge_at=candidate.knowledge_at,
        quality_flags=(*candidate.quality_flags, flag),
        fiscal_year=candidate.fiscal_year,
    )


def _observation_from_candidate(
    metric_id: str, candidate: _FactCandidate
) -> FundamentalObservation:
    citation_id = (
        f"{TAXONOMY}:{candidate.alias}:{candidate.fiscal_year}:{candidate.accession}"
    )
    citation = FundamentalCitation(
        citation_id=citation_id,
        taxonomy=TAXONOMY,
        concept=candidate.alias,
        accession=candidate.accession,
        form=candidate.form,
        source_url=candidate.source_url,
        period_start=candidate.start,
        period_end=candidate.end,
        filed_date=candidate.filed,
        accepted_at=candidate.accepted_at,
        fiscal_year=candidate.fiscal_year,
        fiscal_period="FY",
        unit=candidate.unit,
        document_fy=candidate.document_fy,
        document_fp=candidate.document_fp,
    )
    return FundamentalObservation(
        metric_id=metric_id,
        value=candidate.value,
        unit=candidate.unit,
        period_start=candidate.start,
        period_end=candidate.end,
        fiscal_year=candidate.fiscal_year,
        knowledge_at=candidate.knowledge_at,
        citation=citation,
        quality_flags=candidate.quality_flags,
    )


def _submission_index(payload: dict[str, Any]) -> dict[str, SubmissionMeta]:
    blocks = [payload.get("filings", {}).get("recent", {})]
    for shard in payload.get("_shards", []):
        if "filings" in shard:
            blocks.append(shard["filings"].get("recent", {}))
        else:
            blocks.append(shard)
    index: dict[str, SubmissionMeta] = {}
    for block in blocks:
        if not block:
            continue
        accessions = block.get("accessionNumber") or []
        forms = block.get("form") or []
        filing_dates = block.get("filingDate") or []
        report_dates = block.get("reportDate") or []
        acceptances = block.get("acceptanceDateTime") or []
        documents = block.get("primaryDocument") or []
        for i, accession in enumerate(accessions):
            index[str(accession)] = SubmissionMeta(
                accession=str(accession),
                form=str(forms[i] if i < len(forms) else ""),
                filing_date=str(filing_dates[i] if i < len(filing_dates) else ""),
                report_date=str(report_dates[i] if i < len(report_dates) else ""),
                acceptance_datetime=acceptances[i] if i < len(acceptances) else None,
                primary_document=documents[i] if i < len(documents) else None,
            )
    return index


def _source_url(cik: int, accession: str, primary_document: str | None) -> str:
    nodash = accession.replace("-", "")
    if primary_document:
        return (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{nodash}/{primary_document}"
        )
    if accession:
        return (
            "https://www.sec.gov/cgi-bin/viewer?action=view"
            f"&cik={cik}&accession_number={accession}&xbrl_type=v"
        )
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/"


def _default_fiscal_years(facts: dict[str, Any], requested_years: int) -> tuple[int, ...]:
    years: set[int] = set()
    for node in facts.values():
        for rows in node.get("units", {}).values():
            for row in rows:
                if not _is_fy_form(str(row.get("form", ""))):
                    continue
                end = _as_date_str(row.get("end"))
                if not end:
                    continue
                start = _as_date_str(row.get("start"))
                if start:
                    duration = (_parse_date(end) - _parse_date(start)).days
                    if duration < ANNUAL_DURATION_DAYS[0] or duration > ANNUAL_DURATION_DAYS[1]:
                        continue
                years.add(fiscal_year_from_period_end(end))
    if not years:
        return ()
    ordered = sorted(years)
    return tuple(ordered[-requested_years:])


def _is_fy_form(form: str) -> bool:
    return form.startswith("10-K")


def _unit_family(unit_name: str) -> UnitFamily | None:
    normalized = unit_name.strip()
    if normalized in {"USD", "usd"}:
        return "USD"
    if normalized.lower() == "shares":
        return "shares"
    return None


def _as_date_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value)[:10]
    _parse_date(text)
    return text


def _parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _normalize_acceptance(value: str) -> str:
    from filing_triage.ingest.edgar import ACCEPTANCE_TZ

    raw = value.replace("Z", "")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ACCEPTANCE_TZ).isoformat()
    return parsed.isoformat()
