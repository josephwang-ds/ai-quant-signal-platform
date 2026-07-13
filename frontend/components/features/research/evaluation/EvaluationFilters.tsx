import type {
  EvaluationFilters,
  EvaluationDimensionStatusFilter,
} from "@/types/evaluation";
import { EVALUATION_DIMENSION_STATUSES } from "@/types/evaluation";

export type EvaluationFiltersLabels = {
  search: string;
  searchPlaceholder: string;
  status: string;
  all: string;
};

type EvaluationFiltersBarProps = {
  filters: EvaluationFilters;
  labels: EvaluationFiltersLabels;
  onChange: (filters: EvaluationFilters) => void;
  disabled?: boolean;
};

export default function EvaluationFiltersBar({
  filters,
  labels,
  onChange,
  disabled = false,
}: EvaluationFiltersBarProps) {
  return (
    <div className="evaluation-filters" role="search">
      <div className="form-field evaluation-filters__search">
        <label className="form-label" htmlFor="evaluation-search">
          {labels.search}
        </label>
        <input
          id="evaluation-search"
          className="form-input"
          type="search"
          value={filters.query}
          disabled={disabled}
          placeholder={labels.searchPlaceholder}
          onChange={(event) =>
            onChange({ ...filters, query: event.target.value })
          }
        />
      </div>
      <div className="form-field">
        <label className="form-label" htmlFor="evaluation-status">
          {labels.status}
        </label>
        <select
          id="evaluation-status"
          className="form-select"
          value={filters.status}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              status: event.target.value as EvaluationDimensionStatusFilter,
            })
          }
        >
          <option value="all">{labels.all}</option>
          {EVALUATION_DIMENSION_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
