"use client";

import React, { useState } from "react";
import { useGovt } from "@/context/GovtContext";
import { Search, ShieldCheck, FileText, ArrowRight } from "lucide-react";
import Link from "next/link";

const DISTRICTS = [
  { id: "06", name_en: "Gurugram (06)", name_hi: "गुरुग्राम (06)" },
  { id: "09", name_en: "Gautam Buddha Nagar (Noida)", name_hi: "गौतम बुद्ध नगर (नोएडा)" },
  { id: "10", name_en: "Lucknow", name_hi: "लखनऊ" },
  { id: "12", name_en: "Varanasi", name_hi: "वाराणसी" },
];

const TEHSILS: Record<string, Array<{ id: string; name_en: string; name_hi: string }>> = {
  "06": [
    { id: "08", name_en: "Gurugram Sadar (08)", name_hi: "गुरुग्राम सदर (08)" },
    { id: "09", name_en: "Manesar", name_hi: "मानेसर" },
    { id: "10", name_en: "Pataudi", name_hi: "पटौदी" },
  ],
  "09": [
    { id: "01", name_en: "Dadbari", name_hi: "दादरी" },
    { id: "02", name_en: "Sadar Noida", name_hi: "सदर नोएडा" },
  ],
  "10": [
    { id: "01", name_en: "Lucknow Sadar", name_hi: "लखनऊ सदर" },
  ],
  "12": [
    { id: "01", name_en: "Varanasi Sadar", name_hi: "वाराणसी सदर" },
  ],
};

const VILLAGES: Record<string, Array<{ id: string; name_en: string; name_hi: string; ulpin_count: number }>> = {
  "08": [
    { id: "04", name_en: "DLF CyberCity / Sector 24 (Village 04)", name_hi: "डीएलएफ साइबरसिटी / सेक्टर 24 (ग्राम 04)", ulpin_count: 235 },
    { id: "05", name_en: "Sohna Road Urban", name_hi: "सोहना रोड अर्बन", ulpin_count: 142 },
    { id: "06", name_en: "Golf Course Extension", name_hi: "गोल्फ कोर्स एक्सटेंशन", ulpin_count: 189 },
  ],
  "01": [
    { id: "01", name_en: "Noida Sector 62", name_hi: "नोएडा सेक्टर 62", ulpin_count: 98 },
  ],
};

export function BhulekhSearchPanel() {
  const { t } = useGovt();

  const [selectedDistrict, setSelectedDistrict] = useState("06");
  const [selectedTehsil, setSelectedTehsil] = useState("08");
  const [selectedVillage, setSelectedVillage] = useState("04");

  const [searchTab, setSearchTab] = useState<"gata" | "khata" | "owner" | "ulpin">("ulpin");
  const [searchQuery, setSearchQuery] = useState("06080704000021-F03.U11");
  const [searchResult, setSearchResult] = useState<{
    ulpin3d: string;
    khasra_no: string;
    khata_no: string;
    owner_name: string;
    father_name: string;
    area_h: string;
    volume_m3: string;
    category: string;
    level: string;
    status: string;
  } | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchResult({
      ulpin3d: searchQuery || "06080704000021-F03.U11",
      khasra_no: "21/4 (गाटा संख्या 000021)",
      khata_no: "1048/A",
      owner_name: "आरव शर्मा / Aarav Sharma",
      father_name: "राजेश शर्मा / Rajesh Sharma",
      area_h: "0.0120 Hectare (120 m²)",
      volume_m3: "384.0 m³ (Level 3 Volumetric)",
      category: "Residential Suite (-F03.U11)",
      level: "Storey Floor 3 • Suite Unit 11",
      status: "Verified Un-encumbered (ऋणमुक्त पंजीकृत)",
    });
  };

  return (
    <div className="rounded-lg border border-slate-300 bg-white p-6 space-y-6 text-slate-900">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#F59900] text-slate-950 font-black text-lg shadow-sm">
            भू
          </div>
          <div>
            <span className="text-[11px] font-black uppercase tracking-wider text-amber-800">
              {t("State Revenue Department Land Portal", "राज्य राजस्व विभाग डिजिटल खतौनी पोर्टल")}
            </span>
            <h2 className="text-lg font-black text-slate-900">
              {t("Real-Time Khatauni 3D & Bhu-Aadhaar Search (यूपी भूलेख 3D)", "रियल-टाइम खतौनी 3D एवं गाटा / 3D यूएलपीआईएन खोज")}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold">
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
            {t("Direct UP Bhulekh Integration", "यूपी भूलेख एकीकृत प्रणाली")}
          </span>
        </div>
      </div>

      {/* 3-STEP SELECTION GRID: DISTRICT -> TEHSIL -> VILLAGE */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Step 1: Select District */}
        <div className="rounded-lg border border-slate-300 bg-[#FAFAF6] p-4 space-y-2">
          <div className="flex items-center justify-between font-black text-slate-900 border-b border-slate-200 pb-2">
            <span>1. {t("Select District (जनपद चुनें)", "जनपद चुनें")}</span>
            <span className="text-[10px] text-slate-500 font-bold">Step 1</span>
          </div>
          <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
            {DISTRICTS.map((d) => (
              <button
                key={d.id}
                onClick={() => {
                  setSelectedDistrict(d.id);
                  const tehsils = TEHSILS[d.id] || [];
                  if (tehsils.length > 0) setSelectedTehsil(tehsils[0].id);
                }}
                className={`w-full text-left px-3 py-2 rounded-lg font-bold transition-all ${
                  selectedDistrict === d.id
                    ? "bg-[#F59900] text-slate-950 shadow-sm"
                    : "text-slate-700 hover:bg-slate-200/60"
                }`}
              >
                {t(d.name_en, d.name_hi)}
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Select Tehsil */}
        <div className="rounded-lg border border-slate-300 bg-[#FAFAF6] p-4 space-y-2">
          <div className="flex items-center justify-between font-black text-slate-900 border-b border-slate-200 pb-2">
            <span>2. {t("Select Tehsil (तहसील चुनें)", "तहसील चुनें")}</span>
            <span className="text-[10px] text-slate-500 font-bold">Step 2</span>
          </div>
          <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
            {(TEHSILS[selectedDistrict] || []).map((th) => (
              <button
                key={th.id}
                onClick={() => {
                  setSelectedTehsil(th.id);
                  const villages = VILLAGES[th.id] || [];
                  if (villages.length > 0) setSelectedVillage(villages[0].id);
                }}
                className={`w-full text-left px-3 py-2 rounded-lg font-bold transition-all ${
                  selectedTehsil === th.id
                    ? "bg-[#F59900] text-slate-950 shadow-sm"
                    : "text-slate-700 hover:bg-slate-200/60"
                }`}
              >
                {t(th.name_en, th.name_hi)}
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Select Village */}
        <div className="rounded-lg border border-slate-300 bg-[#FAFAF6] p-4 space-y-2">
          <div className="flex items-center justify-between font-black text-slate-900 border-b border-slate-200 pb-2">
            <span>3. {t("Select Village / Locality (ग्राम चुनें)", "ग्राम चुनें")}</span>
            <span className="text-[10px] text-slate-500 font-bold">Step 3</span>
          </div>
          <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
            {(VILLAGES[selectedTehsil] || [
              { id: "04", name_en: "DLF CyberCity / Sector 24 (Village 04)", name_hi: "डीएलएफ साइबरसिटी / सेक्टर 24 (ग्राम 04)", ulpin_count: 235 },
            ]).map((v) => (
              <button
                key={v.id}
                onClick={() => setSelectedVillage(v.id)}
                className={`w-full text-left px-3 py-2 rounded-lg font-bold transition-all flex items-center justify-between ${
                  selectedVillage === v.id
                    ? "bg-[#F59900] text-slate-950 shadow-sm"
                    : "text-slate-700 hover:bg-slate-200/60"
                }`}
              >
                <span>{t(v.name_en, v.name_hi)}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200 font-bold">{v.ulpin_count} ULPINs</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* SEARCH TAB METHOD SELECTOR */}
      <div className="space-y-4 pt-2">
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
          <span className="text-xs font-black text-slate-700 mr-2">{t("Search Method:", "खोज प्रकार:")}</span>
          {[
            { id: "ulpin", label: t("3D ULPIN / Bhu-Aadhaar (3D यूएलपीआईएन)", "3D भू-आधार यूएलपीआईएन") },
            { id: "gata", label: t("Khasra / Gata No. (गाटा संख्या)", "खसरा / गाटा संख्या") },
            { id: "khata", label: t("Khata No. (खाता संख्या)", "खाता संख्या") },
            { id: "owner", label: t("Owner Name (खातेदार नाम)", "खातेदार का नाम") },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSearchTab(tab.id as typeof searchTab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                searchTab === tab.id
                  ? "bg-[#F59900] text-slate-950 shadow-sm"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* SEARCH INPUT FORM */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={
              searchTab === "ulpin"
                ? "Enter 14-digit 3D ULPIN (e.g. 06080704000021-F03.U11)..."
                : searchTab === "gata"
                ? "Enter Khasra / Gata No. (e.g. 000021)..."
                : searchTab === "khata"
                ? "Enter Khata No. (e.g. 1048)..."
                : "Enter Owner Name (e.g. Aarav Sharma)..."
            }
            className="flex-1 rounded bg-white border border-slate-300 px-4 py-2.5 text-xs text-slate-900 font-mono font-semibold focus:border-[#B85C00] focus:outline-none"
          />
          <button
            type="submit"
            className="rounded bg-[#F59900] hover:bg-[#e08b00] text-slate-950 font-bold px-6 py-2.5 text-xs transition-colors flex items-center gap-2 cursor-pointer"
          >
            <Search className="h-4 w-4" />
            <span>{t("Search Khatauni 3D", "खतौनी 3D खोजें")}</span>
          </button>
        </form>

        {/* SEARCH RESULT KHATAUNI 3D ROR CARD */}
        {searchResult && (
          <div className="rounded-lg border-2 border-emerald-300 bg-emerald-50/60 p-6 space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-emerald-200 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-6 w-6 text-emerald-700" />
                <h3 className="text-base font-black text-slate-900">
                  {t("Real-Time Khatauni 3D Record of Rights (RoR)", "रियल-टाइम अधिकार अभिलेख (खतौनी 3D की नकल)")}
                </h3>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-200 text-emerald-900 font-black text-xs border border-emerald-300">
                {searchResult.status}
              </span>
            </div>

            {/* Attributes Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="rounded bg-white p-3 border border-slate-300">
                <div className="text-[10px] text-slate-500 uppercase font-bold">{t("Registered Owner", "खातेदार का नाम")}</div>
                <div className="font-bold text-amber-800 mt-1">{searchResult.owner_name}</div>
              </div>

              <div className="rounded bg-white p-3 border border-slate-300">
                <div className="text-[10px] text-slate-500 uppercase font-bold">{t("Khasra / Gata No.", "खसरा / गाटा संख्या")}</div>
                <div className="font-mono text-emerald-800 font-bold mt-1">{searchResult.khasra_no}</div>
              </div>

              <div className="rounded bg-white p-3 border border-slate-300">
                <div className="text-[10px] text-slate-500 uppercase font-bold">{t("3D ULPIN Code", "3D यूएलपीआईएन कोड")}</div>
                <div className="font-mono text-blue-800 font-bold mt-1 break-all">{searchResult.ulpin3d}</div>
              </div>

              <div className="rounded bg-white p-3 border border-slate-300">
                <div className="text-[10px] text-slate-500 uppercase font-bold">{t("Volumetric Space", "3D घन आयतन")}</div>
                <div className="font-mono text-amber-900 font-bold mt-1">{searchResult.volume_m3}</div>
              </div>
            </div>

            {/* Quick Link to 3D Viewer & Certificate */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-emerald-200">
              <div className="text-xs text-slate-700">
                {t("Locality:", "स्थान:")} <strong className="text-slate-900">Gurugram 06080704 • Sector 24</strong>
              </div>
              <div className="flex gap-3">
                <Link
                  href={`/certificate?ulpin=${encodeURIComponent(searchResult.ulpin3d)}`}
                  className="inline-flex items-center gap-1.5 rounded bg-[#F59900] hover:bg-[#e08b00] text-slate-950 px-4 py-2 text-xs font-bold transition-colors"
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span>{t("View Title Passport", "भू-अधिकार प्रमाण पत्र देखें")}</span>
                </Link>

                <Link
                  href="/scene"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 text-xs font-bold transition-all"
                >
                  <span>{t("View Plot in 3D Map", "3D मानचित्र में प्लॉट देखें")}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
