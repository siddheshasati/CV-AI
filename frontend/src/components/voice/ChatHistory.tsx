"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { User, Bot } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatTime } from "@/lib/utils";
import type { ChatMessage } from "@/lib/api";

interface ChatHistoryProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  className?: string;
}

export function ChatHistory({ messages, isLoading, className }: ChatHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className={cn("flex h-full flex-col", className)}>
      <ScrollArea className="h-full pr-2">
        <div className="space-y-4 p-1">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center py-12 text-center text-sm text-muted-foreground">
              <Bot className="mb-3 h-10 w-10 opacity-40" />
              <p>Start a conversation by speaking or typing</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-3",
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                  msg.role === "user" ? "bg-violet-600/30" : "bg-emerald-500/20"
                )}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-violet-300" />
                ) : (
                  <Bot className="h-4 w-4 text-emerald-300" />
                )}
              </div>
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                  msg.role === "user"
                    ? "bg-violet-600/20 text-foreground"
                    : "border border-white/10 bg-white/5 text-foreground/90"
                )}
              >
                {msg.content}
                {msg.timestamp && (
                  <p className="mt-1 text-[10px] opacity-50">{formatTime(msg.timestamp)}</p>
                )}
              </div>
            </motion.div>
          ))}

          {isLoading && (
            <div className="space-y-2 px-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>
    </div>
  );
}
