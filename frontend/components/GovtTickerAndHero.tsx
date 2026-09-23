"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";
import Link from "next/link";

export function GovtTickerAndHero() {
  const { t } = useGovt();

  return (
    <div className="w-full space-y-3">
      {/* HERO BANNER */}
      <div className="rounded-2xl bg-gradient-to-r from-[#002B49] via-[#00364A] to-[#004B6E] text-white shadow-lg overflow-hidden border border-slate-800">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-7 sm:py-9">
          <span className="inline-block px-3 py-1 bg-[#F59900] text-slate-950 font-bold text-[11px] uppercase tracking-wider rounded-md shadow-sm">
            {t(
              "Digital India Land Records Modernisation Programme (DILRMP)",
              "डिजिटल इंडिया भूमि अभिलेख आधुनिकीकरण कार्यक्रम"
            )}
          </span>
          <h1 className="mt-3 text-xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight max-w-3xl">
            {t(
              "National 3D Bhu-Aadhaar Portal for Volumetric Land Records",
              "वॉल्यूमेट्रिक भूमि अभिलेखों के लिए राष्ट्रीय 3D भू-आधार पोर्टल"
            )}
          </h1>
          <p className="mt-2.5 text-xs sm:text-sm text-slate-200 leading-relaxed max-w-2xl font-normal">
            {t(
              "Inspect land records, multi-storey property rights and underground infrastructure in three dimensions using the 14-digit 3D ULPIN (Bhu-Aadhaar).",
              "14-अंकीय 3D ULPIN (भू-आधार) के माध्यम से भूमि अभिलेख, बहुमंजिला संपत्ति अधिकार एवं भूमिगत संरचनाओं का 3D में अवलोकन करें।"
            )}
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Link
              href="/scene"
              data-guide-step="explore3d"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#F59900] hover:bg-[#e08b00] text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all hover:scale-[1.02]"
            >
              {t("Explore 3D Cadastre Map", "3D भू-मानचित्र देखें")}
            </Link>
            <Link
              href="/ulpin"
              data-guide-step="ulpinlab"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-bold text-xs rounded-xl border border-white/30 transition-all"
            >
              {t("3D ULPIN Lab", "3D ULPIN लैब")}
            </Link>
          </div>
        </div>
      </div>

      {/* ANNOUNCEMENT TICKER */}
      <div className="rounded-xl bg-slate-900 text-white flex items-center text-xs overflow-hidden border border-slate-800 shadow-sm">
        <div className="bg-[#F59900] px-3.5 py-2 font-black text-slate-950 whitespace-nowrap flex items-center gap-1.5 shrink-0 text-[11px] uppercase tracking-wider">
          <span className="h-2 w-2 rounded-full bg-red-600 animate-ping" />
          <span>{t("Updates", "नवीनतम")}</span>
        </div>
        <div className="overflow-hidden whitespace-nowrap px-4 py-2 text-slate-200 text-xs font-medium flex-1">
          <div className="inline-block animate-marquee">
            {t(
              "3D Bhu-Aadhaar (ULPIN) Volumetric Cadastre Standards are open for public suggestions from 14th to 28th September, 2026.",
              "3D भू-आधार (ULPIN) वॉल्यूमेट्रिक मानकों पर दिनांक 14 से 28 सितंबर, 2026 तक जन सुझाव आमंत्रित हैं।"
            )}{" "}
            <span className="inline-block px-1.5 py-0.5 bg-rose-600 text-white text-[9px] font-bold rounded ml-2 uppercase">
              {t("NEW", "नई")}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}