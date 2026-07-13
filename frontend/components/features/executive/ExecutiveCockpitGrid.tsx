"use client";

import Link from "next/link";
import { EXECUTIVE_COCKPIT_TILES } from "@/lib/mockQuantData";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function ExecutiveCockpitGrid() {
  const { tr } = useWorkspaceLanguage();

  return (
    <div className="cockpit-grid">
      {EXECUTIVE_COCKPIT_TILES.map((tile) => (
        <article key={tile.id} className="cockpit-tile">
          <h3 className="cockpit-tile__title">{tr(tile.titleKey)}</h3>
          <p className="cockpit-tile__desc">{tr(tile.descKey)}</p>
          <Link href={tile.href} className="module-card__link">
            {tr("openModule")} →
          </Link>
        </article>
      ))}
    </div>
  );
}
