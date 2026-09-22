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
    <nav className="bg-[#F5F5EE] border-t border-b border-slate-300">
      <div className="max-w-7xl mx-auto px-4 lg:px-12 overflow-x-auto scrollbar-none">
        <div className="flex items-center text-xs font-semibold whitespace-nowrap">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-4 py-3 transition-colors ${
                  isActive
                    ? "text-[#6B4600] font-bold border-b-2 border-[#F59900] bg-white"
                    : "text-slate-700 hover:text-[#6B4600] hover:bg-white"
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
