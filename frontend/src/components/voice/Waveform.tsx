"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AssistantState } from "@/lib/api";

interface WaveformProps {
  state: AssistantState;
  analyser?: AnalyserNode | null;
  className?: string;
}

export function Waveform({ state, analyser, className }: WaveformProps) {
  const bars = 32;
  const [heights, setHeights] = useState<number[]>(() => Array(bars).fill(0.15));

  useEffect(() => {
    if (!analyser || state !== "listening") {
      setHeights(Array(bars).fill(state === "speaking" ? 0.4 : 0.12));
      return;
    }

    const data = new Uint8Array(analyser.frequencyBinCount);
    let frame: number;

    const tick = () => {
      analyser.getByteFrequencyData(data);
      const step = Math.floor(data.length / bars);
      const next = Array.from({ length: bars }, (_, i) => {
        const val = data[i * step] / 255;
        return Math.max(0.08, val);
      });
      setHeights(next);
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [analyser, state]);

  const color =
    state === "listening"
      ? "bg-emerald-400"
      : state === "speaking"
        ? "bg-violet-400"
        : state === "thinking"
          ? "bg-amber-400"
          : "bg-white/30";

  return (
    <div className={cn("flex h-16 items-center justify-center gap-1", className)}>
      {heights.map((h, i) => (
        <motion.div
          key={i}
          className={cn("w-1 rounded-full", color)}
          animate={{ height: `${Math.max(8, h * 64)}px`, opacity: state === "idle" ? 0.35 : 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        />
      ))}
    </div>
  );
}
