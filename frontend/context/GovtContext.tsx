"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "en" | "hi";
export type FontSize = "normal" | "large" | "xlarge";
export type ThemeMode = "light" | "dark";

interface GovtContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  fontSize: FontSize;
  setFontSize: (size: FontSize) => void;
  highContrast: boolean;
  setHighContrast: (hc: boolean | ((prev: boolean) => boolean)) => void;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode | ((prev: ThemeMode) => ThemeMode)) => void;
  t: (enText: string, hiText: string) => string;
}

const GovtContext = createContext<GovtContextType | undefined>(undefined);

export function GovtProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Language>("hi");
  const [fontSize, setFontSize] = useState<FontSize>("normal");
  const [highContrast, setHighContrast] = useState<boolean>(false);
  const [themeMode, setThemeMode] = useState<ThemeMode>("light");

  const t = (enText: string, hiText: string) => (lang === "hi" ? hiText : enText);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("text-base", "text-lg", "text-xl");
    if (fontSize === "large") {
      root.style.fontSize = "17px";
    } else if (fontSize === "xlarge") {
      root.style.fontSize = "18px";
    } else {
      root.style.fontSize = "16px";
    }
  }, [fontSize]);

  return (
    <GovtContext.Provider
      value={{
        lang,
        setLang,
        fontSize,
        setFontSize,
        highContrast,
        setHighContrast,
        themeMode,
        setThemeMode,
        t,
      }}
    >
      <div className={highContrast ? "contrast-125 saturate-200" : ""}>
        {children}
      </div>
    </GovtContext.Provider>
  );
}

export function useGovt() {
  const context = useContext(GovtContext);
  if (!context) {
    throw new Error("useGovt must be used within a GovtProvider");
  }
  return context;
}
