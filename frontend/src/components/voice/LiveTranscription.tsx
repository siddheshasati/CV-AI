"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface LiveTranscriptionProps {
  transcript: string;
  interimTranscript?: string;
  isListening: boolean;
  className?: string;
}

export function LiveTranscription({
  transcript,
  interimTranscript,
  isListening,
  className,
}: LiveTranscriptionProps) {
  const display = interimTranscript || transcript;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={display || "empty"}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        className={cn(
          "min-h-[3rem] text-center text-lg leading-relaxed text-foreground/90",
          className
        )}
      >
        {display ? (
          <>
            {display}
            {isListening && (
              <motion.span
                className="ml-1 inline-block h-5 w-0.5 bg-emerald-400"
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 0.8, repeat: Infinity }}
              />
            )}
          </>
        ) : isListening ? (
          <span className="text-muted-foreground">Listening...</span>
        ) : (
          <span className="text-muted-foreground">Tap the microphone to speak</span>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
