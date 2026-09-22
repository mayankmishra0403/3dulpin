"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";

export function GovtPartnersCarousel() {
  const { t } = useGovt();

  const partners = [
    { title_hi: "जेम (e-Portal)", title_en: "GeM (e-Marketplace)", subtitle: "Government e-Marketplace", link: "https://gem.gov.in" },
    { title_hi: "राष्ट्रीय मतदाता सेवा पोर्टल", title_en: "National Voters' Service Portal", subtitle: "Election Commission of India", link: "https://voters.eci.gov.in" },
    { title_hi: "भारत सरकार", title_en: "Government of India", subtitle: "National Portal of India", link: "https://www.india.gov.in" },
    { title_hi: "राजस्व विभाग उत्तर प्रदेश", title_en: "Revenue Department UP", subtitle: "Board of Revenue", link: "https://upbhulekh.gov.in" },
  ];

  return (
    <div className="w-full bg-white py-6 border-t border-b border-slate-300">
      <div className="max-w-7xl mx-auto px-4 lg:px-12">
        <h3 className="text-sm font-bold text-slate-800 mb-4">
          {t("Important Government Links", "महत्वपूर्ण सरकारी लिंक")}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {partners.map((p) => (
            <a
              key={p.title_en}
              href={p.link}
              target="_blank"
              rel="noreferrer"
              className="bg-white border border-slate-300 hover:border-[#B85C00] rounded-lg px-4 py-3 transition-colors"
            >
              <div className="font-semibold text-[#002B49] text-xs sm:text-sm">{t(p.title_en, p.title_hi)}</div>
              <div className="text-[10px] text-slate-500 mt-1">{p.subtitle}</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}