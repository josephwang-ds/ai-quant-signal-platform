"use client";

import { useEffect, useId, useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import type { CreateResearchInput } from "@/lib/researchRepository";
import type { FactorId, ResearchTemplateId } from "@/types/research";

export type NewResearchModalLabels = {
  title: string;
  localNote: string;
  name: string;
  question: string;
  hypothesis: string;
  tags: string;
  tagsHint: string;
  template: string;
  templateTrend: string;
  templateFactor: string;
  templateTrendHint: string;
  templateFactorHint: string;
  stepDefine: string;
  stepDefineHint: string;
  stepConfigure: string;
  stepConfigureHint: string;
  next: string;
  back: string;
  close: string;
  useExample: string;
  exampleApplied: string;
  namePlaceholder: string;
  questionPlaceholderTrend: string;
  questionPlaceholderFactor: string;
  hypothesisPlaceholderTrend: string;
  hypothesisPlaceholderFactor: string;
  executionTitle: string;
  executionHint: string;
  factorDefinitionTitle: string;
  factorDefinitionHint: string;
  symbol: string;
  benchmark: string;
  startDate: string;
  endDate: string;
  shortWindow: string;
  longWindow: string;
  transactionCost: string;
  universe: string;
  factor: string;
  factorMomentum: string;
  factorLowVol: string;
  factorValue: string;
  factorValueComingSoon: string;
  rebalance: string;
  holdingPeriod: string;
  create: string;
  cancel: string;
  errorName: string;
  errorQuestion: string;
  errorHypothesis: string;
  errorSymbol: string;
  errorShortWindow: string;
  errorLongWindow: string;
  errorDateRange: string;
  errorTransactionCost: string;
  errorHoldingPeriod: string;
  errorFactorValue: string;
};

export type NewResearchModalProps = {
  open: boolean;
  labels: NewResearchModalLabels;
  busy?: boolean;
  onClose: () => void;
  onCreate: (input: CreateResearchInput) => void | Promise<void>;
};

function makeDefaultForm() {
  return {
    templateId: "trend_following" as ResearchTemplateId,
    name: "",
    researchQuestion: "",
    hypothesis: "",
    tags: "",
    symbol: "SPY",
    benchmark: "SPY",
    startDate: "2018-01-01",
    endDate: "",
    shortWindow: "20",
    longWindow: "60",
    transactionCost: "0.001",
    universeId: "us_sector_etfs",
    factorId: "momentum" as FactorId,
    rebalanceFrequency: "monthly",
    holdingPeriodMonths: "1",
  };
}

type FormState = ReturnType<typeof makeDefaultForm>;

/** Two-step research setup: define the idea first, then review executable defaults. */
export default function NewResearchModal({
  open,
  labels,
  busy = false,
  onClose,
  onCreate,
}: NewResearchModalProps) {
  const titleId = useId();
  const descriptionId = useId();
  const [form, setForm] = useState(makeDefaultForm);
  const [step, setStep] = useState<1 | 2>(1);
  const [error, setError] = useState<string | null>(null);
  const [exampleApplied, setExampleApplied] = useState(false);

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [busy, onClose, open]);

  if (!open) return null;

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((previous) => ({ ...previous, [key]: value }));
    setError(null);
    setExampleApplied(false);
  }

  function selectTemplate(templateId: ResearchTemplateId) {
    setForm((previous) => ({ ...previous, templateId }));
    setError(null);
    setExampleApplied(false);
  }

  function validateDefinition(): boolean {
    if (!form.name.trim()) {
      setError(labels.errorName);
      return false;
    }
    if (!form.researchQuestion.trim()) {
      setError(labels.errorQuestion);
      return false;
    }
    if (!form.hypothesis.trim()) {
      setError(labels.errorHypothesis);
      return false;
    }
    setError(null);
    return true;
  }

  function applyExample() {
    const isFactor = form.templateId === "cross_sectional_factor";
    setForm((previous) => ({
      ...previous,
      name: isFactor
        ? labels.templateFactor
        : `${previous.symbol || "SPY"} ${labels.templateTrend}`,
      researchQuestion: isFactor
        ? labels.questionPlaceholderFactor
        : labels.questionPlaceholderTrend,
      hypothesis: isFactor
        ? labels.hypothesisPlaceholderFactor
        : labels.hypothesisPlaceholderTrend,
      tags: isFactor ? "factor, cross-sectional" : "trend, moving-average",
    }));
    setExampleApplied(true);
    setError(null);
  }

  function goToConfiguration() {
    if (!validateDefinition()) return;
    setStep(2);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (step === 1) {
      goToConfiguration();
      return;
    }
    if (!validateDefinition()) {
      setStep(1);
      return;
    }

    const transactionCost = Number(form.transactionCost);
    if (!Number.isFinite(transactionCost) || transactionCost < 0) {
      return setError(labels.errorTransactionCost);
    }
    if (form.endDate && form.startDate >= form.endDate) {
      return setError(labels.errorDateRange);
    }

    if (form.templateId === "cross_sectional_factor") {
      if (form.factorId === "value") return setError(labels.errorFactorValue);
      const holdingPeriodMonths = Number(form.holdingPeriodMonths);
      if (
        !Number.isInteger(holdingPeriodMonths) ||
        holdingPeriodMonths < 1 ||
        holdingPeriodMonths > 12
      ) {
        return setError(labels.errorHoldingPeriod);
      }
      setError(null);
      await onCreate({
        name: form.name.trim(),
        researchQuestion: form.researchQuestion.trim(),
        hypothesis: form.hypothesis.trim(),
        tags: [
          ...form.tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
          "cross-sectional-factor",
        ],
        runConfiguration: {
          templateId: "cross_sectional_factor",
          universeId: form.universeId,
          factorId: form.factorId,
          rebalanceFrequency: "monthly",
          holdingPeriodMonths,
          startDate: form.startDate,
          endDate: form.endDate || null,
          transactionCost,
        },
      });
      setForm(makeDefaultForm());
      setStep(1);
      return;
    }

    if (!form.symbol.trim()) return setError(labels.errorSymbol);
    const shortWindow = Number(form.shortWindow);
    const longWindow = Number(form.longWindow);
    if (!Number.isInteger(shortWindow) || shortWindow <= 0) {
      return setError(labels.errorShortWindow);
    }
    if (!Number.isInteger(longWindow) || longWindow <= shortWindow) {
      return setError(labels.errorLongWindow);
    }

    setError(null);
    await onCreate({
      name: form.name.trim(),
      researchQuestion: form.researchQuestion.trim(),
      hypothesis: form.hypothesis.trim(),
      tags: form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      runConfiguration: {
        templateId: "trend_following",
        symbol: form.symbol.trim().toUpperCase(),
        benchmark: (form.benchmark.trim() || form.symbol.trim()).toUpperCase(),
        startDate: form.startDate,
        endDate: form.endDate || null,
        shortWindow,
        longWindow,
        transactionCost,
        riskFreeRate: 0,
      },
    });
    setForm(makeDefaultForm());
    setStep(1);
  }

  const isFactor = form.templateId === "cross_sectional_factor";
  const questionPlaceholder = isFactor
    ? labels.questionPlaceholderFactor
    : labels.questionPlaceholderTrend;
  const hypothesisPlaceholder = isFactor
    ? labels.hypothesisPlaceholderFactor
    : labels.hypothesisPlaceholderTrend;

  return (
    <div
      className="research-modal"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <div
        className="research-modal__panel research-modal__panel--guided"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <header className="research-modal__header">
          <div>
            <p className="research-modal__eyebrow">
              {step === 1 ? labels.stepDefine : labels.stepConfigure}
            </p>
            <h2 id={titleId} className="research-modal__title">
              {labels.title}
            </h2>
            <p id={descriptionId} className="section-meta">
              {step === 1 ? labels.stepDefineHint : labels.stepConfigureHint}
            </p>
          </div>
          <button
            type="button"
            className="research-modal__close"
            aria-label={labels.close}
            onClick={onClose}
            disabled={busy}
          >
            ×
          </button>
        </header>

        <ol className="research-modal__steps" aria-label={labels.title}>
          <li className={step === 1 ? "is-active" : "is-complete"}>
            <span>1</span>
            {labels.stepDefine}
          </li>
          <li className={step === 2 ? "is-active" : ""}>
            <span>2</span>
            {labels.stepConfigure}
          </li>
        </ol>

        <form
          className="research-modal__form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          {step === 1 ? (
            <div className="research-modal__step-content">
              <fieldset className="research-modal__template-picker">
                <legend>{labels.template} *</legend>
                <div className="research-modal__template-options">
                  <button
                    type="button"
                    className={`research-modal__template-option${
                      !isFactor ? " is-selected" : ""
                    }`}
                    aria-pressed={!isFactor}
                    onClick={() => selectTemplate("trend_following")}
                    disabled={busy}
                  >
                    <strong>{labels.templateTrend}</strong>
                    <span>{labels.templateTrendHint}</span>
                  </button>
                  <button
                    type="button"
                    className={`research-modal__template-option${
                      isFactor ? " is-selected" : ""
                    }`}
                    aria-pressed={isFactor}
                    onClick={() => selectTemplate("cross_sectional_factor")}
                    disabled={busy}
                  >
                    <strong>{labels.templateFactor}</strong>
                    <span>{labels.templateFactorHint}</span>
                  </button>
                </div>
              </fieldset>

              <div className="research-modal__example-bar">
                <p>{exampleApplied ? labels.exampleApplied : questionPlaceholder}</p>
                <Button type="button" onClick={applyExample} disabled={busy}>
                  {labels.useExample}
                </Button>
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="new-research-name">
                  {labels.name} *
                </label>
                <input
                  id="new-research-name"
                  className="form-input"
                  value={form.name}
                  placeholder={labels.namePlaceholder}
                  onChange={(event) => updateField("name", event.target.value)}
                  required
                  autoFocus
                  disabled={busy}
                />
                <p className="form-hint">{labels.namePlaceholder}</p>
              </div>

              <div className="research-modal__row">
                <div className="form-field">
                  <label className="form-label" htmlFor="new-research-question">
                    {labels.question} *
                  </label>
                  <textarea
                    id="new-research-question"
                    className="form-input"
                    rows={4}
                    value={form.researchQuestion}
                    placeholder={questionPlaceholder}
                    onChange={(event) =>
                      updateField("researchQuestion", event.target.value)
                    }
                    required
                    disabled={busy}
                  />
                  <p className="form-hint">{questionPlaceholder}</p>
                </div>

                <div className="form-field">
                  <label className="form-label" htmlFor="new-research-hypothesis">
                    {labels.hypothesis} *
                  </label>
                  <textarea
                    id="new-research-hypothesis"
                    className="form-input"
                    rows={4}
                    value={form.hypothesis}
                    placeholder={hypothesisPlaceholder}
                    onChange={(event) =>
                      updateField("hypothesis", event.target.value)
                    }
                    required
                    disabled={busy}
                  />
                  <p className="form-hint">{hypothesisPlaceholder}</p>
                </div>
              </div>

              <div className="form-field research-modal__tags">
                <label className="form-label" htmlFor="new-research-tags">
                  {labels.tags}
                </label>
                <input
                  id="new-research-tags"
                  className="form-input"
                  value={form.tags}
                  placeholder={isFactor ? "factor, momentum" : "trend, SPY"}
                  onChange={(event) => updateField("tags", event.target.value)}
                  disabled={busy}
                />
                <p className="form-hint">{labels.tagsHint}</p>
              </div>
            </div>
          ) : (
            <div className="research-modal__step-content">
              <div className="research-modal__definition-summary">
                <div>
                  <span>{labels.name}</span>
                  <strong>{form.name}</strong>
                </div>
                <div>
                  <span>{labels.question}</span>
                  <p>{form.researchQuestion}</p>
                </div>
                <button type="button" onClick={() => setStep(1)}>
                  {labels.back}
                </button>
              </div>

              {isFactor ? (
                <fieldset className="research-modal__fieldset">
                  <legend>{labels.factorDefinitionTitle}</legend>
                  <p className="section-meta">{labels.factorDefinitionHint}</p>
                  <div className="research-modal__row">
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-universe">
                        {labels.universe} *
                      </label>
                      <select
                        id="new-research-universe"
                        className="form-input"
                        value={form.universeId}
                        onChange={(event) =>
                          updateField("universeId", event.target.value)
                        }
                        disabled={busy}
                      >
                        <option value="us_sector_etfs">US sector ETFs</option>
                      </select>
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-factor">
                        {labels.factor} *
                      </label>
                      <select
                        id="new-research-factor"
                        className="form-input"
                        value={form.factorId}
                        onChange={(event) =>
                          updateField("factorId", event.target.value as FactorId)
                        }
                        disabled={busy}
                      >
                        <option value="momentum">{labels.factorMomentum}</option>
                        <option value="low_volatility">{labels.factorLowVol}</option>
                        <option value="value" disabled>
                          {labels.factorValue} ({labels.factorValueComingSoon})
                        </option>
                      </select>
                    </div>
                  </div>
                  <div className="research-modal__row research-modal__row--three">
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-rebalance">
                        {labels.rebalance}
                      </label>
                      <input
                        id="new-research-rebalance"
                        className="form-input"
                        value={labels.rebalance}
                        disabled
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-holding">
                        {labels.holdingPeriod} *
                      </label>
                      <input
                        id="new-research-holding"
                        className="form-input"
                        type="number"
                        min="1"
                        max="12"
                        step="1"
                        value={form.holdingPeriodMonths}
                        onChange={(event) =>
                          updateField("holdingPeriodMonths", event.target.value)
                        }
                        disabled={busy}
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-cost">
                        {labels.transactionCost}
                      </label>
                      <input
                        id="new-research-cost"
                        className="form-input"
                        type="number"
                        min="0"
                        step="0.0001"
                        value={form.transactionCost}
                        onChange={(event) =>
                          updateField("transactionCost", event.target.value)
                        }
                        disabled={busy}
                      />
                    </div>
                  </div>
                  <DateFields form={form} labels={labels} busy={busy} updateField={updateField} />
                </fieldset>
              ) : (
                <fieldset className="research-modal__fieldset">
                  <legend>{labels.executionTitle}</legend>
                  <p className="section-meta">{labels.executionHint}</p>
                  <div className="research-modal__row">
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-symbol">
                        {labels.symbol} *
                      </label>
                      <input
                        id="new-research-symbol"
                        className="form-input"
                        value={form.symbol}
                        onChange={(event) =>
                          updateField("symbol", event.target.value)
                        }
                        required
                        disabled={busy}
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-benchmark">
                        {labels.benchmark}
                      </label>
                      <input
                        id="new-research-benchmark"
                        className="form-input"
                        value={form.benchmark}
                        onChange={(event) =>
                          updateField("benchmark", event.target.value)
                        }
                        disabled={busy}
                      />
                    </div>
                  </div>
                  <DateFields form={form} labels={labels} busy={busy} updateField={updateField} />
                  <div className="research-modal__row research-modal__row--three">
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-short-window">
                        {labels.shortWindow} *
                      </label>
                      <input
                        id="new-research-short-window"
                        className="form-input"
                        type="number"
                        min="1"
                        step="1"
                        value={form.shortWindow}
                        onChange={(event) =>
                          updateField("shortWindow", event.target.value)
                        }
                        disabled={busy}
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-long-window">
                        {labels.longWindow} *
                      </label>
                      <input
                        id="new-research-long-window"
                        className="form-input"
                        type="number"
                        min="2"
                        step="1"
                        value={form.longWindow}
                        onChange={(event) =>
                          updateField("longWindow", event.target.value)
                        }
                        disabled={busy}
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="new-research-cost">
                        {labels.transactionCost}
                      </label>
                      <input
                        id="new-research-cost"
                        className="form-input"
                        type="number"
                        min="0"
                        step="0.0001"
                        value={form.transactionCost}
                        onChange={(event) =>
                          updateField("transactionCost", event.target.value)
                        }
                        disabled={busy}
                      />
                    </div>
                  </div>
                </fieldset>
              )}
            </div>
          )}

          {error ? (
            <p className="research-modal__error" role="alert">
              {error}
            </p>
          ) : null}

          <div className="research-modal__actions">
            {step === 1 ? (
              <>
                <Button type="button" onClick={onClose} disabled={busy}>
                  {labels.cancel}
                </Button>
                <Button type="submit" primary disabled={busy}>
                  {labels.next}
                </Button>
              </>
            ) : (
              <>
                <Button type="button" onClick={() => setStep(1)} disabled={busy}>
                  {labels.back}
                </Button>
                <Button type="submit" primary disabled={busy}>
                  {labels.create}
                </Button>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

function DateFields({
  form,
  labels,
  busy,
  updateField,
}: {
  form: FormState;
  labels: NewResearchModalLabels;
  busy: boolean;
  updateField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
}) {
  return (
    <div className="research-modal__row">
      <div className="form-field">
        <label className="form-label" htmlFor="new-research-start-date">
          {labels.startDate} *
        </label>
        <input
          id="new-research-start-date"
          className="form-input"
          type="date"
          value={form.startDate}
          onChange={(event) => updateField("startDate", event.target.value)}
          required
          disabled={busy}
        />
      </div>
      <div className="form-field">
        <label className="form-label" htmlFor="new-research-end-date">
          {labels.endDate}
        </label>
        <input
          id="new-research-end-date"
          className="form-input"
          type="date"
          value={form.endDate}
          onChange={(event) => updateField("endDate", event.target.value)}
          disabled={busy}
        />
      </div>
    </div>
  );
}
