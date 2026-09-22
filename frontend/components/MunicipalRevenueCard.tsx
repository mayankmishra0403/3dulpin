"use client";

import { useState } from "react";
import { useGovt } from "@/context/GovtContext";
import { TrendingUp, IndianRupee } from "lucide-react";

type TierKey = "all" | "residential" | "commercial" | "air_rights";

export function MunicipalRevenueCard() {
  const [selectedTier, setSelectedTier] = useState<TierKey>("all");
  const { t } = useGovt();

  const tierStats: Record<TierKey, { flat2d: string; vol3d: string; uplift: string; extra: string }> = {
    all: {
      flat2d: "42.5 Lakhs",
      vol3d: "1.84 Crores",
      uplift: "+333%",
      extra: t("₹1.41 Cr unregistered revenue unlocked", "₹1.41 करोड़ अप्रत्यक्ष राजस्व अनलॉक"),
    },
    residential: {
      flat2d: "28.0 Lakhs",
      vol3d: "94.2 Lakhs",
      uplift: "+236%",
      extra: t("235 multi-storey suite units registered", "235 बहुमंजिला अपार्टमेंट इकाइयाँ पंजीकृत"),
    },
    commercial: {
      flat2d: "14.5 Lakhs",
      vol3d: "62.8 Lakhs",
      uplift: "+333%",
      extra: t("Retail podiums & underground parking", "रिटेल पोडियम व भूमिगत पार्किंग"),
    },
    air_rights: {
      flat2d: "0.0 Lakhs",
      vol3d: "27.0 Lakhs",
      uplift: "∞ NEW",
      extra: t("Helipad & upper-air rights taxation", "हेलीपैड व ऊपरी-वायु अधिकार कराधान"),
    },
  };

  const curr = tierStats[selectedTier];

  return (
    <div className="rounded-lg border border-slate-300 bg-white p-6 space-y-5 text-slate-900">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-emerald-100 p-3 text-emerald-800 border border-emerald-300">
            <IndianRupee className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[11px] uppercase font-black tracking-wider text-emerald-800">
              {t("Municipal Revenue & Fiscal Impact", "नगर निगम राजस्व एवं वित्तीय प्रभाव")}
            </span>
            <h2 className="text-base font-black text-slate-900">
              {t("3D Volumetric Property Tax & Revenue Simulator", "3D वॉल्यूमेट्रिक संपत्ति कर एवं राजस्व सिमुलेटर")}
            </h2>
          </div>
        </div>

        {/* Tier Selector */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-300 text-xs">
          {[
            { id: "all", label: t("Total Locality", "संपूर्ण क्षेत्र") },
            { id: "residential", label: t("Residential", "आवासीय") },
            { id: "commercial", label: t("Commercial", "व्यावसायिक") },
            { id: "air_rights", label: t("Air Rights", "वायु अधिकार") },
          ].map((tier) => (
            <button
              key={tier.id}
              onClick={() => setSelectedTier(tier.id as TierKey)}
              className={`rounded px-3 py-1 font-bold transition-all cursor-pointer ${
                selectedTier === tier.id ? "bg-emerald-700 text-white shadow-sm" : "text-slate-700 hover:text-slate-900"
              }`}
            >
              {tier.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* 2D Flat Tax */}
        <div className="rounded-lg border border-slate-300 bg-slate-50 p-4 space-y-1.5">
          <div className="text-[10px] uppercase font-black text-slate-600">
            {t("Traditional 2D Flat Tax", "पारंपरिक 2D समतल कर")}
          </div>
          <div className="text-xl font-black font-mono text-slate-800">₹{curr.flat2d}</div>
          <div className="text-[11px] text-slate-600 font-medium">
            {t("Assesses surface plot footprint only", "केवल भू-सतह भूखंड का मूल्यांकन")}
          </div>
        </div>

        {/* 3D Volumetric Tax */}
        <div className="rounded-lg border-2 border-emerald-300 bg-emerald-50 p-4 space-y-1.5 shadow-sm">
          <div className="text-[10px] uppercase font-black text-emerald-900 tracking-wider">
            {t("3D Volumetric Tax Assessment", "3D वॉल्यूमेट्रिक संपत्ति कर")}
          </div>
          <div className="text-xl font-black font-mono text-emerald-800">₹{curr.vol3d}</div>
          <div className="text-[11px] text-emerald-950 font-bold">
            {t("Assesses floor levels, suites & voids", "मंजिलों, सुइटों व शून्य क्षेत्र का मूल्यांकन")}
          </div>
        </div>

        {/* Revenue Uplift Badge */}
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 space-y-1.5">
          <div className="text-[10px] uppercase font-black text-amber-900 tracking-wider">
            {t("Municipal Revenue Yield Uplift", "नगर निगम राजस्व वृद्धि")}
          </div>
          <div className="text-xl font-black font-mono text-amber-800 flex items-center gap-1">
            <TrendingUp className="h-5 w-5 text-amber-700" /> {curr.uplift}
          </div>
          <div className="text-[11px] text-amber-950 font-bold">{curr.extra}</div>
        </div>
      </div>
    </div>
  );
}
