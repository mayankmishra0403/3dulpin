import type { Metadata } from "next";
import { GovtProvider } from "@/context/GovtContext";
import { GovtHeader } from "@/components/GovtHeader";
import { Navbar } from "@/components/Navbar";
import { GovtFooter } from "@/components/GovtFooter";
import { VoiceGuide } from "@/components/VoiceGuide";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bhumi3D • 3D Bhu-Aadhaar National Portal | Govt. of India",
  description:
    "National 3D Volumetric Cadastre & Vertical Property Mapping System under Digital India Land Records Modernization Programme (DILRMP).",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[var(--background)] text-slate-800 selection:bg-[#F59900] selection:text-slate-950">
        <GovtProvider>
          <GovtHeader />
          <Navbar />
          <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-7xl w-full mx-auto">{children}</main>
          <GovtFooter />
          <VoiceGuide />
        </GovtProvider>
      </body>
    </html>
  );
}
