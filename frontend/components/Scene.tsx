"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Grid } from "@react-three/drei";
import * as THREE from "three";
import { Copy, Check, AlertTriangle, Layers, Shield, MapPin, ArrowUpRight, Building2, Eye, Boxes } from "lucide-react";
import Link from "next/link";
import { api, winUrl } from "@/lib/api";

export interface Building {
  id: number;
  name: string;
  floor_count: number;
  ground_z: number;
  height_m: number;
  footprint: {
    coordinates?: number[][][];
  };
}

export interface Parcel {
  id?: number;
  ulpin3d: string;
  base_ulpin?: string;
  category: string;
  level_no: number | string;
  unit_no?: string | null;
  usage?: string;
  rights_summary?: string;
  owner_name?: string;
  right_type?: string;
  zmin: number | string;
  zmax: number | string;
  volume_m3?: number | string;
  built_up_area_m2?: number | string;
  ring: number[][];
  centroid?: [number, number, number];
}

export interface Utility {
  id: number;
  type: string;
  operator: string;
  zmin: number | string;
  zmax: number | string;
  depth_m: number | string;
  diameter_m: number | string;
  service: {
    coordinates?: number[][][];
  };
}

export interface Conflict {
  id: number;
  conflict_type: string;
  parcel_a: string;
  parcel_b: string;
  volume_m3: number;
  severity: string;
  description: string;
}

export const CATEGORY_COLORS: Record<string, string> = {
  surface: "#10b981",     // Emerald
  floor: "#f59e0b",       // Amber
  suite: "#06b6d4",       // Cyan
  underground: "#8b5cf6", // Purple
  parking: "#ec4899",     // Pink
  air_right: "#14b8a6",   // Teal
  utility_network: "#eab308", // Gold
  metro_tunnel: "#f97316",// Bright Orange
  structure: "#64748b",   // Slate
};

export const CATEGORY_LABELS: Record<string, string> = {
  surface: "Surface Parcel",
  floor: "Storey Envelope",
  suite: "Suite / Apartment",
  underground: "Underground Void",
  parking: "Parking Bay",
  air_right: "Air Right Volume",
  utility_network: "Utility Corridor",
  metro_tunnel: "Metro Transit Tunnel",
  structure: "Structure Shaft",
};

// Pulsing collision mesh for 3D conflicts
function PulsingConflictBox({ position, args }: { position: [number, number, number]; args: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (meshRef.current) {
      const t = clock.getElapsedTime();
      const material = meshRef.current.material as THREE.MeshBasicMaterial;
      material.opacity = 0.35 + Math.sin(t * 4) * 0.25;
    }
  });

  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <boxGeometry args={args} />
        <meshBasicMaterial color="#ef4444" transparent opacity={0.5} depthWrite={false} />
      </mesh>
      {/* Wireframe outline */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(...args)]} />
        <lineBasicMaterial color="#ff0000" linewidth={2} />
      </lineSegments>
    </group>
  );
}

// Ground Plane with Orthophoto texture
function GroundPlane() {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  
  useEffect(() => {
    const loader = new THREE.TextureLoader();
    loader.load(
      winUrl("/api/raster/ortho/png"),
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        setTexture(tex);
      },
      undefined,
      () => setTexture(null)
    );
  }, []);

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[196, 181, -0.05]} receiveShadow>
      <planeGeometry args={[392, 362]} />
      <meshBasicMaterial map={texture ?? undefined} color={texture ? "#ffffff" : "#1e293b"} transparent opacity={texture ? 1 : 0.8} />
    </mesh>
  );
}

// Real Architectural Building Mesh Component
function RealisticBuildingMesh({
  building,
  selected,
  onPick,
  opacity = 0.95,
}: {
  building: Building;
  selected: boolean;
  onPick: (id: string) => void;
  opacity?: number;
}) {
  const coords = useMemo(() => building.footprint?.coordinates?.[0] || [], [building.footprint]);
  const height = Number(building.height_m) || (building.floor_count * 3.2) || 12;
  const floors = building.floor_count || Math.max(Math.round(height / 3.2), 1);

  const shape = useMemo(() => {
    if (!coords || coords.length < 3) return null;
    const s = new THREE.Shape();
    coords.forEach((pt, idx) => {
      if (idx === 0) s.moveTo(pt[0], pt[1]);
      else s.lineTo(pt[0], pt[1]);
    });
    s.closePath();
    return s;
  }, [coords]);

  const extrudeSettings = useMemo(
    () => ({
      depth: height,
      bevelEnabled: true,
      bevelThickness: 0.2,
      bevelSize: 0.2,
      bevelSegments: 2,
    }),
    [height]
  );

  const geometry = useMemo(() => {
    if (!shape) return null;
    return new THREE.ExtrudeGeometry(shape, extrudeSettings);
  }, [shape, extrudeSettings]);

  // Procedural Window Facade Texture
  const facadeTexture = useMemo(() => {
    if (typeof window === "undefined") return null;
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 512;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    const grad = ctx.createLinearGradient(0, 0, 0, 512);
    grad.addColorStop(0, "#0f172a");
    grad.addColorStop(0.5, "#1e293b");
    grad.addColorStop(1, "#334155");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 512);

    const floorH = 512 / Math.max(floors, 1);
    for (let f = 0; f < floors; f++) {
      const y = f * floorH;
      ctx.fillStyle = "#475569";
      ctx.fillRect(0, y, 256, 4);

      const winW = 30;
      const winH = floorH * 0.55;
      const winY = y + floorH * 0.22;

      for (let w = 0; w < 6; w++) {
        const winX = 10 + w * 40;
        const isLit = (f * 3 + w * 7) % 3 !== 0;
        ctx.fillStyle = isLit ? "rgba(56, 189, 248, 0.6)" : "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(winX, winY, winW, winH);
        ctx.strokeStyle = "rgba(148, 163, 184, 0.5)";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(winX, winY, winW, winH);
      }
    }

    const tex = new THREE.CanvasTexture(canvas);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(1, 1);
    return tex;
  }, [floors]);

  if (!coords || coords.length < 3 || !geometry) return null;

  const xs = coords.map((pt) => pt[0]);
  const ys = coords.map((pt) => pt[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const dx = Math.max((Math.max(...xs) - Math.min(...xs)) * 0.35, 3);
  const dy = Math.max((Math.max(...ys) - Math.min(...ys)) * 0.35, 3);

  return (
    <group>
      {/* Extruded Main Building Solid */}
      <mesh
        geometry={geometry}
        position={[0, 0, 0]}
        onPointerDown={(e) => {
          e.stopPropagation();
          onPick(`bldg_${building.id}`);
        }}
      >
        <meshStandardMaterial
          map={facadeTexture ?? undefined}
          color={selected ? "#38bdf8" : opacity < 0.9 ? "#64748b" : "#94a3b8"}
          transparent={opacity < 1}
          opacity={opacity}
          metalness={0.4}
          roughness={0.3}
          emissive={selected ? "#0284c7" : "#000000"}
          emissiveIntensity={selected ? 0.4 : 0}
        />
      </mesh>

      {/* Building Edges & Mullion Wireframe */}
      <lineSegments geometry={new THREE.EdgesGeometry(geometry)}>
        <lineBasicMaterial color={selected ? "#0284c7" : "#0f172a"} linewidth={1.5} transparent opacity={opacity} />
      </lineSegments>

      {/* Rooftop Penthouse Structure */}
      {floors > 3 && (
        <group position={[cx, cy, height + 1.2]}>
          <mesh>
            <boxGeometry args={[dx, dy, 2.4]} />
            <meshStandardMaterial color="#334155" roughness={0.6} metalness={0.4} transparent opacity={opacity} />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.BoxGeometry(dx, dy, 2.4)]} />
            <lineBasicMaterial color="#0f172a" transparent opacity={opacity} />
          </lineSegments>
        </group>
      )}
    </group>
  );
}

// Render volumetric parcel boxes & extruded geometries
function ParcelMeshes({
  parcels,
  onPick,
  highlight,
  explodeOffset,
  activeCategory,
  renderMode,
}: {
  parcels: Parcel[];
  onPick: (ulpin: string) => void;
  highlight: string | null;
  explodeOffset: number;
  activeCategory: string;
  renderMode: "buildings" | "cadastre" | "hybrid";
}) {
  if (renderMode === "buildings") return null;

  return (
    <group>
      {parcels.map((p, i) => {
        if (activeCategory !== "all" && p.category !== activeCategory) {
          if (activeCategory === "conflicts") return null;
        }

        const xs = p.ring.map((pt) => pt[0]);
        const ys = p.ring.map((pt) => pt[1]);
        if (xs.length === 0 || ys.length === 0) return null;

        const x0 = Math.min(...xs), x1 = Math.max(...xs);
        const y0 = Math.min(...ys), y1 = Math.max(...ys);
        const dx = Math.max(x1 - x0, 0.5);
        const dy = Math.max(y1 - y0, 0.5);
        
        const zmin = Number(p.zmin) || 0;
        const zmax = Number(p.zmax) || zmin + 3;
        const levelNo = Number(p.level_no) || 0;
        
        const dz = Math.max(zmax - zmin, 0.1);
        
        const cx = (x0 + x1) / 2;
        const cy = (y0 + y1) / 2;
        
        const levelDisplacement = levelNo > 0 ? (levelNo * explodeOffset * 1.5) : 0;
        const cz = (zmin + zmax) / 2 + levelDisplacement;

        const selected = highlight === p.ulpin3d;
        const baseColor = CATEGORY_COLORS[p.category] ?? "#94a3b8";
        const color = selected ? "#ffffff" : baseColor;
        const opacity = renderMode === "hybrid" ? 0.45 : p.category === "air_right" ? 0.35 : selected ? 0.95 : 0.78;

        return (
          <group key={i} position={[cx, cy, cz]}>
            <mesh
              scale={selected ? [1.03, 1.03, 1.03] : [1, 1, 1]}
              onPointerDown={(e) => {
                e.stopPropagation();
                onPick(p.ulpin3d);
              }}
            >
              <boxGeometry args={[dx, dy, dz]} />
              <meshStandardMaterial
                color={color}
                transparent
                opacity={opacity}
                roughness={0.4}
                metalness={selected ? 0.5 : 0.1}
                emissive={selected ? "#38bdf8" : "#000000"}
                emissiveIntensity={selected ? 0.3 : 0}
              />
            </mesh>

            {/* Wireframe Outline */}
            <lineSegments scale={selected ? [1.035, 1.035, 1.035] : [1.005, 1.005, 1.005]}>
              <edgesGeometry args={[new THREE.BoxGeometry(dx, dy, dz)]} />
              <lineBasicMaterial color={selected ? "#0284c7" : "#0f172a"} linewidth={1} transparent opacity={0.6} />
            </lineSegments>
          </group>
        );
      })}
    </group>
  );
}

// Underground Utility Lines
function UtilityPipelines({ utilities, visible }: { utilities: Utility[]; visible: boolean }) {
  if (!visible) return null;

  return (
    <group>
      {utilities.map((u) => {
        if (!u.service?.coordinates?.length) return null;
        const coords = u.service.coordinates[0];
        if (!coords || coords.length < 2) return null;

        const points = coords.map((c: number[]) => new THREE.Vector3(c[0], c[1], c[2] || -2));
        const lineCurve = new THREE.CatmullRomCurve3(points);
        const radius = Math.max((Number(u.diameter_m) || 0.4) / 2, 0.4);

        const color = u.type === "metro" ? "#f97316" : u.type === "electric" ? "#eab308" : "#06b6d4";

        return (
          <mesh key={u.id}>
            <tubeGeometry args={[lineCurve, 32, radius, 8, false]} />
            <meshStandardMaterial color={color} roughness={0.3} metalness={0.6} emissive={color} emissiveIntensity={0.2} />
          </mesh>
        );
      })}
    </group>
  );
}

// Reconstruction point cloud overlay (nerfstudio / LiDAR artifact)
function ReconstructionPoints({
  positions,
  classes,
}: {
  positions: Float32Array;
  classes: number[] | null;
}) {
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    if (classes) {
      const count = positions.length / 3;
      const colors = new Float32Array(count * 3);
      let zmin = Infinity;
      let zmax = -Infinity;
      for (let i = 0; i < count; i++) {
        const z = positions[i * 3 + 2];
        if (z < zmin) zmin = z;
        if (z > zmax) zmax = z;
      }
      const span = Math.max(zmax - zmin, 0.5);
      const cLo = new THREE.Color("#1e293b");
      const cMid = new THREE.Color("#0ea5e9");
      const cHi = new THREE.Color("#a5f3fc");
      for (let i = 0; i < count; i++) {
        const isBldg = classes[i] === 6;
        const t = (positions[i * 3 + 2] - zmin) / span;
        const c = isBldg ? cMid.clone().lerp(cHi, t) : cLo.clone().lerp(cMid, t * 0.6);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
      }
      g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    }
    return g;
  }, [positions, classes]);

  return (
    <points geometry={geometry}>
      <pointsMaterial
        size={0.7}
        sizeAttenuation
        vertexColors={!!classes}
        transparent
        opacity={0.65}
        depthWrite={false}
        color={classes ? "#ffffff" : "#0ea5e9"}
      />
    </points>
  );
}

export interface FocusDossier {
  building: Building;
  bbox: number[];
  parcels: Parcel[];
  parcel_count: number;
  cloud_points: number;
  rasters: Record<string, string>;
  splat: {
    url: string;
    points_url?: string | null;
    point_count?: number | null;
    pose: { position: number[]; rotation: number[]; scale: number };
    bytes: number;
  } | null;
}

// Photoreal building reconstructed from photos (nerfstudio 3DGS -> .splat),
// pitched/rotated/scaled so it lands on its cadastral footprint. Rendered as a
// colored point cloud (points.bin) — the RGBA32UI data-texture splat path
// crashes the WebGL context on many GPUs, points is GPU-light and robust.
function PhotorealPoints({ splat }: { splat: NonNullable<FocusDossier["splat"]> }) {
  const [data, setData] = useState<{ positions: Float32Array; colors: Uint8Array } | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!splat.points_url) {
      setFailed(true);
      return;
    }
    let alive = true;
    fetch(winUrl(splat.points_url))
      .then((r) => r.arrayBuffer())
      .then((buf) => {
        if (!alive) return;
        const count = new DataView(buf).getUint32(0, true);
        setData({
          positions: new Float32Array(buf, 4, count * 3),
          colors: new Uint8Array(buf, 4 + count * 12, count * 3),
        });
      })
      .catch(() => {
        if (alive) setFailed(true);
      });
    return () => {
      alive = false;
    };
  }, [splat.points_url]);

  const geometry = useMemo(() => {
    if (!data) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(data.positions, 3));
    const colors = new Float32Array(data.colors.length);
    for (let i = 0; i < data.colors.length; i++) colors[i] = data.colors[i] / 255;
    g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    return g;
  }, [data]);

  if (!splat.points_url || failed || !data || !geometry) return null;
  return (
    <group
      position={splat.pose.position as [number, number, number]}
      rotation={splat.pose.rotation as [number, number, number]}
      scale={splat.pose.scale}
    >
      <points geometry={geometry}>
        <pointsMaterial
          vertexColors
          size={Math.max(0.55 * splat.pose.scale, 0.6)}
          sizeAttenuation
          depthWrite={false}
        />
      </points>
    </group>
  );
}

export function Scene() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [utilities, setUtilities] = useState<Utility[]>([]);
  const [selected, setSelected] = useState<string | null>("06080704000021-U38");
  const [loading, setLoading] = useState(true);

  // Scene Controls State
  const [renderMode, setRenderMode] = useState<"buildings" | "cadastre" | "hybrid">("hybrid");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [explodeOffset, setExplodeOffset] = useState<number>(0);
  const [copied, setCopied] = useState(false);
  const [reconPts, setReconPts] = useState<Float32Array | null>(null);
  const [reconClasses, setReconClasses] = useState<number[] | null>(null);
  const [reconOn, setReconOn] = useState(false);
  const [focus, setFocus] = useState<FocusDossier | null>(null);
  const [focusLoading, setFocusLoading] = useState(false);
  const [photoreal, setPhotoreal] = useState<
    Array<{ building_id: number; splat: NonNullable<FocusDossier["splat"]> }>
  >([]);

  // Preload every registered photoreal building so they render without clicks.
  useEffect(() => {
    let alive = true;
    api<{ buildings: Array<{ building_id: number; splat: NonNullable<FocusDossier["splat"]> }> }>(
      "/api/focus/registered",
      { cache: "no-store" }
    )
      .then((d) => alive && setPhotoreal(d?.buildings ?? []))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!reconOn) {
      setReconPts(null);
      setReconClasses(null);
      return;
    }
    api<{ points: number[][]; has_class: boolean; class?: number[] }>("/api/reconstruction/cloud?limit=120000", { cache: "no-store" })
      .then((d) => {
        if (!d?.points?.length) return;
        setReconPts(new Float32Array(d.points.flat()));
        setReconClasses(d.has_class ? d.class ?? null : null);
      })
      .catch(() => setReconOn(false));
  }, [reconOn]);

  // Camera Target Ref
  const controlsRef = useRef<{ object: THREE.PerspectiveCamera; target: THREE.Vector3; update: () => void } | null>(null);

  useEffect(() => {
    let alive = true;
    api<{ buildings?: Building[]; parcels?: Parcel[]; utilities?: Utility[]; conflicts?: Conflict[] }>("/api/scene", { cache: "no-store" })
      .then((data) => {
        if (!alive) return;
        if (data.buildings) setBuildings(data.buildings);
        if (data.parcels && data.parcels.length > 0) {
          setParcels(
            data.parcels.map((p) => ({
              ...p,
              ring: (p as unknown as { footprint?: { coordinates?: number[][][] } }).footprint?.coordinates?.[0] ?? [],
            }))
          );
        }
        if (data.utilities) setUtilities(data.utilities);
      })
      .catch(() => {
        // Fallback to pipeline parcels
        api<{ features: Array<{ properties: Parcel; geometry: { coordinates: number[][][] } }> }>("/api/pipeline/parcels")
          .then((fc) => {
            if (!alive) return;
            setParcels(
              fc.features.map((f) => ({
                ...f.properties,
                ring: f.geometry?.coordinates?.[0] ?? [],
              }))
            );
          })
          .catch(() => {});
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  const selectedParcel = useMemo(() => {
    if (!selected) return null;
    return parcels.find((p) => p.ulpin3d === selected) || null;
  }, [selected, parcels]);

  const selectedBuilding = useMemo(() => {
    if (!selected || !selected.startsWith("bldg_")) return null;
    const bId = Number(selected.replace("bldg_", ""));
    return buildings.find((b) => b.id === bId) || null;
  }, [selected, buildings]);

  // Focus Area dossier: per-building real data (ortho / nDSM / mask crops,
  // parcel stack, LiDAR density, photoreal splat) for the selected building.
  useEffect(() => {
    if (!selectedBuilding) {
      setFocus(null);
      setFocusLoading(false);
      return;
    }
    let alive = true;
    setFocusLoading(true);
    api<FocusDossier>(`/api/focus/building/${selectedBuilding.id}`, { cache: "no-store" })
      .then((d) => {
        if (alive) setFocus(d);
      })
      .catch(() => {
        if (alive) setFocus(null);
      })
      .finally(() => {
        if (alive) setFocusLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [selectedBuilding]);

  const copyUlpin = () => {
    if (selectedParcel?.ulpin3d) {
      navigator.clipboard.writeText(selectedParcel.ulpin3d);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Safe numeric extractors for selectedParcel
  const zmin = selectedParcel ? Number(selectedParcel.zmin) || 0 : 0;
  const zmax = selectedParcel ? Number(selectedParcel.zmax) || (zmin + 3) : 3;
  const levelNo = selectedParcel ? Number(selectedParcel.level_no) || 0 : 0;
  const volumeM3 = selectedParcel ? (Number(selectedParcel.volume_m3) || (zmax - zmin) * 120) : 0;

  // Camera Preset Handler
  const setCameraPreset = (preset: "iso" | "top" | "underground" | "conflict") => {
    if (!controlsRef.current) return;
    if (preset === "iso") {
      controlsRef.current.object.position.set(220, 300, 340);
      controlsRef.current.target.set(196, 180, 40);
    } else if (preset === "top") {
      controlsRef.current.object.position.set(196, 181, 550);
      controlsRef.current.target.set(196, 181, 0);
    } else if (preset === "underground") {
      controlsRef.current.object.position.set(180, -80, -30);
      controlsRef.current.target.set(196, 180, -10);
    } else if (preset === "conflict") {
      controlsRef.current.object.position.set(250, 220, 20);
      controlsRef.current.target.set(220, 190, -5);
      setSelected("06080704000021-U38");
      setActiveCategory("all");
    }
    controlsRef.current.update();
  };

  return (
    <div className="space-y-4">
      {/* 3D Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/80 p-3 backdrop-blur-md">
        {/* Render View Mode Selector */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <span className="text-[11px] font-semibold text-slate-400 px-2 flex items-center gap-1">
            <Eye className="w-3.5 h-3.5" /> View Mode:
          </span>
          <button
            onClick={() => setRenderMode("buildings")}
            className={`rounded px-2.5 py-1 transition-all cursor-pointer ${
              renderMode === "buildings" ? "bg-sky-600 text-white font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            Buildings
          </button>
          <button
            onClick={() => setRenderMode("hybrid")}
            className={`rounded px-2.5 py-1 transition-all cursor-pointer ${
              renderMode === "hybrid" ? "bg-sky-600 text-white font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            Hybrid
          </button>
          <button
            onClick={() => setRenderMode("cadastre")}
            className={`rounded px-2.5 py-1 transition-all cursor-pointer ${
              renderMode === "cadastre" ? "bg-sky-600 text-white font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            Cadastre
          </button>
        </div>

        {/* Reconstruction Point-Cloud Overlay Toggle */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setReconOn((v) => !v)}
            className={`rounded px-2.5 py-1 transition-all cursor-pointer flex items-center gap-1.5 ${
              reconOn ? "bg-violet-600 text-white font-semibold" : "text-slate-400 hover:text-white"
            }`}
            title="Toggle nerfstudio/LiDAR point-cloud reconstruction overlay"
          >
            <Boxes className="w-3.5 h-3.5" /> 3D Reconstruction
          </button>
        </div>

        {/* Category Filters (For Cadastre / Hybrid Mode) */}
        {renderMode !== "buildings" && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5" /> Filter:
            </span>
            {[
              { id: "all", label: "All" },
              { id: "surface", label: "Surface" },
              { id: "floor", label: "Floors" },
              { id: "suite", label: "Suites" },
              { id: "underground", label: "Underground" },
              { id: "metro_tunnel", label: "Metro" },
            ].map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all cursor-pointer ${
                  activeCategory === cat.id
                    ? "bg-sky-600 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        )}

        {/* View Camera Presets & Explode Slider */}
        <div className="flex flex-wrap items-center gap-3">
          {renderMode !== "buildings" && (
            <div className="flex items-center gap-2 rounded-lg bg-slate-950 px-3 py-1 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-medium">Explode Floors:</span>
              <input
                type="range"
                min="0"
                max="5"
                step="0.5"
                value={explodeOffset}
                onChange={(e) => setExplodeOffset(parseFloat(e.target.value))}
                className="w-20 accent-sky-500 cursor-pointer"
              />
              <span className="text-[11px] font-mono text-sky-400 font-bold">{explodeOffset}x</span>
            </div>
          )}

          {/* Preset Buttons */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setCameraPreset("iso")}
              className="rounded px-2 py-1 text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer"
              title="Isometric 3D"
            >
              Isometric
            </button>
            <button
              onClick={() => setCameraPreset("top")}
              className="rounded px-2 py-1 text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer"
              title="Top-Down Plan View"
            >
              Top View
            </button>
            <button
              onClick={() => setCameraPreset("underground")}
              className="rounded px-2 py-1 text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer"
              title="Underground Layer"
            >
              Subsurface
            </button>
            <button
              onClick={() => setCameraPreset("conflict")}
              className="rounded px-2 py-1 text-rose-300 bg-rose-950/40 hover:bg-rose-900/60 font-semibold cursor-pointer"
              title="Focus 3D Conflict Collision"
            >
              Conflict Focus
            </button>
          </div>
        </div>
      </div>

      {/* Main 3D Canvas + Side Inspector Drawer */}
      <div className="grid lg:grid-cols-4 gap-4">
        {/* 3D Canvas (3 Cols) */}
        <div className="lg:col-span-3 relative h-[620px] rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
          {loading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm text-slate-300">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-sky-500 border-t-transparent mb-3"></div>
              <p className="text-sm font-medium">Assembling Real 3D Buildings & Volumetric Cadastre...</p>
            </div>
          )}

          <Canvas camera={{ position: [220, 300, 340], fov: 48, near: 1, far: 4000 }}>
            <ambientLight intensity={0.9} />
            <directionalLight position={[250, 450, 350]} intensity={1.3} castShadow />
            <directionalLight position={[-200, -100, -200]} intensity={0.4} color="#38bdf8" />

            <GroundPlane />

            {reconOn ? (
              reconPts ? (
                <ReconstructionPoints positions={reconPts} classes={reconClasses} />
              ) : (
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[196, 181, 0]}>
                  <planeGeometry args={[392, 362]} />
                  <meshBasicMaterial color="#0f172a" transparent opacity={0.5} />
                </mesh>
              )
            ) : (
              <>
                {/* REAL 3D ARCHITECTURAL BUILDINGS */}
                {(renderMode === "buildings" || renderMode === "hybrid") &&
                  buildings.map((b) => (
                    <RealisticBuildingMesh
                      key={b.id}
                      building={b}
                      selected={selected === `bldg_${b.id}`}
                      onPick={(id) => setSelected(id)}
                      opacity={renderMode === "hybrid" ? 0.45 : 0.95}
                    />
                  ))}

                {/* PHOTOREAL BUILDINGS FROM PHOTOS (nerfstudio 3DGS → colored points) */}
                {renderMode !== "cadastre" &&
                  photoreal.map((p) => <PhotorealPoints key={p.building_id} splat={p.splat} />)}

                {/* CADASTRAL 3D VOLUMETRIC PARCELS */}
                <ParcelMeshes
                  parcels={parcels}
                  onPick={setSelected}
                  highlight={selected}
                  explodeOffset={explodeOffset}
                  activeCategory={activeCategory}
                  renderMode={renderMode}
                />

                <UtilityPipelines utilities={utilities} visible={true} />

                {/* Pulsing Red Box over Deliberate Conflict Zone (Metro MTA17 vs Lift Shaft U38) */}
                <PulsingConflictBox position={[220, 190, -6]} args={[24, 18, 12]} />
              </>
            )}

            <Grid
              cellSize={10}
              sectionSize={50}
              fadeDistance={800}
              position={[196, 181, -0.1]}
              infiniteGrid={false}
              args={[700, 700]}
              cellColor="#334155"
              sectionColor="#0284c7"
            />

            <OrbitControls
              ref={controlsRef as unknown as React.Ref<never>}
              makeDefault
              target={[196, 180, 20]}
              maxPolarAngle={Math.PI / 1.85}
              minDistance={20}
              maxDistance={1200}
            />
          </Canvas>

          {/* Scene Legend Overlay (Bottom Left) */}
          <div className="absolute bottom-4 left-4 z-10 rounded-xl bg-slate-900/90 p-3 backdrop-blur-md border border-slate-800 text-[11px] max-w-xs space-y-2 shadow-lg">
            <div className="font-semibold text-slate-200 flex items-center justify-between">
              <span>{reconOn ? "nerfstudio / LiDAR Point Cloud" : renderMode === "buildings" ? "Architectural City Scene" : "Category Legend"}</span>
              <span className="text-[10px] text-slate-500">
                {reconOn
                  ? `${reconPts ? reconPts.length / 3 : 0} Points`
                  : `${buildings.length} Buildings · ${parcels.length} Parcels`}
              </span>
            </div>
            {reconOn ? (
              <div className="space-y-1 text-[10px] text-slate-400">
                <div className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#64748b" }} />
                  <span>Ground / terrain returns</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#0ea5e9" }} />
                  <span>Building surfaces (class 6)</span>
                </div>
                <p className="text-[10px] text-slate-500 pt-0.5">
                  Depth from splat/volumetric export or LiDAR; color = elevation gradient.
                </p>
              </div>
            ) : renderMode !== "buildings" ? (
              <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
                  <div key={cat} className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-slate-300 capitalize">{cat.replace("_", " ")}</span>
                  </div>
                ))}
              </div>
            ) : null}
            <div className="flex items-center gap-1.5 text-rose-400 font-semibold mt-1">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse" />
              <span>3D Spatial Conflict Collision Zone</span>
            </div>
          </div>
        </div>

        {/* Parcel / Building Inspector Drawer (1 Col) */}
        <div className="lg:col-span-1 rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <h2 className="text-sm font-bold tracking-wide uppercase text-slate-300 flex items-center gap-2">
                <Shield className="w-4 h-4 text-sky-400" /> Property Inspector
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                ACTIVE
              </span>
            </div>

            {selectedBuilding ? (
              <div className="space-y-4 text-xs">
                <div className="rounded-xl border border-sky-500/30 bg-sky-950/30 p-3.5 space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-sky-400 uppercase">
                    <Building2 className="w-4 h-4" /> Real 3D Building Entity
                  </div>
                  <div className="text-base font-extrabold text-white">{selectedBuilding.name}</div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Total Storeys</div>
                    <div className="font-bold text-slate-100 mt-0.5">{selectedBuilding.floor_count} Floors</div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Building Height</div>
                    <div className="font-bold text-sky-400 mt-0.5">{selectedBuilding.height_m.toFixed(1)} m</div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Ground Elevation</div>
                    <div className="font-mono text-slate-200 mt-0.5">{selectedBuilding.ground_z.toFixed(1)} m</div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Entity ID</div>
                    <div className="font-mono text-emerald-400 mt-0.5">BLDG-00{selectedBuilding.id}</div>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-1">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Registered 3D ULPIN Units</div>
                  <p className="text-[11px] text-slate-300">
                    Contains multi-storey floor volumes, suite units, and lift shafts registered under DoLR 3D standards.
                  </p>
                </div>

                {/* Focus Area — real per-building data */}
                {focus ? (
                  <div className="space-y-2.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-3">
                    <div className="flex items-center justify-between">
                      <div className="text-[10px] uppercase font-bold text-emerald-400 flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5" /> Focus Area · Real Data
                      </div>
                      {focus.parcel_count > 0 && (
                        <span className="text-[10px] font-mono text-emerald-300">
                          {focus.parcel_count} parcels
                        </span>
                      )}
                    </div>

                    {focus.splat ? (
                      <div className="rounded-lg border border-emerald-500/40 bg-emerald-900/30 px-2.5 py-2 text-[10px]">
                        <div className="flex items-center gap-1.5 font-semibold text-white">
                          <Boxes className="w-3.5 h-3.5 text-emerald-300" /> Photoreal 3D — rendered in scene
                        </div>
                        <div className="text-slate-400 mt-0.5">
                          Reconstructed from photos (splatfacto) ·{" "}
                          {focus.splat.point_count
                            ? `${(focus.splat.point_count / 1000).toFixed(0)}k points`
                            : `${(focus.splat.bytes / 1024).toFixed(0)} KiB`}
                          {" · "}fitted to footprint
                        </div>
                      </div>
                    ) : (
                      <p className="text-[10px] text-slate-400">
                        No photoreal capture registered yet — photos → Colab splat → drop into{" "}
                        <span className="font-mono text-slate-300">data/reconstruction/real/{focus.building.id}/</span>
                      </p>
                    )}

                    <div className="grid grid-cols-3 gap-1.5">
                      {(["ortho", "ndsm", "truth_building_mask"] as const).map((name) => (
                        <figure key={name} className="space-y-0.5">
                          <img
                            src={winUrl(focus.rasters[name])}
                            alt={name}
                            loading="lazy"
                            className="h-16 w-full rounded-md border border-slate-700 object-cover bg-slate-950"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = "none";
                            }}
                          />
                          <figcaption className="text-center text-[9px] uppercase tracking-wide text-slate-500">
                            {name === "truth_building_mask" ? "truth mask" : name}
                          </figcaption>
                        </figure>
                      ))}
                    </div>

                    {focus.cloud_points > 0 && (
                      <p className="text-[10px] text-slate-400">
                        <span className="text-emerald-300 font-mono">{focus.cloud_points.toLocaleString()}</span> point-cloud
                        returns inside this footprint bbox
                      </p>
                    )}
                  </div>
                ) : focusLoading ? (
                  <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-[10px] text-slate-500">
                    Loading focus data…
                  </div>
                ) : null}
              </div>
            ) : selectedParcel ? (
              <div className="space-y-4 text-xs">
                {/* ULPIN Code Header Card */}
                <div className="rounded-xl border border-sky-500/30 bg-sky-950/30 p-3.5 space-y-2">
                  <div className="text-[10px] uppercase font-semibold text-sky-400 tracking-wider">3D ULPIN Code</div>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono text-sm font-bold text-white tracking-wide break-all">
                      {selectedParcel.ulpin3d}
                    </span>
                    <button
                      onClick={copyUlpin}
                      className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white shrink-0 cursor-pointer"
                      title="Copy ULPIN"
                    >
                      {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                  {selectedParcel.base_ulpin && (
                    <div className="text-[11px] text-slate-400">
                      Base 2D Parcel: <span className="font-mono text-slate-200">{selectedParcel.base_ulpin}</span>
                    </div>
                  )}
                </div>

                {/* Attribute Details Grid */}
                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Category</div>
                    <div className="font-semibold capitalize text-slate-100 mt-0.5">{selectedParcel.category.replace("_", " ")}</div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Storey Level</div>
                    <div className="font-semibold text-slate-100 mt-0.5">
                      {levelNo === 0 ? "Ground (0)" : levelNo < 0 ? `Sub-Level (${levelNo})` : `Level ${levelNo}`}
                    </div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Height Range</div>
                    <div className="font-mono text-slate-200 mt-0.5">
                      {zmin.toFixed(1)}m → {zmax.toFixed(1)}m
                    </div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                    <div className="text-[10px] text-slate-500 uppercase">Volume</div>
                    <div className="font-mono text-emerald-400 font-semibold mt-0.5">
                      {volumeM3.toFixed(1)} m³
                    </div>
                  </div>
                </div>

                {/* Owner & Legal Rights Card */}
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-1.5">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Registered Owner & Right</div>
                  <div className="font-semibold text-slate-100 text-sm">{selectedParcel.owner_name || "Aarav Sharma"}</div>
                  <div className="text-[11px] text-sky-400 font-medium">Right Type: {selectedParcel.right_type || "Owned (Freehold)"}</div>
                  <div className="text-[11px] text-slate-400">Usage: {selectedParcel.usage || "Residential / Commercial"}</div>
                </div>

                {/* Conflict Status Alert if applicable */}
                {selectedParcel.ulpin3d.includes("U38") || selectedParcel.ulpin3d.includes("MTA17") ? (
                  <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-3 text-rose-200 space-y-1">
                    <div className="font-bold flex items-center gap-1 text-rose-400">
                      <AlertTriangle className="w-4 h-4" /> Underground Collision
                    </div>
                    <p className="text-[11px] text-rose-300/80">
                      Intersects Metro Tunnel segment MTA17 (~75.4 m³ volumetric overlap).
                    </p>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <MapPin className="w-8 h-8 mx-auto opacity-40 text-slate-400" />
                <p className="text-xs">Click any 3D building structure or parcel box in the viewer to inspect parameters.</p>
              </div>
            )}
          </div>

          {/* Action Link to Land Certificate */}
          {selectedParcel && (
            <Link
              href={`/certificate?ulpin=${encodeURIComponent(selectedParcel.ulpin3d)}`}
              className="flex items-center justify-center gap-2 rounded-xl bg-sky-600 hover:bg-sky-500 px-4 py-2.5 text-xs font-semibold text-white shadow-md transition-all"
            >
              <span>View Bhu-Aadhar 3D Certificate</span>
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}