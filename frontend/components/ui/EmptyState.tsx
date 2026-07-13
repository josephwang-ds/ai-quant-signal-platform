import type { ReactNode } from "react";

type EmptyStateProps = {
  /** 兼容旧用法：单行提示 */
  message?: string;
  title?: string;
  description?: string;
  action?: ReactNode;
};

/**
 * 空状态：支持简单 message 或标题 + 描述 + 操作区。
 */
export default function EmptyState({
  message,
  title,
  description,
  action,
}: EmptyStateProps) {
  if (message && !title && !description) {
    return <p className="empty-state">{message}</p>;
  }

  return (
    <div className="empty-state-panel">
      {title ? <h3 className="empty-state-panel__title">{title}</h3> : null}
      {description ? (
        <p className="empty-state-panel__description">{description}</p>
      ) : null}
      {action ? <div className="empty-state-panel__action">{action}</div> : null}
    </div>
  );
}
