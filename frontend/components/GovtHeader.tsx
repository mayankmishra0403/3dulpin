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
      <div className="max-w-7xl mx-auto px-4 lg:px-12 py-4 flex items-center justify-between">
        {/* LEFT — BIG ASHOKA EMBLEM */}
        <AshokaEmblem className="h-52 w-52" />

        {/* RIGHT — PM CIRCULAR PORTRAIT */}
        <div className="flex flex-col gap-3">
          {PORTRAITS.map((p) => (
            <div key={p.name} className="flex items-center gap-3">
              <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-full border-4 border-[#F59900] bg-slate-100">
                <Image src={p.img} alt={p.name} fill sizes="80px" unoptimized className="object-cover object-top" />
              </div>
              <div className="max-w-[140px]">
                <div className="text-[12px] font-bold text-slate-900 leading-tight">{p.name}</div>
                <div className="text-[10px] text-slate-600 font-medium leading-tight mt-0.5">
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
