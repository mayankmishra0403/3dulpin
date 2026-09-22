"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";
import { ArrowUp } from "lucide-react";
import Link from "next/link";

export function DolrGovtSchemesAndMinisters() {
  const { t } = useGovt();

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="w-full bg-white py-10 border-b border-slate-300 relative">
      <div className="max-w-7xl mx-auto px-4 lg:px-12 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT 2 COLUMNS: SCHEMES & ACTS */}
        <div className="lg:col-span-2 space-y-8">
          {/* Section 1: Schemes */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900 border-b-2 border-slate-300 pb-2">
              {t("Schemes & Programs", "योजनाओं")}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#FAFAF8] border border-slate-300 rounded-lg p-5 space-y-3">
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  {t(
                    "Digital India Land Records Modernization Programme (DILRMP)",
                    "डिजिटल इंडिया भूमि अभिलेख आधुनिकीकरण कार्यक्रम (डी.आई.एल.आर.एम.पी.)"
                  )}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {t(
                    "Volumetric 3D spatial cadastre with 14-digit Bhu-Aadhaar ULPIN assignment to multi-storey floors, basements and subsurface transit corridors.",
                    "3D भू-मानचित्रण एवं 14-अंकीय भू-आधार (ULPIN) द्वारा बहुमंजिला इमारतों, बेसमेंट व भूमिगत संपत्तियों का डिजिटल पंजीकरण।"
                  )}
                </p>
                <Link href="/scene" className="inline-block text-xs font-semibold text-[#B85C00] hover:underline">
                  {t("View 3D Cadastre", "3D भू-मानचित्र देखें")}
                </Link>
              </div>

              <div className="bg-[#FAFAF8] border border-slate-300 rounded-lg p-5 space-y-3">
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  {t(
                    "Watershed Development Component - PMKSY 2.0",
                    "वाटरशेड विकास घटक - पीएमकेएसवाई 2.0"
                  )}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {t(
                    "Soil and water conservation, watershed management and rainfed area development across rural districts.",
                    "मृदा व जल संरक्षण, वाटरशेड प्रबंधन एवं वर्षा आधारित क्षेत्रों का विकास।"
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Acts */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900 border-b-2 border-slate-300 pb-2">
              {t("Acts & Rules", "अधिनियम")}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#FAFAF8] border border-slate-300 rounded-lg p-5 space-y-3">
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  {t("Registration Act, 1908", "पंजीकरण अधिनियम, 1908")}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {t(
                    "Framework governing computerized registration of multi-storey floor units, suites and 3D volumetric land titles.",
                    "कंप्यूटरीकृत संपत्ति पंजीकरण, बहुमंजिला इकाइयों एवं 3D भू-अधिकारों का विधिक ढांचा।"
                  )}
                </p>
              </div>

              <div className="bg-[#FAFAF8] border border-slate-300 rounded-lg p-5 space-y-3">
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  {t("RFCTLARR Act, 2013 (Land Acquisition)", "आर.एफ.सी.टी.एल.ए.आर.आर., 2013")}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {t(
                    "Right to Fair Compensation and Transparency in Land Acquisition, Rehabilitation and Resettlement Act.",
                    "भूमि अधिग्रहण, पुनर्वास और पुनर्व्यवस्थापन में उचित प्रतिकर और पारदर्शिता का अधिकार अधिनियम।"
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT 1 COLUMN: MINISTER PROFILES */}
        <div className="space-y-6">
          <h2 className="text-lg font-bold text-slate-900 border-b-2 border-slate-300 pb-2">
            {t("Minister Profiles", "मंत्री प्रोफ़ाइल")}
          </h2>

          <div className="space-y-8">
            <div className="text-center space-y-3">
              <div className="mx-auto h-24 w-24 rounded-full bg-[#002B49] text-[#F59900] flex items-center justify-center text-2xl font-bold border-4 border-slate-200">
                SSC
              </div>
              <div>
                <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                  {t("Union Minister of Rural Development & Agriculture", "ग्रामीण विकास, कृषि एवं किसान कल्याण मंत्री")}
                </h3>
                <p className="text-sm font-bold text-slate-900 mt-1">
                  {t("Shri Shivraj Singh Chouhan", "श्री शिवराज सिंह चौहान")}
                </p>
              </div>
            </div>

            <div className="text-center space-y-3">
              <div className="mx-auto h-24 w-24 rounded-full bg-[#002B49] text-[#F59900] flex items-center justify-center text-2xl font-bold border-4 border-slate-200">
                CSP
              </div>
              <div>
                <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                  {t("Minister of State for Rural Development & Communications", "ग्रामीण विकास एवं संचार राज्य मंत्री")}
                </h3>
                <p className="text-sm font-bold text-slate-900 mt-1">
                  {t("Dr. Chandra Sekhar Pemmasani", "डॉ. चन्द्रशेखर पेम्मासानी")}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll-to-Top */}
      <button
        onClick={scrollToTop}
        className="fixed bottom-6 right-6 h-11 w-11 bg-[#002B49] hover:bg-[#00364A] text-[#F59900] font-bold rounded flex items-center justify-center transition-colors cursor-pointer z-50"
        title="Scroll to Top"
        aria-label="Scroll to Top"
      >
        <ArrowUp className="h-6 w-6" />
      </button>
    </div>
  );
}