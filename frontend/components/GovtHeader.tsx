"use client";

import React from "react";
import Image from "next/image";
import { useGovt } from "@/context/GovtContext";
import { AshokaEmblem, TricolorStrip } from "./GovtLogos";

const IMG = "https://commons.wikimedia.org/wiki/Special:FilePath/Official%20portrait%20of%20Narendra%20Modi%2C%202022.jpg?width=400";

const PORTRAITS = [
  { name: "Shri Narendra Modi", roleEn: "Hon'ble Prime Minister of India", roleHi: "माननीय प्रधानमंत्री, भारत", img: IMG },
];

export function GovtHeader() {
  const { lang, setLang, t, setHighContrast } = useGovt();

  return (
    <header className="w-full border-b border-slate-300 bg-white text-slate-900">
      {/* TRICOLOR STRIP ON TOP */}
      <TricolorStrip className="h-2 w-full" />

      {/* TOP UTILITY BAR — STATIC, PLAIN TEXT */}
      <div className="bg-[#EBEBEB] px-4 lg:px-12 py-1.5 text-xs border-b border-slate-300">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span className="font-medium text-slate-800">
            {t("भारत सरकार", "भारत सरकार")} <span className="text-slate-400">|</span>{" "}
            <span className="font-semibold text-slate-950">
              {t("GOVERNMENT OF INDIA", "भारत की सरकार")}
            </span>
          </span>

          <div className="flex items-center gap-4 text-slate-700">
            <button
              onClick={() => setHighContrast((prev) => !prev)}
              className="hover:text-black cursor-pointer"
              title="High Contrast"
            >
              A+
            </button>
            <button
              onClick={() => setLang(lang === "hi" ? "en" : "hi")}
              className="hover:text-black cursor-pointer"
              title="Switch Language"
            >
              {lang === "hi" ? "English" : "हिन्दी"}
            </button>
          </div>
        </div>
      </div>

      {/* LOGO BAR */}
      <div className="max-w-7xl mx-auto px-4 lg:px-12 py-3.5 flex items-center justify-between gap-4">
        {/* LEFT — ASHOKA EMBLEM + PORTAL TITLE */}
        <div className="flex items-center gap-4">
          <AshokaEmblem className="h-14 w-auto shrink-0" />
          <div className="border-l border-slate-300 pl-4 py-0.5">
            <h1 className="text-base sm:text-lg font-extrabold text-[#002B49] tracking-tight leading-snug">
              {t("3D Bhu-Aadhaar National Portal", "3D भू-आधार राष्ट्रीय पोर्टल")}
            </h1>
            <p className="text-[11px] text-slate-600 font-medium">
              {t(
                "Department of Land Resources • Ministry of Rural Development",
                "भूमि संसाधन विभाग • ग्रामीण विकास मंत्रालय"
              )}
            </p>
          </div>
        </div>

        {/* RIGHT — PM CIRCULAR PORTRAIT */}
        <div className="hidden sm:flex items-center gap-3 bg-slate-50/80 rounded-full pl-1.5 pr-4 py-1 border border-slate-200">
          {PORTRAITS.map((p) => (
            <div key={p.name} className="flex items-center gap-2.5">
              <div className="relative h-11 w-11 shrink-0 overflow-hidden rounded-full border-2 border-[#F59900] bg-slate-100 shadow-sm">
                <Image src={p.img} alt={p.name} fill sizes="44px" unoptimized className="object-cover object-top" />
              </div>
              <div className="text-left">
                <div className="text-xs font-bold text-slate-900 leading-tight">{p.name}</div>
                <div className="text-[10px] text-slate-500 font-medium leading-tight">
                  {t(p.roleEn, p.roleHi)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
