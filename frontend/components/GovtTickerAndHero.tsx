"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";
import Link from "next/link";

export function GovtTickerAndHero() {
  const { t } = useGovt();

  return (
    <div className="w-full">
      {/* HERO BANNER */}
      <div className="bg-[#002B49] text-white">
        <div className="max-w-7xl mx-auto px-4 lg:px-12 py-10 sm:py-14">
          <span className="inline-block px-3 py-1 bg-[#F59900] text-slate-950 font-semibold text-xs uppercase tracking-wider">
            {t(
              "Digital India Land Records Modernisation Programme",
              "डिजिटल इंडिया भूमि अभिलेख आधुनिकीकरण कार्यक्रम"
            )}
          </span>
          <h1 className="mt-4 text-2xl sm:text-4xl font-bold text-white leading-tight max-w-3xl">
            {t(
              "National 3D Bhu-Aadhaar Portal for Volumetric Land Records",
              "वॉल्यूमेट्रिक भूमि अभिलेखों के लिए राष्ट्रीय 3D भू-आधार पोर्टल"
            )}
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-200 leading-relaxed max-w-2xl">
            {t(
              "Inspect land records, multi-storey property rights and underground infrastructure in three dimensions using the 14-digit 3D ULPIN (Bhu-Aadhaar).",
              "14-अंकीय 3D ULPIN (भू-आधार) के माध्यम से भूमि अभिलेख, बहुमंजिला संपत्ति अधिकार एवं भूमिगत संरचनाओं का 3D में अवलोकन करें।"
            )}
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              href="/scene"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#F59900] hover:bg-[#e08b00] text-slate-950 font-semibold text-sm rounded transition-colors"
            >
              {t("Explore 3D Cadastre Map", "3D भू-मानचित्र देखें")}
            </Link>
            <Link
              href="/ulpin"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white font-semibold text-sm rounded border border-white/30 transition-colors"
            >
              {t("3D ULPIN Lab", "3D ULPIN लैब")}
            </Link>
          </div>
        </div>
      </div>

      {/* ANNOUNCEMENT TICKER */}
      <div className="bg-[#00364A] text-white flex items-stretch text-xs border-b border-slate-900">
        <div className="flex items-center w-full overflow-hidden">
          <div className="bg-[#F59900] px-4 sm:px-6 py-2.5 font-bold text-slate-950 whitespace-nowrap flex items-center gap-2 shrink-0">
            <span className="h-2 w-2 rounded-full bg-red-700" />
            <span>{t("Latest Updates", "नवीनतम अद्यतन")}</span>
          </div>
          <div className="overflow-hidden whitespace-nowrap px-4 py-2.5 text-slate-100 flex-1">
            <div className="inline-block animate-marquee">
              {t(
                "3D Bhu-Aadhaar (ULPIN) Volumetric Cadastre Standards are open for public suggestions from 14th to 28th September, 2026.",
                "3D भू-आधार (ULPIN) वॉल्यूमेट्रिक मानकों पर दिनांक 14 से 28 सितंबर, 2026 तक जन सुझाव आमंत्रित हैं।"
              )}{" "}
              <span className="inline-block px-1.5 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded ml-2 uppercase">
                {t("NEW", "नई")}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}