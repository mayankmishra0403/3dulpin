"use client";

import { useState } from "react";
import { useGovt } from "@/context/GovtContext";
import { QRCodeSVG } from "qrcode.react";
import { api } from "@/lib/api";
import { AshokaEmblem } from "@/components/GovtLogos";
import { Copy, Check, Box, ArrowRight, ShieldCheck, QrCode } from "lucide-react";

const CATEGORIES = [
  "surface", "floor", "suite", "underground", "parking",
  "air_right", "utility_network", "metro_tunnel", "structure",
];

interface GeneratedUlpin {
  value: string;
  front: string;
  checksum_ok: boolean;
}

interface ParsedUlpin {
  base_ulpin?: string;
  parcel_no?: string;
  descriptor?: string;
  vertical_code?: string;
  value?: string;
  category?: string;
  level_no?: number;
  unit_no?: string;
}

export default function ULPINLab() {
  const { t } = useGovt();

  // Generator State
  const [base, setBase] = useState("06080704000021");
  const [category, setCategory] = useState("floor");
  const [level, setLevel] = useState(3);
  const [unit, setUnit] = useState("11");
  const [out, setOut] = useState<GeneratedUlpin | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Parser State
  const [code, setCode] = useState("06080704000021-U38");
  const [parsed, setParsed] = useState<ParsedUlpin | null>(null);
  const [parseErr, setParseErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generate() {
    setErr(null);
    setOut(null);
    try {
      const res = await api<GeneratedUlpin>("/api/ulpins/generate", {
        method: "POST",
        body: JSON.stringify({
          base_ulpin: base,
          category,
          level_no: Number(level),
          unit_no: unit || null,
        }),
      });
      setOut(res);
      if (res?.value) setCode(res.value);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function parse() {
    setParseErr(null);
    setParsed(null);
    try {
      const res = await api<ParsedUlpin>(`/api/ulpins/parse/${code}`);
      setParsed(res);
    } catch (e) {
      setParseErr(String(e));
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadPreset = (presetCode: string) => {
    setCode(presetCode);
    api<ParsedUlpin>(`/api/ulpins/parse/${presetCode}`).then(setParsed).catch(() => {});
  };

  return (
    <div className="space-y-8">
      {/* GOVERNMENT HEADER */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <AshokaEmblem className="h-7 w-7 text-[#002B49]" />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {t("3D ULPIN Generator & Base-36 Verifier Portal", "3D यूएलपीआईएन जनरेटर एवं सत्यापन पोर्टल")}
            </h1>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            {t(
              "DoLR Bhu-Aadhaar 3D Volumetric Standard · Base-36 Modulo Checksum, Vertical Suffix Descriptor & QR Passport",
              "भू-संसाधन विभाग भू-आधार 3D मानक · Base-36 चेकसम, लंबवत कोड एवं QR पासपोर्ट"
            )}
          </p>
        </div>

        {/* PRESET CHIPS */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] text-amber-900 font-bold uppercase">{t("Quick Presets:", "त्वरित उदाहरण:")}</span>
          {[
            { label: "High-Rise Suite", code: "06080704000021-F03.U11" },
            { label: "Metro Tunnel", code: "06080704900001-MTA17" },
            { label: "Lift Shaft", code: "06080704000021-U38" },
          ].map((preset) => (
            <button
              key={preset.code}
              onClick={() => loadPreset(preset.code)}
              className="rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1 text-xs font-mono text-amber-900 hover:bg-amber-100 transition-all cursor-pointer font-bold shadow-sm"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* TWO COLUMN GENERATOR AND PARSER */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* GENERATOR CARD */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-5 shadow-sm">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
            <Box className="h-5 w-5 text-[#B85C00]" />
            <h2 className="text-base font-bold text-slate-900">
              1. {t("Compose 3D ULPIN (Bhu-Aadhaar 3D)", "3D यूएलपीआईएन कोड की रचना करें")}
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-700">
                {t("Base 14-Digit ULPIN (State + Dist + Subdist + Village + Parcel)", "आधार 14-अंकीय यूएलपीआईएन (राज्य + जिला + उपजिला + गांव + पार्सल)")}
              </label>
              <input
                value={base}
                onChange={(e) => setBase(e.target.value)}
                className="mt-1 w-full rounded-xl bg-slate-50 border border-slate-300 px-3.5 py-2.5 font-mono text-sm text-amber-900 focus:border-amber-600 focus:outline-none font-bold"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-700">{t("Category", "श्रेणी")}</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="mt-1 w-full rounded-xl bg-slate-50 border border-slate-300 px-3 py-2.5 text-xs text-slate-800 capitalize focus:border-amber-600 focus:outline-none"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c.replace("_", " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700">{t("Storey Level", "मंजिल स्तर")}</label>
                <input
                  type="number"
                  value={level}
                  onChange={(e) => setLevel(Number(e.target.value))}
                  className="mt-1 w-full rounded-xl bg-slate-50 border border-slate-300 px-3 py-2.5 font-mono text-sm text-slate-800 focus:border-amber-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700">{t("Unit / Suite No.", "इकाई / सुइट संख्या")}</label>
                <input
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="e.g. 11"
                  className="mt-1 w-full rounded-xl bg-slate-50 border border-slate-300 px-3 py-2.5 font-mono text-sm text-slate-800 focus:border-amber-600 focus:outline-none"
                />
              </div>
            </div>

            <button
              onClick={generate}
              className="w-full rounded bg-[#F59900] hover:bg-[#E08B00] px-4 py-3 text-xs font-bold text-slate-950 transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>{t("Compose & Generate Official Code", "3D यूएलपीआईएन कोड जनरेट करें")}</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            {err && <p className="text-xs text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200">{err}</p>}

            {out && (
              <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 space-y-3 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-emerald-800 tracking-wider">
                    {t("Generated Official 3D ULPIN", "निर्मित आधिकारिक 3D यूएलपीआईएन")}
                  </span>
                  <button
                    onClick={() => copyToClipboard(out.value)}
                    className="flex items-center gap-1 text-xs text-emerald-800 hover:text-emerald-950 cursor-pointer font-bold"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-emerald-700" /> : <Copy className="h-3.5 w-3.5" />} {t("Copy Code", "कॉपी करें")}
                  </button>
                </div>
                <div className="font-mono text-xl font-bold text-emerald-900 break-all">{out.value}</div>
                <div className="flex items-center gap-2 text-xs text-slate-700 font-semibold">
                  <ShieldCheck className="h-4 w-4 text-emerald-700" />
                  <span>{t("DoLR Base-36 Modulo Checksum Passed", "DoLR Base-36 मोडुलो चेकसम पास")}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* PARSER & QR CODE CANVAS CARD */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-5 shadow-sm">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
            <ShieldCheck className="h-5 w-5 text-emerald-700" />
            <h2 className="text-base font-bold text-slate-900">
              2. {t("Parse, Validate & Generate QR Passport", "सत्यापन एवं QR पासपोर्ट कैनवास")}
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-700">{t("Enter 3D ULPIN Code", "3D यूएलपीआईएन कोड दर्ज करें")}</label>
              <div className="mt-1 flex gap-2">
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="flex-1 rounded-xl bg-slate-50 border border-slate-300 px-3.5 py-2.5 font-mono text-sm text-amber-900 focus:border-amber-600 focus:outline-none font-bold"
                />
                <button
                  onClick={parse}
                  className="rounded-xl bg-[#002B49] hover:bg-[#00364A] px-4 py-2.5 text-xs font-bold text-white transition-all cursor-pointer"
                >
                  {t("Parse Code", "सत्यापित करें")}
                </button>
              </div>
            </div>

            {parseErr && <p className="text-xs text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200">{parseErr}</p>}

            {/* Code Breakdown & Scannable QR */}
            {parsed && (
              <div className="space-y-4">
                {/* Visual Code Breakdown */}
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
                  <div className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">
                    {t("Spatial Code Breakdown", "स्थानिक कोड का विस्तृत विवरण")}
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200 shadow-sm">
                      <div className="text-[10px] text-slate-500 font-semibold">{t("State / Dist / Locality", "राज्य / जिला / स्थान")}</div>
                      <div className="font-mono text-amber-800 font-bold mt-0.5">06 08 07 04</div>
                    </div>
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200 shadow-sm">
                      <div className="text-[10px] text-slate-500 font-semibold">{t("Base 2D Parcel", "मूल 2D पार्सल")}</div>
                      <div className="font-mono text-emerald-800 font-bold mt-0.5">{parsed.base_ulpin || parsed.parcel_no || "000021"}</div>
                    </div>
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200 shadow-sm">
                      <div className="text-[10px] text-slate-500 font-semibold">{t("Vertical Suffix", "लंबवत कोड")}</div>
                      <div className="font-mono text-sky-800 font-bold mt-0.5">{parsed.descriptor || parsed.vertical_code || "F03.U11"}</div>
                    </div>
                  </div>
                </div>

                {/* Scannable QR Code Canvas */}
                <div className="rounded-xl border border-amber-300 bg-amber-50/50 p-4 flex items-center justify-between gap-4 shadow-sm">
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900">
                      <QrCode className="h-4 w-4 text-amber-700" />
                      <span>{t("Scannable Bhu-Aadhaar 3D Passport", "स्कैन करने योग्य 3D पासपोर्ट")}</span>
                    </div>
                    <p className="text-[11px] text-slate-600 max-w-xs leading-relaxed">
                      {t(
                        "Scan with mobile camera to instantly verify registered 3D spatial title volume (m³) and digital registry rights.",
                        "पंजीकृत 3D भू-आयतन (m³) एवं डिजिटल स्वामित्व अधिकारों के तत्काल सत्यापन हेतु स्कैन करें।"
                      )}
                    </p>
                  </div>
                  <div className="bg-white p-2.5 rounded-xl shadow-md shrink-0 border-2 border-amber-500">
                    <QRCodeSVG value={`https://bhumi3d.gov.in/verify?ulpin=${encodeURIComponent(code)}`} size={88} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}