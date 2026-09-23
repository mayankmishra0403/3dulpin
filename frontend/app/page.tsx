"use client";

import { useState } from "react";
import Link from "next/link";
import { useGovt } from "@/context/GovtContext";
import { GovtTickerAndHero } from "@/components/GovtTickerAndHero";
import { BhulekhSearchPanel } from "@/components/BhulekhSearchPanel";
import { DolrGovtMetricsRow } from "@/components/DolrGovtMetricsRow";
import { UpBhulekhPortalHero } from "@/components/UpBhulekhPortalHero";
import { MunicipalRevenueCard } from "@/components/MunicipalRevenueCard";
import { DolrGovtSchemesAndMinisters } from "@/components/DolrGovtSchemesAndMinisters";
import { GovtPartnersCarousel } from "@/components/GovtPartnersCarousel";
import { ShieldAlert, Box, Hash, LandPlot, ChevronDown, ExternalLink } from "lucide-react";

const FEATURES = [
  {
    key: "map",
    title: (t_: (en: string, hi: string) => string) => t_("3D Cadastre Map", "3D भू-मानचित्र"),
    desc: (t_: (en: string, hi: string) => string) =>
      t_(
        "Click any building to see its floors, suites and 14-digit 3D ULPIN, plus underground metro corridors.",
        "किसी भी इमारत पर क्लिक करके मंजिलें, सुइट और 14-अंकीय 3D ULPIN, साथ ही भूमिगत मेट्रो कॉरिडोर देखें।"
      ),
    href: "/scene",
    icon: Box,
    cta: (t_: (en: string, hi: string) => string) => t_("Open 3D Map", "3D मानचित्र खोलें"),
    badge: (t_: (en: string, hi: string) => string) => t_("3D", "3D"),
  },
  {
    key: "ulpin",
    title: (t_: (en: string, hi: string) => string) => t_("3D ULPIN Lab", "3D ULPIN लैब"),
    desc: (t_: (en: string, hi: string) => string) =>
      t_(
        "Paste any 14-digit ULPIN (Bhu-Aadhaar) to pull its full record — khasra, khata, owner, volume — or generate a new one.",
        "कोई भी 14-अंकीय ULPIN (भू-आधार) चिपकाकर उसका पूरा विवरण पाएँ — खसरा, खाता, स्वामी, आयतन — या नया ULPIN बनाएँ।"
      ),
    href: "/ulpin",
    icon: Hash,
    cta: (t_: (en: string, hi: string) => string) => t_("Open ULPIN Lab", "ULPIN लैब खोलें"),
    badge: (t_: (en: string, hi: string) => string) => t_("Lab", "लैब"),
  },
  {
    key: "validate",
    title: (t_: (en: string, hi: string) => string) => t_("Validation & AI", "जाँच व AI"),
    desc: (t_: (en: string, hi: string) => string) =>
      t_(
        "Compare AI-extracted 3D models against point-cloud reconstruction and certify spatial correctness.",
        "AI-निकाले गए 3D मॉडलों की तुलना पॉइंट-क्लाउड पुनर्निर्माण से करें और स्थानिक शुद्धता प्रमाणित करें।"
      ),
    href: "/validation",
    icon: LandPlot,
    cta: (t_: (en: string, hi: string) => string) => t_("Open Validation", "जाँच विभाग खोलें"),
    badge: (t_: (en: string, hi: string) => string) => t_("AI", "AI"),
  },
];

export default function Dashboard() {
  const { t } = useGovt();
  const [knowMoreOpen, setKnowMoreOpen] = useState(false);

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* HERO + ANNOUNCEMENT TICKER */}
      <GovtTickerAndHero />

      {/* PRIMARY FEATURE TILES */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {FEATURES.map((f) => {
          const Icon = f.icon;
          return (
            <Link
              key={f.key}
              href={f.href}
              className="group relative rounded-2xl border border-slate-200/90 bg-white p-5 transition-all hover:-translate-y-0.5 hover:border-[#F59900] hover:shadow-md shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-2.5 text-[#002B49] group-hover:bg-amber-50 group-hover:text-[#B85C00] transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
                <span className="rounded-md bg-[#002B49] px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-[#F59900]">
                  {f.badge(t)}
                </span>
              </div>
              <h3 className="mt-3 text-sm sm:text-base font-extrabold text-slate-900">{f.title(t)}</h3>
              <p className="mt-1.5 text-xs text-slate-600 leading-relaxed min-h-[44px] font-normal">{f.desc(t)}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-[#B85C00]">
                {f.cta(t)}
                <ExternalLink className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </section>

      {/* HOW IT WORKS STRIP */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
        {[
          [t("1 · Choose area", "1 · क्षेत्र चुनें"), t("District → Tehsil → Village", "जिला → तहसील → ग्राम")],
          [t("2 · Click a building", "2 · इमारत चुनें"), t("See it in 3D", "3D में देखें")],
          [t("3 · Open 3D ULPINs", "3 · 3D ULPIN देखें"), t("Floors, suites & volume", "मंजिलें, सुइट व आयतन")],
        ].map(([head, sub], i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-200/80 bg-slate-50/70 px-3.5 py-3 text-xs text-slate-700 shadow-sm"
          >
            <div className="font-extrabold text-[#002B49]">{head}</div>
            <div className="mt-0.5 font-medium text-slate-500 text-[11px]">{sub}</div>
          </div>
        ))}
      </section>

      {/* 3D KHATAUNI SEARCH */}
      <section data-guide-step="search" className="scroll-mt-24">
        <BhulekhSearchPanel />
      </section>

      {/* NATIONAL LAND RECORDS METRICS */}
      <DolrGovtMetricsRow />

      {/* ACTIVE 3D SPATIAL CONFLICT NOTICE */}
      <div
        data-guide-step="conflict"
        className="scroll-mt-24 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 rounded-2xl border border-rose-200 bg-rose-50/70 px-5 py-4 shadow-sm"
      >
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-rose-600 p-2 text-white shrink-0 shadow-sm">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-xs sm:text-sm font-extrabold text-rose-950">
                {t("Active 3D Spatial Conflict Alert", "सक्रिय 3D भू-स्थानिक अतिव्यापन चेतावनी")}
              </h3>
              <span className="rounded-md bg-rose-600 px-2 py-0.5 text-[9px] font-bold text-white uppercase tracking-wider">
                {t("High Severity", "गंभीर: उच्च")}
              </span>
            </div>
            <p className="text-xs text-rose-900 leading-relaxed font-medium">
              {t(
                "Metro Transit Tunnel 06080704900001-MTA17 vs High-Rise Lift Shaft 06080704000021-U38 — intersection ≈ 75.4 m³. Inspect in 3D.",
                "मेट्रो टनल 06080704900001-MTA17 बनाम लिफ्ट शाफ्ट 06080704000021-U38 — अतिव्याप्ति ≈ 75.4 m³। 3D में जाँचें।"
              )}
            </p>
          </div>
        </div>
        <Link
          href="/scene"
          className="inline-flex shrink-0 items-center gap-1.5 rounded-xl bg-rose-700 hover:bg-rose-800 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition-all cursor-pointer"
        >
          <span>{t("Inspect in 3D", "3D में जाँचें")}</span>
          <ExternalLink className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* KNOW MORE — extra detail stays collapsed, keeps page clean */}
      <section data-guide-step="knowmore" className="scroll-mt-24" id="know-more">
        <button
          onClick={() => setKnowMoreOpen((v) => !v)}
          className="flex w-full items-center justify-between rounded-2xl border border-slate-200/90 bg-white px-5 py-4 text-left transition-colors hover:border-[#F59900] cursor-pointer shadow-sm"
          aria-expanded={knowMoreOpen}
        >
          <div className="flex items-center gap-3">
            <span className="text-sm font-extrabold text-slate-900">
              {t("Know More & Portal Info", "और जानें (पोर्टल विवरण)")}
            </span>
            <span className="hidden sm:inline text-[11px] font-medium text-slate-500">
              {t("Portal details, revenue impact, schemes & ministers", "पोर्टल विवरण, राजस्व प्रभाव, योजनाएँ व मंत्री")}
            </span>
          </div>
          <ChevronDown
            className={`h-5 w-5 text-[#B85C00] transition-transform duration-300 ${knowMoreOpen ? "rotate-180" : ""}`}
          />
        </button>

        <div
          className={`grid transition-all duration-300 ${knowMoreOpen ? "grid-rows-[1fr] opacity-100 mt-4" : "grid-rows-[0fr] opacity-0"}`}
        >
          <div className="overflow-hidden space-y-6">
            <UpBhulekhPortalHero />
            <MunicipalRevenueCard />
            <DolrGovtSchemesAndMinisters />
          </div>
        </div>
      </section>

      {/* GOVERNMENT PARTNERS */}
      <GovtPartnersCarousel />
    </div>
  );
}