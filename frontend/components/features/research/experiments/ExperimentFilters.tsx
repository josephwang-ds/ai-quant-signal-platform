import type {
  ExperimentFilters,
  ExperimentStatusFilter,
  ExperimentTypeFilter,
} from "@/types/experiment";
import { EXPERIMENT_STATUSES, EXPERIMENT_TYPES } from "@/types/experiment";

export type ExperimentFiltersLabels = {
  search: string;
  searchPlaceholder: string;
  status: string;
  type: string;
  sort: string;
  all: string;
  sortUpdated: string;
  sortCreated: string;
  sortResult: string;
};

type ExperimentFiltersBarProps = {
  filters: ExperimentFilters;
  labels: ExperimentFiltersLabels;
  onChange: (filters: ExperimentFilters) => void;
  disabled?: boolean;
};

export default function ExperimentFiltersBar({
  filters,
  labels,
  onChange,
  disabled = false,
}: ExperimentFiltersBarProps) {
  return (
    <div className="experiment-filters" role="search">
      <div className="form-field experiment-filters__search">
        <label className="form-label" htmlFor="experiment-search">
          {labels.search}
        </label>
        <input
          id="experiment-search"
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
        <label className="form-label" htmlFor="experiment-status">
          {labels.status}
        </label>
        <select
          id="experiment-status"
          className="form-select"
          value={filters.status}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              status: event.target.value as ExperimentStatusFilter,
            })
          }
        >
          <option value="all">{labels.all}</option>
          {EXPERIMENT_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label className="form-label" htmlFor="experiment-type">
          {labels.type}
        </label>
        <select
          id="experiment-type"
          className="form-select"
          value={filters.experimentType}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              experimentType: event.target.value as ExperimentTypeFilter,
            })
          }
        >
          <option value="all">{labels.all}</option>
          {EXPERIMENT_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label className="form-label" htmlFor="experiment-sort">
          {labels.sort}
        </label>
        <select
          id="experiment-sort"
          className="form-select"
          value={filters.sort}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              sort: event.target.value as ExperimentFilters["sort"],
            })
          }
        >
          <option value="updated">{labels.sortUpdated}</option>
          <option value="created">{labels.sortCreated}</option>
          <option value="result">{labels.sortResult}</option>
        </select>
      </div>
    </div>
  );
}
