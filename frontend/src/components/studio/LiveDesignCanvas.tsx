"use client";

/**
 * LiveDesignCanvas — client-side interactive design placement.
 *
 * Overlays the uploaded design on the product image and lets the user drag,
 * resize (corner handles) and rotate (top handle) it directly with the mouse,
 * in real time, with no server call. Movement/size are clamped to the view's
 * Print Area.
 *
 * The transform is expressed in the SAME parameters the backend render uses:
 *   - scale     : fraction of the print-area width the design's box spans
 *   - rotation  : degrees
 *   - offsetX/Y : pixels (in product-image coordinates) from print-area centre
 * so what you position here is what the real render produces.
 *
 * Implemented with native pointer events + CSS transforms (no Fabric.js/Konva)
 * because those can't be installed in this environment and a DOM overlay meets
 * every interaction requirement without a heavy dependency.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { DesignSettings, ProductViewType, DesignUpload } from "@/types";
import { getMediaUrl } from "@/lib/utils";

interface Props {
  view: ProductViewType;
  design: DesignUpload;
  settings: DesignSettings;
  onLiveChange: (partial: Partial<DesignSettings>) => void;
  onCommit: () => void;
}

const MIN_SCALE = 0.1;
const MAX_SCALE = 1.0;

type GestureKind = "move" | "resize" | "rotate" | null;

interface GestureState {
  kind: GestureKind;
  startX: number;
  startY: number;
  startScale: number;
  startRotation: number;
  startOffsetX: number;
  startOffsetY: number;
  centerScreenX: number;
  centerScreenY: number;
  startDist: number;
  startAngle: number;
}

export default function LiveDesignCanvas({
  view,
  design,
  settings,
  onLiveChange,
  onCommit,
}: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({ w: 0, h: 0 }); // rendered product image size (screen px)
  const gesture = useRef<GestureState | null>(null);

  const pa = view.print_areas?.[0];
  const imgW = view.image_width || 1000;
  const designAspect =
    design.width && design.height ? design.width / design.height : 1;

  // Screen px per image px.
  const s = box.w > 0 ? box.w / imgW : 0;

  const scale = settings.scale ?? 0.9;
  const rotation = settings.rotation ?? 0;
  const offsetX = settings.offsetX ?? 0;
  const offsetY = settings.offsetY ?? 0;

  // ── Measure the rendered product image ──
  const measure = useCallback(() => {
    const el = wrapRef.current?.querySelector("img[data-product]") as
      | HTMLImageElement
      | null;
    if (el && el.clientWidth > 0) {
      setBox({ w: el.clientWidth, h: el.clientHeight });
    }
  }, []);

  useEffect(() => {
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [measure, view.id]);

  if (!pa) {
    return (
      <div className="text-sm" style={{ color: "var(--text-muted)" }}>
        This view has no print area configured.
      </div>
    );
  }

  // ── Design box size in image px (mirrors backend placement) ──
  function designBoxImg(sc: number) {
    let bw = pa!.width * sc;
    let bh = bw / designAspect;
    if (bh > pa!.height * sc) {
      bh = pa!.height * sc;
      bw = bh * designAspect;
    }
    return { bw, bh };
  }

  // Clamp the centre so the (rotated) design box stays inside the print area.
  function clampOffset(ox: number, oy: number, sc: number, rot: number) {
    const { bw, bh } = designBoxImg(sc);
    const rad = (rot * Math.PI) / 180;
    const hx = (Math.abs(bw * Math.cos(rad)) + Math.abs(bh * Math.sin(rad))) / 2;
    const hy = (Math.abs(bw * Math.sin(rad)) + Math.abs(bh * Math.cos(rad))) / 2;
    const cx = pa!.x + pa!.width / 2 + ox;
    const cy = pa!.y + pa!.height / 2 + oy;
    const minCx = pa!.x + Math.min(hx, pa!.width / 2);
    const maxCx = pa!.x + pa!.width - Math.min(hx, pa!.width / 2);
    const minCy = pa!.y + Math.min(hy, pa!.height / 2);
    const maxCy = pa!.y + pa!.height - Math.min(hy, pa!.height / 2);
    const clCx = Math.min(Math.max(cx, minCx), maxCx);
    const clCy = Math.min(Math.max(cy, minCy), maxCy);
    return {
      offsetX: Math.round(clCx - (pa!.x + pa!.width / 2)),
      offsetY: Math.round(clCy - (pa!.y + pa!.height / 2)),
    };
  }

  // ── Geometry for rendering (screen px) ──
  const { bw, bh } = designBoxImg(scale);
  const centerImgX = pa.x + pa.width / 2 + offsetX;
  const centerImgY = pa.y + pa.height / 2 + offsetY;
  const boxScreen = {
    left: (centerImgX - bw / 2) * s,
    top: (centerImgY - bh / 2) * s,
    w: bw * s,
    h: bh * s,
  };
  const paScreen = {
    left: pa.x * s,
    top: pa.y * s,
    w: pa.width * s,
    h: pa.height * s,
  };

  // ── Gesture handlers ──
  function beginGesture(kind: GestureKind, e: React.PointerEvent) {
    e.preventDefault();
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    const centerScreenX = boxScreen.left + boxScreen.w / 2;
    const centerScreenY = boxScreen.top + boxScreen.h / 2;
    const dx = e.clientX - rectLeft() - centerScreenX;
    const dy = e.clientY - rectTop() - centerScreenY;
    gesture.current = {
      kind,
      startX: e.clientX,
      startY: e.clientY,
      startScale: scale,
      startRotation: rotation,
      startOffsetX: offsetX,
      startOffsetY: offsetY,
      centerScreenX,
      centerScreenY,
      startDist: Math.hypot(dx, dy) || 1,
      startAngle: (Math.atan2(dy, dx) * 180) / Math.PI,
    };
  }

  function rectLeft() {
    return wrapRef.current?.getBoundingClientRect().left ?? 0;
  }
  function rectTop() {
    return wrapRef.current?.getBoundingClientRect().top ?? 0;
  }

  function onPointerMove(e: React.PointerEvent) {
    const g = gesture.current;
    if (!g || s === 0) return;

    if (g.kind === "move") {
      const dImgX = (e.clientX - g.startX) / s;
      const dImgY = (e.clientY - g.startY) / s;
      const c = clampOffset(g.startOffsetX + dImgX, g.startOffsetY + dImgY, scale, rotation);
      onLiveChange(c);
    } else if (g.kind === "resize") {
      const dx = e.clientX - rectLeft() - g.centerScreenX;
      const dy = e.clientY - rectTop() - g.centerScreenY;
      const dist = Math.hypot(dx, dy);
      let ns = g.startScale * (dist / g.startDist);
      ns = Math.min(MAX_SCALE, Math.max(MIN_SCALE, ns));
      const c = clampOffset(offsetX, offsetY, ns, rotation);
      onLiveChange({ scale: Math.round(ns * 100) / 100, ...c });
    } else if (g.kind === "rotate") {
      const dx = e.clientX - rectLeft() - g.centerScreenX;
      const dy = e.clientY - rectTop() - g.centerScreenY;
      const ang = (Math.atan2(dy, dx) * 180) / Math.PI;
      let nr = Math.round(g.startRotation + (ang - g.startAngle));
      while (nr > 180) nr -= 360;
      while (nr < -180) nr += 360;
      const c = clampOffset(offsetX, offsetY, scale, nr);
      onLiveChange({ rotation: nr, ...c });
    }
  }

  function endGesture() {
    if (gesture.current) {
      gesture.current = null;
      onCommit();
    }
  }

  const handleStyle: React.CSSProperties = {
    position: "absolute",
    width: 14,
    height: 14,
    background: "#ffffff",
    border: "2px solid #000000",
    borderRadius: 2,
    touchAction: "none",
  };

  return (
    <div
      ref={wrapRef}
      className="relative inline-block select-none"
      style={{ touchAction: "none", lineHeight: 0 }}
      onPointerMove={onPointerMove}
      onPointerUp={endGesture}
      onPointerCancel={endGesture}
    >
      <img
        data-product
        src={getMediaUrl(view.image_url || view.image)}
        alt={view.view_name}
        className="max-h-[70vh] max-w-full rounded-lg"
        draggable={false}
        onLoad={measure}
      />

      {s > 0 && (
        <>
          {/* Print area outline + clip region */}
          <div
            className="absolute pointer-events-none"
            style={{
              left: paScreen.left,
              top: paScreen.top,
              width: paScreen.w,
              height: paScreen.h,
              border: "1.5px dashed rgba(0,0,0,0.5)",
              overflow: "hidden",
            }}
          >
            {/* Clipped ghost of the design (so overflow is visually cut) */}
            <img
              src={getMediaUrl(design.image)}
              alt=""
              draggable={false}
              style={{
                position: "absolute",
                left: boxScreen.left - paScreen.left,
                top: boxScreen.top - paScreen.top,
                width: boxScreen.w,
                height: boxScreen.h,
                transform: `rotate(${rotation}deg)`,
                transformOrigin: "center center",
                pointerEvents: "none",
              }}
            />
          </div>

          {/* Interactive design box (drag) + handles */}
          <div
            style={{
              position: "absolute",
              left: boxScreen.left,
              top: boxScreen.top,
              width: boxScreen.w,
              height: boxScreen.h,
              transform: `rotate(${rotation}deg)`,
              transformOrigin: "center center",
              cursor: "move",
              touchAction: "none",
            }}
            onPointerDown={(e) => beginGesture("move", e)}
          >
            {/* selection outline */}
            <div
              className="absolute inset-0"
              style={{ border: "1.5px solid #000000", opacity: 0.85 }}
            />
            {/* corner resize handles */}
            {(
              [
                ["nwse", 0, 0],
                ["nesw", 1, 0],
                ["nwse", 1, 1],
                ["nesw", 0, 1],
              ] as const
            ).map(([cur, cx, cy], i) => (
              <div
                key={i}
                onPointerDown={(e) => beginGesture("resize", e)}
                style={{
                  ...handleStyle,
                  left: `calc(${cx * 100}% - 7px)`,
                  top: `calc(${cy * 100}% - 7px)`,
                  cursor: `${cur}-resize`,
                }}
              />
            ))}
            {/* rotate handle */}
            <div
              onPointerDown={(e) => beginGesture("rotate", e)}
              style={{
                ...handleStyle,
                left: "calc(50% - 7px)",
                top: -28,
                borderRadius: "50%",
                cursor: "grab",
              }}
            />
            <div
              className="absolute pointer-events-none"
              style={{
                left: "50%",
                top: -14,
                width: 1,
                height: 14,
                background: "#000000",
              }}
            />
          </div>
        </>
      )}
    </div>
  );
}
