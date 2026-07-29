"use client";

import Button from "@/components/ui/Button";
import IntegrityHint from "@/components/features/intelligence-workspace/IntegrityHint";
import {
  ViewEmptyState,
  ViewLocalError,
} from "@/components/features/intelligence-workspace/WorkspaceStates";
import type { Language } from "@/lib/i18n";
import type {
  ReferenceListState,
} from "@/lib/intelligence/usePublishedRun";
import type {
  ArtifactReferenceDto,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";
import {
  formatByteSize,
  formatNullableText,
  formatPublishedTimestamp,
  truncateChecksum,
} from "@/lib/intelligence/workspaceDisplay";

export type EvidenceViewProps = {
  language: Language;
  snapshots: ReferenceListState<SnapshotReferenceDto>;
  artifacts: ReferenceListState<ArtifactReferenceDto>;
  onRetrySnapshots: () => void;
  onRetryArtifacts: () => void;
};

function ChecksumCell({
  algorithm,
  checksum,
}: {
  algorithm: string;
  checksum: string;
}) {
  const truncated = truncateChecksum(checksum);
  return (
    <code title={`${algorithm}: ${checksum}`}>
      {algorithm}: {truncated}
    </code>
  );
}

export default function EvidenceView({
  language,
  snapshots,
  artifacts,
  onRetrySnapshots,
  onRetryArtifacts,
}: EvidenceViewProps) {
  const zh = language === "zh";

  return (
    <section
      className="published-workspace__view"
      aria-labelledby="workspace-view-heading"
      data-testid="evidence-view"
    >
      <h2 id="workspace-view-heading" tabIndex={-1}>
        {zh ? "证据" : "Evidence"}
      </h2>
      <p className="published-workspace__lede">
        {zh
          ? "仅展示登记引用。不下载产物内容；完整性已记录，本页不执行核验。"
          : "Reference lists only. Artifact payloads are not downloaded. Integrity is recorded—not verified on this page."}
      </p>

      <div className="published-workspace__subsection" data-testid="evidence-snapshots">
        <div className="published-workspace__subsection-header">
          <h3>{zh ? "快照" : "Snapshots"}</h3>
          <IntegrityHint kind="consumer_contract" language={language} />
        </div>

        {snapshots.status === "loading" || snapshots.status === "idle" ? (
          <div className="published-workspace__view-loading" aria-hidden="true">
            <div className="research-skeleton research-skeleton--line" />
            <div className="research-skeleton research-skeleton--block" />
          </div>
        ) : null}

        {snapshots.status === "error" ? (
          <ViewLocalError
            language={language}
            error={snapshots.error}
            onRetry={onRetrySnapshots}
          />
        ) : null}

        {snapshots.status === "ready" && snapshots.items.length === 0 ? (
          <ViewEmptyState
            title={
              zh
                ? "未发布消费端快照。"
                : "No consumer snapshots published."
            }
          />
        ) : null}

        {snapshots.status === "ready" && snapshots.items.length > 0 ? (
          <div className="published-workspace__table-wrap">
            <table className="published-workspace__table">
              <caption className="research-library__sr-only">
                {zh ? "消费端快照引用" : "Consumer snapshot references"}
              </caption>
              <thead>
                <tr>
                  <th scope="col">{zh ? "名称" : "Name"}</th>
                  <th scope="col">{zh ? "类型" : "Type"}</th>
                  <th scope="col">{zh ? "架构" : "Schema"}</th>
                  <th scope="col">{zh ? "创建时间" : "Created"}</th>
                  <th scope="col">{zh ? "截至" : "As of"}</th>
                  <th scope="col">{zh ? "大小" : "Size"}</th>
                  <th scope="col">{zh ? "来源产物" : "Sources"}</th>
                  <th scope="col">{zh ? "校验和" : "Checksum"}</th>
                  <th scope="col">{zh ? "完整性" : "Integrity"}</th>
                </tr>
              </thead>
              <tbody>
                {snapshots.items.map((item) => {
                  const created = formatPublishedTimestamp(item.created_at, language);
                  const asOf = formatPublishedTimestamp(item.as_of, language);
                  return (
                    <tr key={item.snapshot_id} data-testid="snapshot-reference-row">
                      <td>{item.name}</td>
                      <td>
                        <code>{item.snapshot_type}</code>
                      </td>
                      <td>
                        <code>{item.schema_version}</code>
                      </td>
                      <td>
                        {created.dateTime ? (
                          <time dateTime={created.dateTime}>{created.display}</time>
                        ) : (
                          created.display
                        )}
                      </td>
                      <td>
                        {asOf.dateTime ? (
                          <time dateTime={asOf.dateTime}>{asOf.display}</time>
                        ) : (
                          asOf.display
                        )}
                      </td>
                      <td>{formatByteSize(item.size_bytes)}</td>
                      <td>{item.source_artifact_ids.length}</td>
                      <td>
                        <ChecksumCell
                          algorithm={item.checksum_algorithm}
                          checksum={item.checksum}
                        />
                      </td>
                      <td>
                        <IntegrityHint kind="integrity_recorded" language={language} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      <div className="published-workspace__subsection" data-testid="evidence-artifacts">
        <div className="published-workspace__subsection-header">
          <h3>{zh ? "产物" : "Artifacts"}</h3>
          <IntegrityHint kind="opaque_evidence" language={language} />
        </div>

        {artifacts.status === "loading" || artifacts.status === "idle" ? (
          <div className="published-workspace__view-loading" aria-hidden="true">
            <div className="research-skeleton research-skeleton--line" />
            <div className="research-skeleton research-skeleton--block" />
          </div>
        ) : null}

        {artifacts.status === "error" ? (
          <ViewLocalError
            language={language}
            error={artifacts.error}
            onRetry={onRetryArtifacts}
          />
        ) : null}

        {artifacts.status === "ready" && artifacts.items.length === 0 ? (
          <ViewEmptyState
            title={
              zh
                ? "未发布产物引用。"
                : "No artifact references published."
            }
          />
        ) : null}

        {artifacts.status === "ready" && artifacts.items.length > 0 ? (
          <div className="published-workspace__table-wrap">
            <table className="published-workspace__table">
              <caption className="research-library__sr-only">
                {zh ? "不透明产物引用" : "Opaque artifact references"}
              </caption>
              <thead>
                <tr>
                  <th scope="col">{zh ? "名称" : "Name"}</th>
                  <th scope="col">{zh ? "类型" : "Type"}</th>
                  <th scope="col">{zh ? "架构" : "Schema"}</th>
                  <th scope="col">{zh ? "创建时间" : "Created"}</th>
                  <th scope="col">{zh ? "行数" : "Rows"}</th>
                  <th scope="col">{zh ? "大小" : "Size"}</th>
                  <th scope="col">{zh ? "校验和" : "Checksum"}</th>
                </tr>
              </thead>
              <tbody>
                {artifacts.items.map((item) => {
                  const created = formatPublishedTimestamp(item.created_at, language);
                  return (
                    <tr key={item.artifact_id} data-testid="artifact-reference-row">
                      <td>{item.name}</td>
                      <td>
                        <code>{item.artifact_type}</code>
                      </td>
                      <td>
                        <code>{item.schema_version}</code>
                      </td>
                      <td>
                        {created.dateTime ? (
                          <time dateTime={created.dateTime}>{created.display}</time>
                        ) : (
                          created.display
                        )}
                      </td>
                      <td>
                        {item.row_count == null
                          ? formatNullableText(null)
                          : String(item.row_count)}
                      </td>
                      <td>{formatByteSize(item.size_bytes)}</td>
                      <td>
                        <ChecksumCell
                          algorithm={item.checksum_algorithm}
                          checksum={item.checksum}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {(snapshots.status === "error" || artifacts.status === "error") &&
      (snapshots.status === "ready" || artifacts.status === "ready") ? (
        <div className="button-row">
          {snapshots.status === "error" ? (
            <Button onClick={onRetrySnapshots}>{zh ? "重试快照" : "Retry snapshots"}</Button>
          ) : null}
          {artifacts.status === "error" ? (
            <Button onClick={onRetryArtifacts}>{zh ? "重试产物" : "Retry artifacts"}</Button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
