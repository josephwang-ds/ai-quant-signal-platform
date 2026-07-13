"use client";

import Button from "@/components/ui/Button";
import type { ExperimentComposerValues, ExperimentType } from "@/types/experiment";
import { EXPERIMENT_TYPES } from "@/types/experiment";
import type { ExperimentComposerErrors } from "@/lib/researchExperiments";

export type ExperimentComposerLabels = {
  title: string;
  name: string;
  hypothesis: string;
  experimentType: string;
  dataset: string;
  startDate: string;
  endDate: string;
  benchmark: string;
  parameters: string;
  parametersHint: string;
  successCriteria: string;
  falsification: string;
  notes: string;
  save: string;
  cancel: string;
};

type ExperimentComposerProps = {
  open: boolean;
  values: ExperimentComposerValues;
  errors: ExperimentComposerErrors;
  labels: ExperimentComposerLabels;
  onChange: (values: ExperimentComposerValues) => void;
  onSave: () => void;
  onCancel: () => void;
};

export default function ExperimentComposer({
  open,
  values,
  errors,
  labels,
  onChange,
  onSave,
  onCancel,
}: ExperimentComposerProps) {
  if (!open) {
    return null;
  }

  return (
    <section
      className="experiment-composer"
      aria-label={labels.title}
      role="region"
    >
      <h3 className="experiment-composer__title">{labels.title}</h3>

      <div className="experiment-composer__grid">
        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-name">
            {labels.name}
          </label>
          <input
            id="exp-name"
            className={`form-input${errors.name ? " is-invalid" : ""}`}
            value={values.name}
            onChange={(event) =>
              onChange({ ...values, name: event.target.value })
            }
          />
          {errors.name ? (
            <p className="form-error" role="alert">
              {errors.name}
            </p>
          ) : null}
        </div>

        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-hypothesis">
            {labels.hypothesis}
          </label>
          <textarea
            id="exp-hypothesis"
            className={`form-input${errors.hypothesis ? " is-invalid" : ""}`}
            rows={3}
            value={values.hypothesis}
            onChange={(event) =>
              onChange({ ...values, hypothesis: event.target.value })
            }
          />
          {errors.hypothesis ? (
            <p className="form-error" role="alert">
              {errors.hypothesis}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="exp-type">
            {labels.experimentType}
          </label>
          <select
            id="exp-type"
            className={`form-select${errors.experimentType ? " is-invalid" : ""}`}
            value={values.experimentType}
            onChange={(event) =>
              onChange({
                ...values,
                experimentType: event.target.value as ExperimentType | "",
              })
            }
          >
            <option value="">—</option>
            {EXPERIMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          {errors.experimentType ? (
            <p className="form-error" role="alert">
              {errors.experimentType}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="exp-dataset">
            {labels.dataset}
          </label>
          <input
            id="exp-dataset"
            className={`form-input${errors.datasetOrSymbol ? " is-invalid" : ""}`}
            value={values.datasetOrSymbol}
            onChange={(event) =>
              onChange({ ...values, datasetOrSymbol: event.target.value })
            }
          />
          {errors.datasetOrSymbol ? (
            <p className="form-error" role="alert">
              {errors.datasetOrSymbol}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="exp-start">
            {labels.startDate}
          </label>
          <input
            id="exp-start"
            type="date"
            className={`form-input${
              errors.startDate || errors.dateRange ? " is-invalid" : ""
            }`}
            value={values.startDate}
            onChange={(event) =>
              onChange({ ...values, startDate: event.target.value })
            }
          />
          {errors.startDate ? (
            <p className="form-error" role="alert">
              {errors.startDate}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="exp-end">
            {labels.endDate}
          </label>
          <input
            id="exp-end"
            type="date"
            className={`form-input${
              errors.endDate || errors.dateRange ? " is-invalid" : ""
            }`}
            value={values.endDate}
            onChange={(event) =>
              onChange({ ...values, endDate: event.target.value })
            }
          />
          {errors.endDate ? (
            <p className="form-error" role="alert">
              {errors.endDate}
            </p>
          ) : null}
          {errors.dateRange ? (
            <p className="form-error" role="alert">
              {errors.dateRange}
            </p>
          ) : null}
        </div>

        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-benchmark">
            {labels.benchmark}
          </label>
          <input
            id="exp-benchmark"
            className="form-input"
            value={values.benchmark}
            onChange={(event) =>
              onChange({ ...values, benchmark: event.target.value })
            }
          />
        </div>

        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-params">
            {labels.parameters}
          </label>
          <textarea
            id="exp-params"
            className="form-input"
            rows={3}
            value={values.parameters}
            onChange={(event) =>
              onChange({ ...values, parameters: event.target.value })
            }
          />
          <p className="form-hint">{labels.parametersHint}</p>
        </div>

        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-success">
            {labels.successCriteria}
          </label>
          <textarea
            id="exp-success"
            className={`form-input${errors.successCriteria ? " is-invalid" : ""}`}
            rows={2}
            value={values.successCriteria}
            onChange={(event) =>
              onChange({ ...values, successCriteria: event.target.value })
            }
          />
          {errors.successCriteria ? (
            <p className="form-error" role="alert">
              {errors.successCriteria}
            </p>
          ) : null}
        </div>

        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-falsify">
            {labels.falsification}
          </label>
          <textarea
            id="exp-falsify"
            className={`form-input${
              errors.falsificationCondition ? " is-invalid" : ""
            }`}
            rows={2}
            value={values.falsificationCondition}
            onChange={(event) =>
              onChange({
                ...values,
                falsificationCondition: event.target.value,
              })
            }
          />
          {errors.falsificationCondition ? (
            <p className="form-error" role="alert">
              {errors.falsificationCondition}
            </p>
          ) : null}
        </div>

        <div className="form-field experiment-composer__span-2">
          <label className="form-label" htmlFor="exp-notes">
            {labels.notes}
          </label>
          <textarea
            id="exp-notes"
            className="form-input"
            rows={2}
            value={values.notes}
            onChange={(event) =>
              onChange({ ...values, notes: event.target.value })
            }
          />
        </div>
      </div>

      <div className="experiment-composer__actions">
        <Button primary onClick={onSave}>
          {labels.save}
        </Button>
        <Button className="btn--ghost" onClick={onCancel}>
          {labels.cancel}
        </Button>
      </div>
    </section>
  );
}
