import type { DataProvenance } from "@/types/researchExecution";

export type ProvenanceBannerLabels = {
  realData: string;
  cached: string;
  stale: string;
  provider: string;
  symbol: string;
  range: string;
  retrieved: string;
  disclaimer: string;
};

type ProvenanceBannerProps = {
  provenance: DataProvenance;
  labels: ProvenanceBannerLabels;
  warnings?: string[];
};

export default function ProvenanceBanner({
  provenance,
  labels,
  warnings = [],
}: ProvenanceBannerProps) {
  return (
    <aside className="provenance-banner" aria-label={labels.realData}>
      <div className="provenance-banner__badges">
        <span className="badge badge--success">{labels.realData}</span>
        {provenance.cache_hit ? (
          <span className="badge badge--info">
            {provenance.cache_stale ? labels.stale : labels.cached}
          </span>
        ) : null}
      </div>
      <dl className="provenance-banner__meta">
        <div>
          <dt>{labels.provider}</dt>
          <dd>{provenance.source}</dd>
        </div>
        <div>
          <dt>{labels.symbol}</dt>
          <dd className="font-mono">{provenance.symbol}</dd>
        </div>
        <div>
          <dt>{labels.range}</dt>
          <dd className="font-mono">
            {provenance.actual_start} → {provenance.actual_end}
          </dd>
        </div>
        <div>
          <dt>{labels.retrieved}</dt>
          <dd className="font-mono">{provenance.retrieved_at}</dd>
        </div>
      </dl>
      <p className="provenance-banner__disclaimer">{labels.disclaimer}</p>
      {warnings.length > 0 ? (
        <ul className="provenance-banner__warnings">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </aside>
  );
}
