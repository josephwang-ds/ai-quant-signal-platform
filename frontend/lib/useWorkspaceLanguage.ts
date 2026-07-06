"use client";

import { useEffect, useState } from "react";
import {
  loadStoredLanguage,
  saveLanguage,
  t,
  type Language,
  type TranslationKey,
} from "@/lib/i18n";

/** 工作区页面共用的语言状态与翻译函数 */
export function useWorkspaceLanguage() {
  const [language, setLanguage] = useState<Language>("en");

  useEffect(() => {
    setLanguage(loadStoredLanguage());
  }, []);

  function handleLanguageChange(next: Language) {
    setLanguage(next);
    saveLanguage(next);
  }

  const tr = (key: TranslationKey) => t(language, key);

  return {
    language,
    setLanguage: handleLanguageChange,
    tr,
  };
}
