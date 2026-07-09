"use client";

import { usePathname } from "next/navigation";
import { useMemo } from "react";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import { pickQuantTip } from "@/lib/quantTips";

type QuantTipProps = {
  language: Language;
};

export default function QuantTip({ language }: QuantTipProps) {
  const pathname = usePathname();
  const tip = useMemo(() => pickQuantTip(pathname), [pathname]);

  return (
    <aside className="quant-tip" aria-label={t(language, "quantTipLabel")}>
      <p className="quant-tip__label">{t(language, "quantTipLabel")}</p>
      <p className="quant-tip__title">{t(language, tip.titleKey)}</p>
      <p className="quant-tip__body">{t(language, tip.bodyKey)}</p>
    </aside>
  );
}
