"use client";

import { motion } from "framer-motion";
import { Mic, MicOff, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AssistantState } from "@/lib/api";

interface MicrophoneButtonProps {
  state: AssistantState;
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  onInterrupt?: () => void;
  disabled?: boolean;
}

export function MicrophoneButton({
  state,
  isRecording,
  onStart,
  onStop,
  onInterrupt,
  disabled,
}: MicrophoneButtonProps) {
  const isSpeaking = state === "speaking";
  const isThinking = state === "thinking";

  const handleClick = () => {
    if (isSpeaking && onInterrupt) {
      onInterrupt();
      return;
    }
    if (isRecording) {
      onStop();
    } else if (!isThinking) {
      onStart();
    }
  };

  return (
    <div className="relative flex items-center justify-center">
      {(isRecording || isSpeaking) && (
        <>
          <motion.div
            className={cn(
              "absolute h-24 w-24 rounded-full",
              isRecording ? "bg-emerald-500/20" : "bg-violet-500/20"
            )}
            animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className={cn(
              "absolute h-20 w-20 rounded-full",
              isRecording ? "bg-emerald-500/30" : "bg-violet-500/30"
            )}
            animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
          />
        </>
      )}

      <Button
        size="xl"
        variant={isRecording ? "destructive" : isSpeaking ? "secondary" : "default"}
        className={cn(
          "relative z-10 rounded-full shadow-2xl transition-transform hover:scale-105 active:scale-95",
          isRecording && "shadow-emerald-500/40",
          isSpeaking && "shadow-violet-500/40"
        )}
        onClick={handleClick}
        disabled={disabled || isThinking}
        aria-label={isRecording ? "Stop recording" : isSpeaking ? "Interrupt" : "Start recording"}
      >
        {isRecording ? (
          <Square className="h-8 w-8 fill-current" />
        ) : isSpeaking ? (
          <MicOff className="h-8 w-8" />
        ) : (
          <Mic className="h-8 w-8" />
        )}
      </Button>
    </div>
  );
}
