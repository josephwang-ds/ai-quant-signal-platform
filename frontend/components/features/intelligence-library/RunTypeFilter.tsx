"use client";

import type { Language } from "@/lib/i18n";
import { formatRunType } from "@/lib/intelligence/display";
import type { ResearchRunType } from "@/lib/intelligence/types";

export type RunTypeFilterProps = {
  language: Language;
  value: ResearchRunType | "all";
  options: ResearchRunType[];
  onChange: (value: ResearchRunType | "all") => void;
};

export default function RunTypeFilter({
  language,
  value,
  options,
  onChange,
}: RunTypeFilterProps) {
  if (options.length <= 1) {
    return null;
  }

  const zh = language === "zh";
  const labelId = "published-run-type-filter-label";

  return (
    <div className="research-library__filter" data-testid="run-type-filter">
      <label id={labelId} htmlFor="published-run-type-filter">
        {zh ? "研究类型" : "Run type"}
      </label>
      <select
        id="published-run-type-filter"
        aria-labelledby={labelId}
        value={value}
        onChange={(event) => {
          const next = event.target.value;
          onChange(next === "all" ? "all" : (next as ResearchRunType));
        }}
      >
        <option value="all">{zh ? "全部" : "All"}</option>
        {options.map((type) => (
          <option key={type} value={type}>
            {formatRunType(type, language)}
          </option>
        ))}
      </select>
    </div>
  );
}
