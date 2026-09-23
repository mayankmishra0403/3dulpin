"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useGovt } from "@/context/GovtContext";
import {
  Compass,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  X,
  MapPin,
  ExternalLink,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

type GuideStep = {
  id: string;
  route: string;
  title: string;
  narrativeEn: string;
  narrativeHi: string;
  target?: string;
  pageNameEn: string;
  pageNameHi: string;
};

const TOUR_STEPS: GuideStep[] = [
  {
    id: "welcome",
    route: "/",
    title: "1. National 3D Bhu-Aadhaar Portal",
    narrativeEn:
      "Welcome to India's official 3D Bhu-Aadhaar Portal under DILRMP. This portal extends 2D land records to 3D volumetric property titles covering multi-storey floors, basements, and subsurface transit tunnels.",
    narrativeHi:
      "डीआईएलआरएमपी के अंतर्गत भारत के आधिकारिक 3D भू-आधार पोर्टल में आपका स्वागत है। यह पोर्टल 2D भूमि अभिलेखों को बहुमंजिला मंजिलों, बेसमेंट एवं भूमिगत टनल सहित 3D वॉल्यूमेट्रिक अधिकारों तक विस्तारित करता है।",
    target: '[data-guide-step="explore3d"]',
    pageNameEn: "Main Dashboard",
    pageNameHi: "मुख्य डैशबोर्ड",
  },
  {
    id: "search",
    route: "/",
    title: "2. 3D Khatauni & Plot Search",
    narrativeEn:
      "Search land records by District, Tehsil, Village, Gata No., or 14-digit 3D ULPIN code to pull real-time Record of Rights (RoR) with volumetric dimensions.",
    narrativeHi:
      "जनपद, तहसील, ग्राम, गाटा संख्या या 14-अंकीय 3D ULPIN द्वारा वास्तविक समय खतौनी 3D अधिकार अभिलेख खोजें।",
    target: '[data-guide-step="search"]',
    pageNameEn: "Main Dashboard",
    pageNameHi: "मुख्य डैशबोर्ड",
  },
  {
    id: "conflict",
    route: "/",
    title: "3. 3D Spatial Conflict Alert",
    narrativeEn:
      "Detect overlapping 3D volumes (e.g. metro transit tunnels vs high-rise lift shafts) in real time with spatial collision volume calculation.",
    narrativeHi:
      "भूमिगत मेट्रो टनल एवं बहुमंजिला लिफ्ट शाफ्ट के बीच 3D भू-स्थानिक अतिव्याप्ति (Collision) की रियल-टाइम जाँच करें।",
    target: '[data-guide-step="conflict"]',
    pageNameEn: "Main Dashboard",
    pageNameHi: "मुख्य डैशबोर्ड",
  },
  {
    id: "map-viewer",
    route: "/scene",
    title: "4. 3D Volumetric Cadastre Viewer",
    narrativeEn:
      "Explore the full city in interactive 3D! Orbit, filter by surface, floors, suites, underground metro corridors, and explode floor levels to inspect multi-storey suites.",
    narrativeHi:
      "त्रि-आयामी भू-मानचित्र दर्शक me poora shehar 3D me dekhein! Orbit, surface, floors, suites, underground metro corridors, aur floor explode filters use karein.",
    target: '[data-guide-step="scene-map"]',
    pageNameEn: "3D Map Viewer Page",
    pageNameHi: "3D भू-मानचित्र दर्शक पेज",
  },
  {
    id: "ulpin-lab",
    route: "/ulpin",
    title: "5. 3D ULPIN Lab & Base-36 Verification",
    narrativeEn:
      "Generate 14-digit volumetric ULPIN codes with vertical storey descriptors (e.g. -F03.U11), validate Base-36 checksums, and view scannable QR passports.",
    narrativeHi:
      "3D ULPIN जनरेटर एवं सत्यापन लैब me 14-अंकीय लंबवत कोड निर्मित करें, Base-36 चेकसम सत्यापित करें एवं QR कोड पासपोर्ट देखें।",
    target: '[data-guide-step="ulpin-generator"]',
    pageNameEn: "3D ULPIN Lab Page",
    pageNameHi: "3D ULPIN लैब पेज",
  },
  {
    id: "spatial-audit",
    route: "/validation",
    title: "6. AI Remote Sensing & Spatial Audit",
    narrativeEn:
      "Compare drone orthophotos, nDSM heightmaps, and point-cloud 3D reconstructions with automated building match IoU accuracy scoring.",
    narrativeHi:
      "ड्रोन अर्थोफोटो, nDSM ऊंचाई मानचित्र एवं 3D पॉइंट-क्लाउड रीकंस्ट्रक्शन की तुलना AI ऑटोमेटेड IoU सटीकता स्कोरिंग के साथ करें।",
    target: '[data-guide-step="validation-raster"]',
    pageNameEn: "Spatial Audit Page",
    pageNameHi: "स्थानिक ऑडिट पेज",
  },
  {
    id: "land-passport",
    route: "/certificate",
    title: "7. Bhu-Aadhaar Land Passport Certificate",
    narrativeEn:
      "View and print official 3D land title passports containing registered volumetric bounds (z-min, z-max, m³ volume) and QR verification seal.",
    narrativeHi:
      "पंजीकृत 3D भू-आयतन (z-min, z-max, m³) एवं QR डिजिटल मुहर युक्त आधिकारिक भू-आधार 3D संपत्ति पासपोर्ट देखें व प्रिंट करें।",
    target: '[data-guide-step="certificate-passport"]',
    pageNameEn: "Land Passport Page",
    pageNameHi: "भू-पासपोर्ट पेज",
  },
];

export function VoiceGuide() {
  const { t } = useGovt();
  const router = useRouter();
  const pathname = usePathname();

  const [open, setOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const highlightRef = useRef<HTMLElement | null>(null);

  const clearHighlight = useCallback(() => {
    if (highlightRef.current) {
      highlightRef.current.classList.remove("guide-step-active");
      highlightRef.current = null;
    }
  }, []);

  const highlightStepTarget = useCallback(
    (targetSelector?: string) => {
      clearHighlight();
      if (!targetSelector) return;
      setTimeout(() => {
        const el = document.querySelector<HTMLElement>(targetSelector);
        if (el) {
          el.classList.add("guide-step-active");
          highlightRef.current = el;
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 250);
    },
    [clearHighlight]
  );

  const goToStep = useCallback(
    (idx: number) => {
      const step = TOUR_STEPS[idx];
      if (!step) return;

      setStepIndex(idx);

      if (pathname !== step.route) {
        router.push(step.route);
      } else {
        highlightStepTarget(step.target);
      }
    },
    [pathname, router, highlightStepTarget]
  );

  // Automatically trigger element highlight after route transition
  useEffect(() => {
    if (!open) return;
    const currentStep = TOUR_STEPS[stepIndex];
    if (currentStep && pathname === currentStep.route) {
      highlightStepTarget(currentStep.target);
    }
  }, [pathname, stepIndex, open, highlightStepTarget]);

  const handleToggleOpen = () => {
    if (open) {
      clearHighlight();
      setOpen(false);
    } else {
      setOpen(true);
      goToStep(stepIndex);
    }
  };

  const handleClose = () => {
    clearHighlight();
    setOpen(false);
  };

  useEffect(() => {
    return () => {
      clearHighlight();
    };
  }, [clearHighlight]);

  const currentStep = TOUR_STEPS[stepIndex];

  return (
    <>
      {/* FLOATING TOUR GUIDE BUTTON */}
      <button
        onClick={handleToggleOpen}
        className="fixed bottom-6 left-6 z-[60] h-14 px-4 rounded-full bg-gradient-to-r from-[#002B49] via-[#00364A] to-[#004B6E] text-white shadow-xl flex items-center gap-2.5 hover:scale-105 active:scale-95 transition-all cursor-pointer border-2 border-[#F59900]"
        aria-label="Interactive Website Guide"
        title="Interactive Website Guide Tour"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#F59900] text-slate-950 font-black shrink-0 shadow-sm">
          <Compass className="h-5 w-5 animate-spin" style={{ animationDuration: "12s" }} />
        </div>
        <div className="text-left font-bold text-xs pr-1 hidden sm:block">
          <div>{t("Website Tour Guide", "वेबसाइट गाइड टूर")}</div>
          <div className="text-[10px] text-[#F59900] font-mono">
            {open ? `Step ${stepIndex + 1}/${TOUR_STEPS.length}` : t("Interactive Tour", "इंटरएक्टिव टूर")}
          </div>
        </div>
      </button>

      {/* TOUR CARD OVERLAY */}
      {open && (
        <div className="fixed bottom-24 left-4 sm:left-6 z-[60] w-[clamp(290px,28rem,calc(100vw-2rem))] rounded-2xl bg-white border border-slate-200/90 shadow-2xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
          {/* Header */}
          <div className="relative bg-gradient-to-r from-[#002B49] via-[#00364A] to-[#004B6E] px-5 pt-5 pb-4 text-white">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="h-9 w-9 rounded-xl bg-[#F59900] text-slate-950 font-black flex items-center justify-center shadow-md shrink-0">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[#F59900] font-black">
                    Interactive Website Guide
                  </p>
                  <h3 className="text-sm font-extrabold leading-tight mt-0.5">
                    {currentStep.title}
                  </h3>
                </div>
              </div>

              <button
                onClick={handleClose}
                className="rounded-full p-1.5 hover:bg-white/10 transition-colors cursor-pointer text-slate-300 hover:text-white"
                aria-label="Close guide"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Step Progress Pills Bar */}
            <div className="mt-3 flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
              {TOUR_STEPS.map((s, idx) => (
                <button
                  key={s.id}
                  onClick={() => goToStep(idx)}
                  className={`h-2 rounded-full transition-all cursor-pointer ${
                    idx === stepIndex
                      ? "w-6 bg-[#F59900]"
                      : idx < stepIndex
                      ? "w-2.5 bg-emerald-400"
                      : "w-2.5 bg-white/30 hover:bg-white/50"
                  }`}
                  title={s.title}
                />
              ))}
            </div>
          </div>

          {/* Body Content */}
          <div className="p-4 space-y-3 bg-slate-50/80">
            {/* Page Context Badge */}
            <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 border-b border-slate-200 pb-2">
              <span className="flex items-center gap-1 text-[#002B49]">
                <MapPin className="h-3.5 w-3.5 text-[#F59900]" />
                {t("Page:", "पेज:")}{" "}
                <strong className="text-slate-900">{t(currentStep.pageNameEn, currentStep.pageNameHi)}</strong>
              </span>
              <span className="font-mono text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                Step {stepIndex + 1} / {TOUR_STEPS.length}
              </span>
            </div>

            {/* Narrative Box */}
            <div className="rounded-xl bg-white border border-slate-200 p-3.5 text-xs sm:text-sm text-slate-800 leading-relaxed shadow-sm font-medium">
              {t(currentStep.narrativeEn, currentStep.narrativeHi)}
            </div>

            {/* Action Navigation Controls */}
            <div className="flex items-center justify-between gap-2 pt-1">
              <button
                onClick={() => goToStep(Math.max(0, stepIndex - 1))}
                disabled={stepIndex === 0}
                className="inline-flex items-center gap-1 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-40 cursor-pointer transition-colors shadow-sm"
              >
                <ChevronLeft className="h-4 w-4" /> {t("Prev", "पिछला")}
              </button>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => goToStep(0)}
                  className="inline-flex items-center gap-1 rounded-xl px-2.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200 transition-colors cursor-pointer"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">{t("Restart", "पुनः प्रारंभ")}</span>
                </button>
              </div>

              <button
                onClick={() => goToStep(Math.min(TOUR_STEPS.length - 1, stepIndex + 1))}
                disabled={stepIndex === TOUR_STEPS.length - 1}
                className="inline-flex items-center gap-1 rounded-xl bg-[#F59900] hover:bg-[#e08b00] px-4 py-2 text-xs font-black text-slate-950 transition-all cursor-pointer shadow-sm disabled:opacity-40"
              >
                <span>{stepIndex === TOUR_STEPS.length - 1 ? t("Finish", "समाप्त") : t("Next Step", "अगला")}</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}