import type { NotebookRelatedArtifact } from "@/types/notebook";

type RelatedArtifactLinkProps = {
  artifact: NotebookRelatedArtifact;
  label?: string;
};

/**
 * 关联实验 / 验证 / 证据引用（mock 锚点，无真实路由跳转）。
 * TODO(api): 链接到 Experiment / ValidationRun / Evidence 详情。
 */
export default function RelatedArtifactLink({
  artifact,
  label = "Related",
}: RelatedArtifactLinkProps) {
  return (
    <p className="notebook-artifact-link">
      <span className="notebook-artifact-link__label">{label}</span>
      <span className="notebook-artifact-link__kind">{artifact.kind}</span>
      <span className="notebook-artifact-link__text">{artifact.label}</span>
      <span className="notebook-artifact-link__id font-mono">{artifact.id}</span>
    </p>
  );
}
