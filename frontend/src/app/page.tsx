"use client";

import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, AlertCircle } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { AvatarPlayer } from "@/components/voice/AvatarPlayer";
import { ChatHistory } from "@/components/voice/ChatHistory";
import { LiveTranscription } from "@/components/voice/LiveTranscription";
import { MicrophoneButton } from "@/components/voice/MicrophoneButton";
import { ThinkingAnimation } from "@/components/voice/ThinkingAnimation";
import { TypingEffect } from "@/components/voice/TypingEffect";
import { Waveform } from "@/components/voice/Waveform";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useVoiceAssistant } from "@/hooks/useVoiceAssistant";
import { api, type UserSettings } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function HomePage() {
  const [showHistory, setShowHistory] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [avatarSessionId, setAvatarSessionId] = useState<string | null>(null);

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => {});
  }, []);

  const assistant = useVoiceAssistant({
    voiceId: settings?.voice_id,
    avatarSessionId,
    speechRate: settings?.speech_rate,
  });

  const handleSendText = useCallback(async () => {
    if (!textInput.trim() || assistant.state === "thinking") return;
    const msg = textInput;
    setTextInput("");
    await assistant.sendText(msg);
  }, [textInput, assistant]);

  const statusLabel = {
    idle: "Ready",
    listening: "Listening",
    thinking: "Thinking",
    speaking: "Speaking",
    error: "Error",
  }[assistant.state];

  return (
    <div className="gradient-bg flex min-h-dvh flex-col">
      <Header showHistory={showHistory} onToggleHistory={() => setShowHistory((v) => !v)} />

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4 p-4 md:flex-row md:gap-6 md:p-6">
        {/* Chat sidebar */}
        <AnimatePresence>
          {showHistory && (
            <motion.aside
              initial={{ opacity: 0, x: -20, width: 0 }}
              animate={{ opacity: 1, x: 0, width: "auto" }}
              exit={{ opacity: 0, x: -20, width: 0 }}
              className="w-full shrink-0 md:w-80"
            >
              <Card className="h-[calc(100dvh-8rem)] md:h-[calc(100dvh-7rem)]">
                <CardContent className="flex h-full flex-col p-4">
                  <h2 className="mb-3 text-sm font-semibold text-muted-foreground">Chat History</h2>
                  <ChatHistory
                    messages={assistant.messages}
                    isLoading={assistant.state === "thinking"}
                    className="flex-1"
                  />
                </CardContent>
              </Card>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main voice interface */}
        <div className="flex flex-1 flex-col items-center gap-6">
          <div className="grid w-full max-w-4xl grid-cols-1 items-start gap-6 lg:grid-cols-2">
            {/* Avatar */}
            <Card className="overflow-hidden">
              <CardContent className="p-4">
                <AvatarPlayer
                  state={assistant.state}
                  avatarId={settings?.avatar_id}
                  onSessionReady={setAvatarSessionId}
                />
              </CardContent>
            </Card>

            {/* Response panel */}
            <Card className="flex min-h-[320px] flex-col">
              <CardContent className="flex flex-1 flex-col gap-4 p-6">
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "rounded-full px-3 py-1 text-xs font-medium",
                      assistant.state === "listening" && "bg-emerald-500/20 text-emerald-400",
                      assistant.state === "thinking" && "bg-amber-500/20 text-amber-400",
                      assistant.state === "speaking" && "bg-violet-500/20 text-violet-400",
                      assistant.state === "idle" && "bg-white/10 text-muted-foreground",
                      assistant.state === "error" && "bg-red-500/20 text-red-400"
                    )}
                  >
                    {statusLabel}
                  </span>
                </div>

                <LiveTranscription
                  transcript={assistant.transcript}
                  isListening={assistant.isRecording}
                />

                <ThinkingAnimation
                  visible={assistant.state === "thinking"}
                  tools={assistant.activeTools}
                />

                {assistant.response && (
                  <TypingEffect text={assistant.response} speed={12} />
                )}

                {assistant.error && (
                  <div className="flex items-center gap-2 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {assistant.error}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Waveform + Mic */}
          <div className="flex w-full max-w-lg flex-col items-center gap-6">
            <Waveform state={assistant.state} analyser={assistant.analyser} />

            <MicrophoneButton
              state={assistant.state}
              isRecording={assistant.isRecording}
              onStart={assistant.startRecording}
              onStop={assistant.stopRecording}
              onInterrupt={assistant.interrupt}
              disabled={assistant.state === "thinking"}
            />

            <p className="text-center text-xs text-muted-foreground">
              {assistant.isRecording
                ? "Tap to stop recording"
                : assistant.state === "speaking"
                  ? "Tap to interrupt"
                  : "Hold to speak or type below"}
            </p>
          </div>

          {/* Text input fallback */}
          <div className="flex w-full max-w-lg gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendText()}
              placeholder="Or type a message..."
              disabled={assistant.state === "thinking" || assistant.isRecording}
              className="flex-1 rounded-full border border-white/10 bg-white/5 px-5 py-3 text-sm backdrop-blur transition focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20 disabled:opacity-50"
            />
            <Button
              size="icon"
              onClick={handleSendText}
              disabled={!textInput.trim() || assistant.state === "thinking"}
              className="rounded-full"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
