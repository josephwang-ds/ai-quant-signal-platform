"use client";

import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import type { BenchmarkEvaluation } from "@/types/researchBenchmark";

type Props = {
  benchmark: BenchmarkEvaluation | null;
  language: Language;
};

function fmt(value: unknown): string {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return value == null ? "—" : String(value);
  }
  return Math.abs(value) <= 2 ? `${(value * 100).toFixed(2)}%` : value.toFixed(2);
}

export default function BenchmarkFrameworkPanel({
  benchmark,
  language,
}: Props) {
  const zh = language === "zh";
  if (!benchmark) {
    return (
      <section className="benchmark-framework benchmark-framework--empty">
        <h3>{zh ? "Benchmark 基准协议" : "Benchmark protocol"}</h3>
        <p>
          {zh
            ? "运行研究后，这里会显示同周期、同成本口径的确定性比较与判定。"
            : "Run the study to populate an aligned, deterministic benchmark comparison."}
        </p>
      </section>
    );
  }

  const variant =
    benchmark.verdict === "pass"
      ? "success"
      : benchmark.verdict === "fail"
        ? "danger"
        : "warning";

  return (
    <section className="benchmark-framework" aria-labelledby="benchmark-title">
      <header className="benchmark-framework__header">
        <div>
          <p className="section-eyebrow">
            {zh ? "第 1 层 · 确定性证据" : "Layer 1 · Deterministic evidence"}
          </p>
          <h3 id="benchmark-title">
            {zh ? "Benchmark 基准协议" : "Benchmark protocol"}
          </h3>
        </div>
        <StatusBadge label={benchmark.verdict.toUpperCase()} variant={variant} />
      </header>

      <dl className="benchmark-framework__facts">
        <div>
          <dt>{zh ? "主要基准" : "Primary benchmark"}</dt>
          <dd>{benchmark.primary_benchmark}</dd>
        </div>
        <div>
          <dt>{zh ? "为什么合适" : "Why appropriate"}</dt>
          <dd>{benchmark.why_appropriate}</dd>
        </div>
        <div>
          <dt>{zh ? "比较周期" : "Comparison period"}</dt>
          <dd>
            {Object.entries(benchmark.comparison_period)
              .map(([key, value]) => `${key}: ${fmt(value)}`)
              .join(" · ")}
          </dd>
        </div>
        <div>
          <dt>{zh ? "成本口径" : "Cost assumptions"}</dt>
          <dd>{benchmark.cost_assumption}</dd>
        </div>
        <div>
          <dt>{zh ? "风险调整方法" : "Risk-adjusted method"}</dt>
          <dd>{benchmark.risk_adjusted_method}</dd>
        </div>
      </dl>

      {benchmark.ranking_convention ? (
        <div className="benchmark-framework__convention">
          <strong>{zh ? "分位数方向" : "Quantile direction"}</strong>
          <p>
            {benchmark.ranking_convention.raw_direction} ·{" "}
            {benchmark.ranking_convention.normalization}
          </p>
          <p>{benchmark.ranking_convention.q5_meaning}</p>
        </div>
      ) : null}

      <div className="benchmark-framework__criteria">
        <h4>{zh ? "预先配置的成功标准" : "Configured success criteria"}</h4>
        <ul>
          {Object.entries(benchmark.configured_success_criteria).map(
            ([key, value]) => (
              <li key={key}>
                <span>{key.replaceAll("_", " ")}</span>
                <strong>{fmt(value)}</strong>
              </li>
            )
          )}
        </ul>
      </div>

      <div className="benchmark-framework__comparison">
        <h4>{zh ? "策略与基准结果" : "Strategy versus benchmark"}</h4>
        <dl>
          {Object.entries(benchmark.comparison).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>{fmt(value)}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="benchmark-framework__checks">
        {benchmark.checks.map((check) => (
          <article key={check.check_id}>
            <StatusBadge
              label={check.status.toUpperCase()}
              variant={
                check.status === "pass"
                  ? "success"
                  : check.status === "fail"
                    ? "danger"
                    : "warning"
              }
            />
            <div>
              <strong>{check.name}</strong>
              <p>{check.explanation}</p>
              <small>{check.evidence_source}</small>
            </div>
          </article>
        ))}
      </div>
      {benchmark.passed_criteria?.length ||
      benchmark.failed_criteria?.length ||
      benchmark.unavailable_criteria?.length ? (
        <div className="benchmark-framework__criterion-summary">
          <p>
            <strong>{zh ? "通过：" : "Passed: "}</strong>
            {benchmark.passed_criteria?.join(", ") || "—"}
          </p>
          <p>
            <strong>{zh ? "失败：" : "Failed: "}</strong>
            {benchmark.failed_criteria?.join(", ") || "—"}
          </p>
          <p>
            <strong>{zh ? "缺失：" : "Unavailable: "}</strong>
            {benchmark.unavailable_criteria?.join(", ") || "—"}
          </p>
        </div>
      ) : null}
      <p className="benchmark-framework__verdict">{benchmark.rationale}</p>
    </section>
  );
}
