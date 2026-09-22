"use client";

import Link from "next/link";
import { useGovt } from "@/context/GovtContext";
import { GovtTickerAndHero } from "@/components/GovtTickerAndHero";
import { UpBhulekhPortalHero } from "@/components/UpBhulekhPortalHero";
import { BhulekhSearchPanel } from "@/components/BhulekhSearchPanel";
import { GovtPartnersCarousel } from "@/components/GovtPartnersCarousel";
import { DolrGovtMetricsRow } from "@/components/DolrGovtMetricsRow";
import { DolrGovtSchemesAndMinisters } from "@/components/DolrGovtSchemesAndMinisters";
import { MunicipalRevenueCard } from "@/components/MunicipalRevenueCard";
import { ShieldAlert, ExternalLink } from "lucide-react";

export default function Dashboard() {
  const { t } = useGovt();

  return (
    <div className="space-y-8">
      {/* HERO + ANNOUNCEMENT TICKER */}
      <GovtTickerAndHero />

      {/* PORTAL DESCRIPTION & NAVIGATION CARDS */}
      <UpBhulekhPortalHero />

      {/* 3D KHATAUNI SEARCH */}
      <BhulekhSearchPanel />

      {/* GOVERNMENT PARTNERS */}
      <GovtPartnersCarousel />

      {/* NATIONAL LAND RECORDS METRICS */}
      <DolrGovtMetricsRow />

      {/* ACTIVE 3D SPATIAL CONFLICT NOTICE */}
      <div className="rounded-lg border border-[#C0392B] bg-[#FDEDEC] p-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="rounded bg-[#C0392B] p-3 text-white shrink-0">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-bold text-[#7B241C]">
                  {t("Active 3D Spatial Conflict", "सक्रिय 3D भू-स्थानिक अतिव्यापन")}
                </h3>
                <span className="rounded bg-[#C0392B] px-2 py-0.5 text-[10px] font-semibold text-white uppercase">
                  {t("Severity: High", "गंभीरता: उच्च")}
                </span>
              </div>
              <p className="text-xs text-[#7B241C] leading-relaxed">
                {t(
                  "Subsurface collision detected between Metro Transit Tunnel segment 06080704900001-MTA17 and High-Rise Lift Shaft 06080704000021-U38. Intersection volume ≈ 75.4 m³.",
                  "भूमिगत मेट्रो टनल खंड 06080704900001-MTA17 तथा उच्च-इमारत लिफ्ट शाफ्ट 06080704000021-U38 के बीच भूमिगत संघर्ष पाया गया। अतिव्याप्त घन आयतन लगभग 75.4 m³।"
                )}
              </p>
            </div>
          </div>

          <Link
            href="/scene"
            className="inline-flex items-center gap-1.5 rounded bg-[#C0392B] hover:bg-[#A93226] px-4 py-2.5 text-xs font-semibold text-white transition-colors shrink-0"
          >
            <span>{t("Inspect in 3D Map", "3D मानचित्र में जाँच करें")}</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* MUNICIPAL REVENUE & FISCAL IMPACT */}
      <MunicipalRevenueCard />

      {/* SCHEMES, ACTS & MINISTERS */}
      <DolrGovtSchemesAndMinisters />
    </div>
  );
}