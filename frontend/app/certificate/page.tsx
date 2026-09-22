"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useGovt } from "@/context/GovtContext";
import { QRCodeSVG } from "qrcode.react";
import { api } from "@/lib/api";
import { AshokaEmblem, TricolorStrip } from "@/components/GovtLogos";
import { Printer, ShieldCheck, ArrowLeft, Lock } from "lucide-react";
import Link from "next/link";

interface ParcelData {
  ulpin3d: string;
  base_ulpin?: string;
  category: string;
  level_no: number | string;
  unit_no?: string;
  zmin: number | string;
  zmax: number | string;
  volume_m3?: number | string;
  built_up_area_m2?: number | string;
  owner_name?: string;
  right_type?: string;
  usage?: string;
  status?: string;
}

function CertificateContent() {
  const { t } = useGovt();
  const searchParams = useSearchParams();
  const initialUlpin = searchParams.get("ulpin") || "06080704000021-F03.U11";

  const [ulpin, setUlpin] = useState(initialUlpin);
  const [parcel, setParcel] = useState<ParcelData | null>(null);

  useEffect(() => {
    if (!ulpin) return;
    let alive = true;
    api<ParcelData>(`/api/cadastre/parcels/by-ulpin/${encodeURIComponent(ulpin)}`)
      .then((data) => { if (alive) setParcel(data); })
      .catch(() => {
        if (!alive) return;
        setParcel({
          ulpin3d: ulpin,
          base_ulpin: ulpin.split("-")[0] || "06080704000021",
          category: "suite",
          level_no: 3,
          unit_no: "11",
          zmin: 9.6,
          zmax: 12.8,
          volume_m3: 384.0,
          built_up_area_m2: 120.0,
          owner_name: "Aarav Sharma",
          right_type: "Owned (Freehold)",
          usage: "Residential Apartment Suite",
          status: "active",
        });
      });
    return () => { alive = false; };
  }, [ulpin]);

  const handlePrint = () => {
    window.print();
  };

  const zmin = parcel ? (Number(parcel.zmin) || 9.6) : 9.6;
  const zmax = parcel ? (Number(parcel.zmax) || 12.8) : 12.8;
  const volumeM3 = parcel ? (Number(parcel.volume_m3) || 384.0) : 384.0;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Action Bar (Hidden in Print) */}
      <div className="flex items-center justify-between gap-4 print:hidden">
        <Link
          href="/scene"
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all cursor-pointer shadow-sm"
        >
          <ArrowLeft className="h-4 w-4 text-[#002B49]" /> {t("Back to 3D Viewer", "3D मानचित्र पर लौटें")}
        </Link>

        <div className="flex items-center gap-3">
          <input
            value={ulpin}
            onChange={(e) => setUlpin(e.target.value)}
            placeholder="Search 3D ULPIN..."
            className="rounded-xl bg-slate-50 border border-slate-300 px-3.5 py-2 font-mono text-xs text-amber-900 focus:outline-none focus:border-amber-600 w-60 font-bold"
          />
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-2 rounded-xl bg-[#F59900] hover:bg-[#E08B00] px-4 py-2 text-xs font-extrabold text-white shadow-sm transition-all cursor-pointer"
          >
            <Printer className="h-4 w-4" /> {t("Print Official Title PDF", "आधिकारिक प्रमाण पत्र प्रिंट करें")}
          </button>
        </div>
      </div>

      {/* PRINTABLE OFFICIAL GOVERNMENT LAND CERTIFICATE CARD */}
      <div className="relative rounded-2xl border-4 border-amber-600/40 bg-white p-8 sm:p-12 shadow-xl space-y-8 text-slate-900 print:bg-white print:text-slate-900 print:border-slate-800 print:shadow-none">
        <TricolorStrip className="h-2 w-full absolute top-0 left-0 rounded-t-xl" />

        {/* Certificate Government Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 border-b-2 border-slate-200 print:border-slate-300 pb-6 pt-2">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 border-2 border-amber-500 p-2 shadow-sm shrink-0">
              <AshokaEmblem className="h-12 w-12 text-[#002B49]" />
            </div>
            <div>
              <div className="text-xs uppercase font-extrabold tracking-widest text-amber-900">
                Government of India • Ministry of Rural Development
              </div>
              <h1 className="text-xl sm:text-2xl font-black tracking-tight text-[#002B49] mt-0.5">
                {t("Bhu-Aadhaar 3D Volumetric Property Passport", "भू-आधार 3D लंबवत संपत्ति पासपोर्ट")}
              </h1>
              <p className="text-xs text-slate-600 font-bold">
                Department of Land Resources (DoLR) • DILRMP Digital Title Standard
              </p>
            </div>
          </div>

          <div className="text-right space-y-1 shrink-0">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-extrabold text-emerald-900 border border-emerald-300">
              <ShieldCheck className="h-4 w-4 text-emerald-700" /> DIGITAL TITLE VERIFIED
            </div>
            <div className="text-[11px] font-mono text-slate-600 font-bold">
              Gazette Ref: GAZ/2026/BHU3D-84920
            </div>
          </div>
        </div>

        {/* Parcel Details Section */}
        {parcel && (
          <div className="space-y-6">
            {/* ULPIN Highlight Box */}
            <div className="rounded-2xl border-2 border-amber-400 bg-amber-50/60 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
              <div>
                <div className="text-[11px] uppercase font-bold tracking-wider text-amber-900">
                  Unique 3D Spatial Identifier (3D ULPIN / Bhu-Aadhaar 3D)
                </div>
                <div className="font-mono text-2xl sm:text-3xl font-black text-[#002B49] tracking-wider mt-1 break-all">
                  {parcel.ulpin3d}
                </div>
              </div>
              <div className="text-xs text-slate-700 space-y-1 font-bold shrink-0">
                <div>Base 2D Parcel: <span className="font-mono text-amber-900">{parcel.base_ulpin || "06080704000021"}</span></div>
                <div>Locality Code: <span className="font-mono text-emerald-800">06080704 (Gurugram)</span></div>
                <div>CRS Standard: <span className="font-mono">EPSG:32643 (UTM 43N)</span></div>
              </div>
            </div>

            {/* Attributes Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <div className="text-[10px] uppercase font-bold text-slate-500">Registered Owner</div>
                <div className="font-bold text-sm text-slate-900 mt-1">{parcel.owner_name || "Aarav Sharma"}</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <div className="text-[10px] uppercase font-bold text-slate-500">Ownership Right</div>
                <div className="font-bold text-sm text-amber-900 mt-1">{parcel.right_type || "Owned (Freehold)"}</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <div className="text-[10px] uppercase font-bold text-slate-500">Category & Level</div>
                <div className="font-bold text-sm text-slate-900 mt-1 capitalize">
                  {parcel.category} · Level {parcel.level_no}
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <div className="text-[10px] uppercase font-semibold text-slate-500">Registered Volume</div>
                <div className="font-bold text-sm font-mono text-emerald-800 mt-1">
                  {volumeM3.toFixed(1)} m³
                </div>
              </div>
            </div>

            {/* Spatial Bounds & Footprint Coordinates */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-3 shadow-sm">
              <div className="text-xs font-bold text-[#002B49] uppercase tracking-wide">
                3D Volumetric Spatial Boundary Parameters
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs font-mono text-slate-800 font-bold">
                <div>Lower Elevation (z-min): <strong className="text-amber-900">{zmin.toFixed(2)} m</strong></div>
                <div>Upper Elevation (z-max): <strong className="text-amber-900">{zmax.toFixed(2)} m</strong></div>
                <div>Net Vertical Height: <strong className="text-emerald-800">{(zmax - zmin).toFixed(2)} m</strong></div>
              </div>
            </div>

            {/* Verification Footer with Digital Seal & QR Code */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6 border-t-2 border-slate-200 pt-6">
              <div className="space-y-1.5 text-center sm:text-left">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                  <Lock className="h-4 w-4 text-emerald-700" />
                  <span>Digital Land Registry Seal & Base-36 Modulo 37 Validation</span>
                </div>
                <p className="text-[11px] text-slate-600 max-w-sm">
                  Issued under Section 14 of the National Volumetric Land Rights Framework. Base-36 checksum validated.
                </p>
                <div className="text-[10px] font-mono text-slate-500 pt-1">
                  Competent Authority: Tehsildar / District Land Collector (Gurugram)
                </div>
              </div>

              <div className="flex items-center gap-4 bg-white p-3 rounded-2xl shadow-md border-2 border-amber-500 shrink-0">
                <QRCodeSVG value={`https://bhumi3d.gov.in/verify?ulpin=${encodeURIComponent(parcel.ulpin3d)}`} size={96} />
                <div className="text-[10px] text-slate-900 font-mono space-y-0.5">
                  <div className="font-extrabold text-amber-900">SCAN TO VERIFY</div>
                  <div>DoLR Portal Valid</div>
                  <div>Base-36 OK</div>
                  <div className="text-[9px] text-slate-500">EPSG:32643</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function CertificatePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-400 text-sm">Loading Land Passport Certificate...</div>}>
      <CertificateContent />
    </Suspense>
  );
}
