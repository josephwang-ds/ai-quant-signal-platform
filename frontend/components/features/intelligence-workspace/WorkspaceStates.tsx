"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import PublishedWorkspaceSkeleton from "@/components/features/intelligence-workspace/PublishedWorkspaceSkeleton";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import type { Language } from "@/lib/i18n";
import type { IntelligenceUiError } from "@/lib/intelligence/errorMap";

export function WorkspaceGateLoading({ language }: { language: Language }) {
  const zh = language === "zh";
  return (
    <PublishedWorkspaceSkeleton
      statusLabel={
        zh ? "正在加载已发布研究工作区…" : "Loading published research workspace…"
      }
    />
  );
}

export function WorkspaceGateError({
  language,
  title,
  message,
  onRetry,
}: {
  language: Language;
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  const zh = language === "zh";
  return (
    <div
      className="published-workspace__gate-error"
      role="alert"
      data-testid="published-workspace-gate-error"
    >
      <ErrorAlert title={title} message={message} />
      <div className="button-row">
        {onRetry ? (
          <Button primary onClick={onRetry} data-testid="published-workspace-retry">
            {zh ? "重试" : "Retry"}
          </Button>
        ) : null}
        <Link href="/" className="btn" data-testid="back-to-library">
          {zh ? "返回研究资料库" : "Back to Research Library"}
        </Link>
      </div>
    </div>
  );
}

export function ViewLocalError({
  language,
  error,
  onRetry,
}: {
  language: Language;
  error: IntelligenceUiError;
  onRetry?: () => void;
}) {
  const zh = language === "zh";
  const rateLimited =
    error.transportCode === "HTTP_429" ||
    error.message.toLowerCase().includes("busy right now");
  const accessDenied = error.status === 401 || error.status === 403;
  return (
    <div className="published-workspace__view-error" role="alert">
      <ErrorAlert
        title={
          error.category === "invalid_snapshot"
            ? zh
              ? "快照内容无效"
              : "Snapshot content is invalid"
            : error.category === "backend_unavailable"
              ? rateLimited
                ? zh
                  ? "请求过于频繁"
                  : "Too many requests"
                : zh
                  ? "后端暂时不可用"
                  : "Backend temporarily unavailable"
              : accessDenied
                ? zh
                  ? "无权访问此视图"
                  : "Access denied for this view"
                : zh
                  ? "无法加载此视图"
                  : "Could not load this view"
        }
        message={error.message}
      />
      {onRetry && !accessDenied ? (
        <Button primary onClick={onRetry}>
          {zh ? "重试" : "Retry"}
        </Button>
      ) : null}
    </div>
  );
}

export function ViewEmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <EmptyState title={title} description={description} action={action} />
  );
}
