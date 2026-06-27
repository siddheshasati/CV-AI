"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AssistantState } from "@/lib/api";

interface AvatarPlayerProps {
  state: AssistantState;
  avatarId?: string | null;
  onSessionReady?: (sessionId: string) => void;
  className?: string;
}

export function AvatarPlayer({ state, className }: AvatarPlayerProps) {
  const isSpeaking = state === "speaking";
  const isThinking = state === "thinking";
  const isListening = state === "listening";

  return (
    <div className={cn("relative aspect-[3/4] w-full max-w-sm overflow-hidden rounded-3xl bg-black", className)}>
      <div className="absolute inset-0 bg-gradient-to-b from-violet-500/10 to-transparent z-10" />

      {/* Photorealistic Avatar Image */}
      <motion.img
        src="/avatar.png"
        alt="Avatar"
        className="absolute inset-0 h-full w-full object-cover"
        animate={
          isSpeaking
            ? { scale: [1, 1.02, 1], filter: ["brightness(1)", "brightness(1.05)", "brightness(1)"] }
            : { scale: 1, filter: "brightness(1)" }
        }
        transition={{ duration: 2, repeat: isSpeaking ? Infinity : 0, ease: "easeInOut" }}
      />
      
      {/* Speaking Overlay Effect */}
      {isSpeaking && (
        <motion.div
          className="absolute inset-0 z-20 pointer-events-none rounded-3xl border-4 border-violet-500/30"
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {/* Status Indicators */}
      <div className="absolute inset-0 z-30 flex flex-col items-center justify-end pb-8 pointer-events-none">
        {isThinking && (
          <motion.div
            className="flex gap-1.5 bg-black/50 backdrop-blur-md px-4 py-2 rounded-full mb-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-2 w-2 rounded-full bg-amber-400"
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
          </motion.div>
        )}

        {isListening && (
          <motion.div
            className="bg-emerald-500/80 backdrop-blur-md px-3 py-1 rounded-full text-xs font-medium text-white mb-4"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            Listening...
          </motion.div>
        )}
      </div>
    </div>
  );
}
