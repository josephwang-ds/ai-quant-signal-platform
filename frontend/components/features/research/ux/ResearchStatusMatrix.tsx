import type { ReactNode } from "react";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  canonicalStatusVariant,
  type ResearchBadgeVariant,
} from "@/lib/researchStatusBadge";

export type ResearchStatusMatrixItem = {
  id: string;
  label: string;
  statusLabel: string;
  /** Canonical or domain status token for badge tone. */
  statusTone?: string;
  variant?: ResearchBadgeVariant;
};

export type ResearchStatusMatrixProps = {
  items: ResearchStatusMatrixItem[];
  empty?: ReactNode;
};

/**
 * Shared status matrix for Validation / Robustness / Observation / Decision checklists.
 */
export default function ResearchStatusMatrix({
  items,
  empty = null,
}: ResearchStatusMatrixProps) {
  if (items.length === 0) {
    return <>{empty}</>;
  }

  return (
    <ul className="research-matrix">
      {items.map((item) => (
        <li key={item.id} className="research-matrix__row">
          <span className="research-matrix__label">{item.label}</span>
          <StatusBadge
            label={item.statusLabel}
            variant={
              item.variant ??
              canonicalStatusVariant(item.statusTone ?? item.statusLabel)
            }
          />
        </li>
      ))}
    </ul>
  );
}
