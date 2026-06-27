"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThinkingAnimationProps {
  visible: boolean;
  tools?: string[];
  className?: string;
}

const toolLabels: Record<string, string> = {
  get_weather: "Checking weather",
  web_search: "Searching the web",
  get_news: "Fetching news",
  wikipedia_search: "Reading Wikipedia",
  get_current_time: "Getting time",
  get_stock_price: "Looking up stocks",
};

export function ThinkingAnimation({ visible, tools = [], className }: ThinkingAnimationProps) {
  if (!visible) return null;

  const label =
    tools.length > 0
      ? toolLabels[tools[tools.length - 1]] || "Using tools"
      : "Thinking";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      className={cn("flex items-center justify-center gap-3", className)}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-500/20"
      >
        <Bot className="h-5 w-5 text-violet-400" />
      </motion.div>
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-violet-300">{label}</span>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="h-1.5 w-1.5 rounded-full bg-violet-400"
              animate={{ y: [0, -4, 0] }}
              transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}
