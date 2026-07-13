import type { NotebookFilters, NotebookTypeFilter } from "@/types/notebook";
import { NOTEBOOK_ENTRY_TYPES } from "@/types/notebook";

export type NotebookFiltersLabels = {
  filterType: string;
  filterAll: string;
  sort: string;
  sortNewest: string;
  sortOldest: string;
};

type NotebookFiltersProps = {
  filters: NotebookFilters;
  labels: NotebookFiltersLabels;
  onChange: (filters: NotebookFilters) => void;
  disabled?: boolean;
};

export default function NotebookFiltersBar({
  filters,
  labels,
  onChange,
  disabled = false,
}: NotebookFiltersProps) {
  return (
    <div className="notebook-filters" role="search">
      <div className="form-field">
        <label className="form-label" htmlFor="notebook-type-filter">
          {labels.filterType}
        </label>
        <select
          id="notebook-type-filter"
          className="form-select"
          value={filters.type}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              type: event.target.value as NotebookTypeFilter,
            })
          }
        >
          <option value="all">{labels.filterAll}</option>
          {NOTEBOOK_ENTRY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label className="form-label" htmlFor="notebook-sort">
          {labels.sort}
        </label>
        <select
          id="notebook-sort"
          className="form-select"
          value={filters.sort}
          disabled={disabled}
          onChange={(event) =>
            onChange({
              ...filters,
              sort: event.target.value as NotebookFilters["sort"],
            })
          }
        >
          <option value="newest">{labels.sortNewest}</option>
          <option value="oldest">{labels.sortOldest}</option>
        </select>
      </div>
    </div>
  );
}
