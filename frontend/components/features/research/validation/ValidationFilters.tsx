import type {
  ValidationFilters,
  ValidationStatusFilter,
} from "@/types/validation";
import { VALIDATION_STATUSES } from "@/types/validation";

export type ValidationFiltersLabels = {
  search: string;
  searchPlaceholder: string;
  status: string;
  all: string;
};

type ValidationFiltersBarProps = {
  filters: ValidationFilters;
  labels: ValidationFiltersLabels;
  onChange: (filters: ValidationFilters) => void;
  disabled?: boolean;
};

export default function ValidationFiltersBar({
  filters,
  labels,
  onChange,
  disabled = false,
}: ValidationFiltersBarProps) {
  return (
    <div className="validation-filters" role="search">
      <div className="form-field validation-filters__search">
        <label className="form-label" htmlFor="validation-search">
          {labels.search}
        </label>
        <input
          id="validation-search"
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
        <label className="form-label" htmlFor="validation-status">
          {labels.status}
        </label>
        <select
          id="validation-status"
          className="form-select"
          value={filters.status}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              status: event.target.value as ValidationStatusFilter,
            })
          }
        >
          <option value="all">{labels.all}</option>
          {VALIDATION_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
