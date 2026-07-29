"use client";

import Link from "next/link";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import type { Language } from "@/lib/i18n";
import type { IntelligenceUiError } from "@/lib/intelligence/errorMap";

export function ResearchLibraryLoading({ language }: { language: Language }) {
  const zh = language === "zh";
  return (
    <div
      className="research-library__loading"
      aria-busy="true"
      data-testid="research-library-loading"
    >
      <div className="research-library__loading-visual" aria-hidden="true">
        <div className="research-skeleton research-skeleton--title" />
        <div className="research-skeleton research-skeleton--line" />
        <div className="research-library__latest-skeleton">
          <div className="research-skeleton research-skeleton--block" />
        </div>
        <div className="research-library__grid research-library__grid--skeleton">
          {Array.from({ length: 3 }, (_, index) => (
            <div key={index} className="research-skeleton research-skeleton--block" />
          ))}
        </div>
      </div>
      <span className="research-library__sr-only" role="status" aria-live="polite">
        {zh ? "正在加载已发布研究…" : "Loading published research…"}
      </span>
    </div>
  );
}

export function ResearchLibraryEmptyState({ language }: { language: Language }) {
  const zh = language === "zh";
  return (
    <div data-testid="research-library-empty">
      <EmptyState
        title={zh ? "尚无已发布研究" : "No published research runs yet."}
        description={
          zh
            ? "研究运行经研究引擎验证并发布后，会出现在这里。"
            : "Research runs appear here after they are validated and published by the Research Engine."
        }
        action={
          <Link href="/engine" className="btn" data-testid="open-research-engine">
            {zh ? "打开研究引擎" : "Open Research Engine"}
          </Link>
        }
      />
    </div>
  );
}

export function ResearchLibraryErrorState({
  language,
  error,
  onRetry,
}: {
  language: Language;
  error: IntelligenceUiError;
  onRetry: () => void;
}) {
  const zh = language === "zh";
  const rateLimited =
    error.transportCode === "HTTP_429" ||
    error.message.toLowerCase().includes("busy right now");
  const accessDenied = error.status === 401 || error.status === 403;
  const heading =
    error.category === "backend_unavailable"
      ? rateLimited
        ? zh
          ? "请求过于频繁"
          : "Too many requests"
        : zh
          ? "研究后端暂时不可用"
          : "Research backend unavailable"
      : error.category === "malformed_response"
        ? zh
          ? "已发布研究数据异常"
          : "Published research data is inconsistent"
        : accessDenied
          ? zh
            ? "无权访问已发布研究"
            : "Published research access denied"
          : zh
            ? "无法加载研究资料库"
            : "Could not load the Research Library";

  return (
    <div
      className="research-library__error"
      role="alert"
      data-testid="research-library-error"
    >
      <ErrorAlert title={heading} message={error.message} />
      {!accessDenied ? (
        <Button primary onClick={onRetry} data-testid="research-library-retry">
          {zh ? "重试" : "Retry"}
        </Button>
      ) : null}
    </div>
  );
}
