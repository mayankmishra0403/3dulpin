"use client";

import dynamic from "next/dynamic";
import { useGovt } from "@/context/GovtContext";
import { MapPin, Shield } from "lucide-react";

const Scene = dynamic(() => import("@/components/Scene").then((m) => m.Scene), {
  ssr: false,
});

export default function ScenePage() {
  const { t } = useGovt();

  return (
    <section data-guide-step="scene-map" className="space-y-4 scroll-mt-24">
      {/* GOVT GIS MAP VIEWER HEADER */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-[#002B49]" />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {t("3D Volumetric Cadastre Map Viewer", "3D त्रि-आयामी भू-मानचित्र दर्शक")}
            </h1>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            {t(
              "DoLR Bhu-Aadhaar 3D Spatial Viewer • Drone Orthomosaic Layer (EPSG:32643 - UTM Zone 43N) • Orbit, Pan, and Filter Parcels",
              "भू-संसाधन विभाग 3D भू-मानचित्र • ड्रोन अर्थोमोज़ेक परत (EPSG:32643 - UTM ज़ोन 43N) • ऑर्बिट व फ़िल्टर पार्सल"
            )}
          </p>
        </div>

        {/* Map Metadata Chips */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="rounded-xl bg-amber-50 border border-amber-200 px-3 py-1.5 font-mono text-amber-900 flex items-center gap-1.5 font-bold">
            <MapPin className="h-3.5 w-3.5 text-amber-700" />
            <span>Locality: 06080704 (Gurugram)</span>
          </div>
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 px-3 py-1.5 font-mono text-emerald-900 font-bold">
            CRS: EPSG:32643
          </div>
        </div>
      </div>

      <Scene />
    </section>
  );
}