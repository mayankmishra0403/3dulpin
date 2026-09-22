"use client";

import React from "react";
import { useGovt } from "@/context/GovtContext";
import { Building2, MapPin, Phone, Mail } from "lucide-react";

export function GovtFooter() {
  const { t } = useGovt();

  return (
    <footer className="w-full">
      {/* MAIN FOOTER */}
      <div className="bg-[#00364A] text-white py-10 border-t-4 border-[#F59900]">
        <div className="max-w-7xl mx-auto px-4 lg:px-12 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-3">
            <h3 className="text-sm font-bold uppercase tracking-wide text-[#F59900] border-b border-cyan-800 pb-2">
              {t("About this Portal", "इस पोर्टल के बारे में")}
            </h3>
            <p className="text-xs text-slate-200 leading-relaxed">
              {t(
                "The 3D Bhu-Aadhaar National Portal is developed by the Department of Land Resources, Ministry of Rural Development, under the Digital India Land Records Modernisation Programme (DILRMP). It extends the 14-digit ULPIN to volumetric 3D property records covering multi-storey units, basements, utilities and subsurface corridors.",
                "3D भू-आधार राष्ट्रीय पोर्टल ग्रामीण विकास मंतालय के अधीन भूमि संसाधन विभाग द्वारा डिजिटल इंडिया भूमि अभिलेख आधुनिकीकरण कार्यक्रम (डी.आई.एल.आर.एम.पी.) के अंतर्गत विकसित किया गया है। यह 14-अंकीय ULPIN को बहुमंजिला इकाइयों, बेसमेंट, उपयोगिताओं एवं भूमिगत कॉरिडोर सहित वॉल्यूमेट्रिक 3D संपत्ति अभिलेखों तक विस्तारित करता है।"
              )}
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-bold uppercase tracking-wide text-[#F59900] border-b border-cyan-800 pb-2">
              {t("Web Manager & Contact", "वेब प्रबंधक एवं संपर्क")}
            </h3>
            <ul className="space-y-2.5 text-xs text-slate-200">
              <li className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-[#F59900] shrink-0" />
                <span>{t("Computer Cell • Department of Land Resources", "कम्प्यूटर सेल • भू-संसाधन विभाग")}</span>
              </li>
              <li className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-[#F59900] shrink-0" />
                <span>{t("Ministry of Rural Development, New Delhi", "ग्रामीण विकास मंतालय, नई दिल्ली")}</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-[#F59900] shrink-0" />
                <span className="font-mono">1800-180-3D-ULPIN</span>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-[#F59900] shrink-0" />
                <span className="font-mono">helpdesk@bhumi3d.gov.in</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* BOTTOM LEGAL ACCREDITATION BAR */}
      <div className="bg-[#1B2024] text-slate-300 py-6 text-xs">
        <div className="max-w-7xl mx-auto px-4 lg:px-12 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="bg-white px-3 py-1.5 rounded font-bold text-slate-900 text-xs flex items-center gap-1.5">
            <span className="text-[#002B49] font-black">NIC</span>
            <span className="text-[9px] text-slate-600 uppercase">National Informatics Centre</span>
          </div>

          <div className="text-center md:text-right text-[11px] space-y-1 leading-relaxed">
            <p>
              {t(
                "© Ownership, updating and maintenance of information on this website is managed by Department of Land Resources.",
                "© इस वेबसाइट की सूचनाओं का स्वामित्व, अद्यतन एवं रखरखाव भूमि संसाधन विभाग द्वारा किया जाता है।"
              )}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
