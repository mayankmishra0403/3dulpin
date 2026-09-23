"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";

export function DolrGovtMetricsRow() {
  const { t } = useGovt();

  const metrics = [
    { num_hi: "6.31 लाख", num_en: "6.31 Lakhs", title_hi: "सी एल आर (CLR Records)", title_en: "CLR Land Records" },
    { num_hi: "4.15 करोड़", num_en: "4.15 Crores", title_hi: "डिजी. मानचित्र", title_en: "Digital Cadastral Maps" },
    { num_hi: "5611", num_en: "5,611", title_hi: "एसआरओ (Computerized SROs)", title_en: "Sub-Registrar Offices" },
    { num_hi: "40.85 करोड़", num_en: "40.85 Crores", title_hi: "भू-आधार (ULPIN Issued)", title_en: "Bhu-Aadhaar (3D ULPIN)" },
    { num_hi: "1114226(हेक.)", num_en: "11,14,226 Ha", title_hi: "डब्ल्यूडीसी (WDC Watershed)", title_en: "WDC Watershed Area" },
    { num_hi: "308558(हेक.)", num_en: "3,08,558 Ha", title_hi: "सिंचाई (Irrigation)", title_en: "Irrigation Coverage" },
    { num_hi: "147259(हेक.)", num_en: "1,47,259 Ha", title_hi: "पेड़ लगाना (Afforestation)", title_en: "Plantation Area" },
    { num_hi: "2.85 करोड़", num_en: "2.85 Crores", title_hi: "रोज़गार (Man-days)", title_en: "Employment Generated" },
  ];

  return (
    <div className="w-full bg-slate-50/60 py-6 border-y border-slate-200/80 rounded-2xl">
      <div className="max-w-7xl mx-auto px-4 lg:px-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
          {metrics.map((m, idx) => (
            <div
              key={idx}
              className="bg-white border border-slate-200/90 rounded-xl p-3 text-center flex flex-col items-center justify-center min-h-[84px] shadow-sm hover:border-[#F59900] transition-colors"
            >
              <div className="font-extrabold text-[#002B49] text-sm sm:text-base tracking-tight">
                {t(m.num_en, m.num_hi)}
              </div>
              <div className="text-[10px] font-semibold text-slate-500 mt-1 leading-snug">
                {t(m.title_en, m.title_hi)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
