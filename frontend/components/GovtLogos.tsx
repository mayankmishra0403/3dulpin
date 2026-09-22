"use client";

import React from "react";

// Official Government of India Emblem SVG Logo
export function AshokaEmblem({ className = "h-12 w-auto" }: { className?: string }) {
  return (
    <img
      src="https://upload.wikimedia.org/wikipedia/commons/8/84/Government_of_India_logo.svg"
      alt="Government of India Emblem"
      className={`object-contain inline-block ${className}`}
      loading="eager"
    />
  );
}

// Tricolor Indian Flag Banner Strip
export function TricolorStrip({ className = "h-1.5 w-full" }: { className?: string }) {
  return (
    <div className={`flex ${className}`}>
      <div className="h-full w-1/3 bg-[#FF9933]" title="Saffron" />
      <div className="h-full w-1/3 bg-[#FFFFFF]" title="White" />
      <div className="h-full w-1/3 bg-[#138808]" title="Green" />
    </div>
  );
}
