"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";
import { MapPin, Building2, Map, FileText, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";

export function UpBhulekhPortalHero() {
  const { t } = useGovt();

  const items = [
    { title_en: "District", title_hi: "जिला", icon: MapPin, href: "/ulpin" },
    { title_en: "Tehsil", title_hi: "तहसील", icon: Building2, href: "/ulpin" },
    { title_en: "Pargana / 3D ULPIN", title_hi: "परगना / 3D ULPIN", icon: Map, href: "/ulpin", accent: true },
    { title_en: "Land Categories", title_hi: "भूमि प्रकार की सूची", icon: FileText, href: "/ulpin" },
    { title_en: "Search Govt 3D Land", title_hi: "सरकारी 3D भूमि खोजें", icon: Search, href: "/ulpin" },
    { title_en: "Cyber Security Guidelines", title_hi: "साइबर सिक्योरिटी गाइडलाइन्स", icon: ShieldCheck, href: "/ulpin" },
  ];

  return (
    <div className="w-full bg-[#EEF4F8] py-8 border-b border-slate-300">
      <div className="max-w-7xl mx-auto px-4 lg:px-12 space-y-6">
        <div className="bg-white border border-slate-300 p-6 text-xs sm:text-sm text-slate-700 leading-relaxed">
          <p>
            {t(
              "Bhulekh portal is the official digital land records portal of the Revenue Department, where citizens can inspect land records, plot disputes, sales, 3D Bhu-Naksha and mutation registers using the 14-digit ULPIN (Bhu-Aadhaar). All land parcel data has been digitized and is available to citizens online.",
              "भूलेख पोर्टल राजस्व विभाग का आधिकारिक डिजिटल भूमि अभिलेख पोर्टल है, जहाँ नागरिक 14-अंकीय ULPIN (भू-आधार) के माध्यम से भूमि अभिलेख, गाटा के वाद, विक्रय, 3D भू-नक्शा एवं नामांतरण बही का अवलोकन कर सकते हैं। राज्य की सभी भूमि का डाटा डिजिटलीकृत कर नागरिकों हेतु ऑनलाइन उपलब्ध कराया गया है।"
            )}
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {items.map((c) => {
            const Icon = c.icon;
            return (
              <Link
                key={c.title_en}
                href={c.href}
                className={`rounded-lg border p-5 flex flex-col items-center justify-center text-center gap-3 min-h-[120px] transition-colors ${
                  c.accent
                    ? "bg-[#FFF6E6] border-[#F59900]"
                    : "bg-white border-slate-300 hover:border-[#B85C00]"
                }`}
              >
                <Icon className={`h-7 w-7 ${c.accent ? "text-[#B85C00]" : "text-[#002B49]"}`} />
                <span className="font-semibold text-slate-900 text-xs sm:text-sm leading-snug">
                  {t(c.title_en, c.title_hi)}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}