"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useGovt } from "@/context/GovtContext";

export function Navbar() {
  const pathname = usePathname();
  const { t } = useGovt();

  const navItems = [
    { href: "/", label: t("Home", "मुख्य पृष्ठ") },
    { href: "/scene", label: t("3D Map Viewer", "3D मानचित्र") },
    { href: "/ulpin", label: t("3D ULPIN Lab", "3D ULPIN लैब") },
    { href: "/validation", label: t("Spatial Audit", "स्थानिक ऑडिट") },
    { href: "/certificate", label: t("Land Passport", "भू-पासपोर्ट") },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-[#002B49] text-white shadow-md border-b border-cyan-900/40">
      <div className="max-w-7xl mx-auto px-4 lg:px-12 overflow-x-auto scrollbar-none">
        <div className="flex items-center text-xs font-semibold whitespace-nowrap gap-1 py-1.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-4 py-2 rounded-lg transition-all ${
                  isActive
                    ? "bg-[#F59900] text-slate-950 font-bold shadow-sm"
                    : "text-slate-200 hover:text-white hover:bg-white/10"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
