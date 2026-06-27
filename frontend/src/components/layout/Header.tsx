"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { Moon, Sun, Settings, Sparkles, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface HeaderProps {
  showHistory?: boolean;
  onToggleHistory?: () => void;
  className?: string;
}

export function Header({ showHistory, onToggleHistory, className }: HeaderProps) {
  const { theme, setTheme } = useTheme();

  return (
    <header
      className={cn(
        "flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-3 backdrop-blur-xl md:px-6",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-500/25">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-tight md:text-base">Voice AI</h1>
          <p className="text-[10px] text-muted-foreground md:text-xs">Powered by GPT & ElevenLabs</p>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {onToggleHistory && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleHistory}
            className={cn(showHistory && "bg-white/10")}
            aria-label="Toggle chat history"
          >
            <MessageSquare className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
        <Link href="/settings">
          <Button variant="ghost" size="icon" aria-label="Settings">
            <Settings className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </header>
  );
}
