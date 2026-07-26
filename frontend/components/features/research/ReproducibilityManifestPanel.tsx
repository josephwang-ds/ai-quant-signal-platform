"use client";

import { useState, type ReactNode } from "react";
import type { Language } from "@/lib/i18n";
import type { ReproducibilityManifest } from "@/types/reproducibility";

const MISSING = "__MISSING__";
const HASH_PREVIEW_LEN = 10;

type Labels = {
  title: string;
  shortSummary: string;
  expand: string;
  collapse: string;
  copy: string;
  copied: string;
  hashNote: string;
  fields: Record<string, string>;
};

type Props = {
  manifest: ReproducibilityManifest | null | undefined;
  language?: Language;
  labels?: Partial<Labels>;
};

const DEFAULT_LABELS_EN: Labels = {
  title: "Reproducibility",
  shortSummary: "Data fingerprint and protocol identity for this result.",
  expand: "Full manifest",
  collapse: "Hide full manifest",
  copy: "Copy",
  copied: "Copied",
  hashNote:
    "Hashes identify inputs for comparison. They are not a certification or security guarantee.",
  fields: {
    data_source: "Data source",
    symbol: "Symbol",
    universe: "Universe",
    requested_start_date: "Requested start",
    requested_end_date: "Requested end",
    actual_start_date: "Actual start",
    actual_end_date: "Actual end",
    retrieval_timestamp: "Retrieved",
    row_count: "Rows",
    adjustment_mode: "Adjustment",
    protocol_version: "Protocol version",
    protocol_hash: "Protocol hash",
    data_hash: "Data hash",
    engine_version: "Engine version",
    git_commit_sha: "Git commit",
    runtime_version: "Runtime",
    created_at: "Created",
  },
};

const DEFAULT_LABELS_ZH: Labels = {
  title: "可复现性",
  shortSummary: "本结果的数据指纹与协议标识。",
  expand: "完整 Manifest",
  collapse: "收起完整 Manifest",
  copy: "复制",
  copied: "已复制",
  hashNote: "哈希用于标识与比对输入，不是认证或安全保证。",
  fields: {
    data_source: "数据源",
    symbol: "标的",
    universe: "股票池",
    requested_start_date: "请求起始",
    requested_end_date: "请求结束",
    actual_start_date: "实际起始",
    actual_end_date: "实际结束",
    retrieval_timestamp: "拉取时间",
    row_count: "行数",
    adjustment_mode: "复权",
    protocol_version: "协议版本",
    protocol_hash: "协议哈希",
    data_hash: "数据哈希",
    engine_version: "引擎版本",
    git_commit_sha: "Git 提交",
    runtime_version: "运行时",
    created_at: "创建时间",
  },
};

function displayValue(value: unknown): string {
  if (value == null || value === "" || value === MISSING) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function shortenHash(value: string | undefined | null): string {
  if (!value || value === MISSING || value === "unavailable") {
    return displayValue(value);
  }
  if (value.length <= HASH_PREVIEW_LEN) {
    return value;
  }
  return value.slice(0, HASH_PREVIEW_LEN);
}

async function copyText(value: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch {
    /* fall through */
  }
  return false;
}

function HashValue({
  value,
  copyLabel,
  copiedLabel,
}: {
  value: string;
  copyLabel: string;
  copiedLabel: string;
}) {
  const [copied, setCopied] = useState(false);
  const preview = shortenHash(value);
  const canCopy = Boolean(value) && value !== MISSING && value !== "unavailable";

  return (
    <span className="repro-manifest__hash">
      <code className="font-mono" title={canCopy ? value : undefined}>
        {preview}
      </code>
      {canCopy ? (
        <button
          type="button"
          className="repro-manifest__copy"
          onClick={async () => {
            const ok = await copyText(value);
            if (ok) {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1500);
            }
          }}
        >
          {copied ? copiedLabel : copyLabel}
        </button>
      ) : null}
    </span>
  );
}

export default function ReproducibilityManifestPanel({
  manifest,
  language = "en",
  labels,
}: Props) {
  if (!manifest || typeof manifest !== "object") {
    return null;
  }

  const base = language === "zh" ? DEFAULT_LABELS_ZH : DEFAULT_LABELS_EN;
  const merged: Labels = {
    ...base,
    ...labels,
    fields: { ...base.fields, ...(labels?.fields ?? {}) },
  };

  const symbolOrUniverse =
    manifest.universe && displayValue(manifest.universe) !== "—"
      ? displayValue(manifest.universe)
      : displayValue(manifest.symbol);
  const range = `${displayValue(manifest.actual_start_date)} → ${displayValue(
    manifest.actual_end_date
  )}`;

  const rows: Array<[string, ReactNode]> = [
    [merged.fields.data_source, displayValue(manifest.data_source)],
    [merged.fields.symbol, displayValue(manifest.symbol)],
    [merged.fields.universe, displayValue(manifest.universe)],
    [merged.fields.requested_start_date, displayValue(manifest.requested_start_date)],
    [merged.fields.requested_end_date, displayValue(manifest.requested_end_date)],
    [merged.fields.actual_start_date, displayValue(manifest.actual_start_date)],
    [merged.fields.actual_end_date, displayValue(manifest.actual_end_date)],
    [merged.fields.retrieval_timestamp, displayValue(manifest.retrieval_timestamp)],
    [merged.fields.row_count, displayValue(manifest.row_count)],
    [merged.fields.adjustment_mode, displayValue(manifest.adjustment_mode)],
    [merged.fields.protocol_version, displayValue(manifest.protocol_version)],
    [
      merged.fields.protocol_hash,
      <HashValue
        key="protocol_hash"
        value={String(manifest.protocol_hash ?? "")}
        copyLabel={merged.copy}
        copiedLabel={merged.copied}
      />,
    ],
    [
      merged.fields.data_hash,
      <HashValue
        key="data_hash"
        value={String(manifest.data_hash ?? "")}
        copyLabel={merged.copy}
        copiedLabel={merged.copied}
      />,
    ],
    [merged.fields.engine_version, displayValue(manifest.engine_version)],
    [merged.fields.git_commit_sha, displayValue(manifest.git_commit_sha)],
    [merged.fields.runtime_version, displayValue(manifest.runtime_version)],
    [merged.fields.created_at, displayValue(manifest.created_at)],
  ];

  return (
    <aside className="repro-manifest" aria-label={merged.title}>
      <div className="repro-manifest__header">
        <h3 className="repro-manifest__title">{merged.title}</h3>
        <p className="repro-manifest__summary">{merged.shortSummary}</p>
      </div>
      <dl className="repro-manifest__short">
        <div>
          <dt>{merged.fields.data_source}</dt>
          <dd>{displayValue(manifest.data_source)}</dd>
        </div>
        <div>
          <dt>
            {manifest.universe && displayValue(manifest.universe) !== "—"
              ? merged.fields.universe
              : merged.fields.symbol}
          </dt>
          <dd className="font-mono">{symbolOrUniverse}</dd>
        </div>
        <div>
          <dt>{merged.fields.actual_start_date}</dt>
          <dd className="font-mono">{range}</dd>
        </div>
        <div>
          <dt>{merged.fields.data_hash}</dt>
          <dd>
            <HashValue
              value={String(manifest.data_hash ?? "")}
              copyLabel={merged.copy}
              copiedLabel={merged.copied}
            />
          </dd>
        </div>
        <div>
          <dt>{merged.fields.protocol_hash}</dt>
          <dd>
            <HashValue
              value={String(manifest.protocol_hash ?? "")}
              copyLabel={merged.copy}
              copiedLabel={merged.copied}
            />
          </dd>
        </div>
      </dl>
      <p className="repro-manifest__note">{merged.hashNote}</p>
      <details className="repro-manifest__details">
        <summary>
          <span className="repro-manifest__expand-label">{merged.expand}</span>
          <span className="repro-manifest__collapse-label">{merged.collapse}</span>
        </summary>
        <dl className="repro-manifest__full">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </details>
    </aside>
  );
}
