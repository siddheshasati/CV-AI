"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, type AssistantState, type ChatMessage } from "@/lib/api";
import { base64ToBlob } from "@/lib/utils";

interface UseVoiceAssistantOptions {
  voiceId?: string | null;
  avatarSessionId?: string | null;
  onAvatarSession?: (id: string) => void;
  speechRate?: number;
}

export function useVoiceAssistant(options: UseVoiceAssistantOptions = {}) {
  const [state, setState] = useState<AssistantState>("idle");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const avatarSessionRef = useRef<string | null>(options.avatarSessionId || null);

  useEffect(() => {
    avatarSessionRef.current = options.avatarSessionId || null;
  }, [options.avatarSessionId]);

  const playAudio = useCallback(async (base64: string) => {
    if (!base64) return;
    const blob = base64ToBlob(base64);
    const url = URL.createObjectURL(blob);
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.playbackRate = options.speechRate || 1.0;
    setState("speaking");
    await new Promise<void>((resolve) => {
      audio.onended = () => {
        URL.revokeObjectURL(url);
        resolve();
      };
      audio.onerror = () => resolve();
      audio.play().catch(() => resolve());
    });
    setState("idle");
  }, [options.speechRate]);

  const connectWebSocket = useCallback((): Promise<WebSocket> => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return Promise.resolve(wsRef.current);
    }

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(`${api.wsUrl}/ws/voice`);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ type: "ping" }));
        resolve(ws);
      };
      ws.onerror = () => {
        setError("WebSocket connection failed");
        reject(new Error("WebSocket connection failed"));
      };
    });
  }, []);

  const sendTextStream = useCallback(
    async (message: string) => {
      setState("thinking");
      setResponse("");
      setActiveTools([]);
      setError(null);

      const ws = await connectWebSocket();
      let fullResponse = "";
      const audioChunks: string[] = [];

      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("Request timeout")), 60000);

        ws.onmessage = async (event) => {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case "conversation_id":
              setConversationId(data.conversation_id);
              break;
            case "text_delta":
              fullResponse += data.content;
              setResponse(fullResponse);
              break;
            case "tool_start":
              setActiveTools((prev) => [...prev, data.tool]);
              break;
            case "tool_end":
              break;
            case "audio_chunk":
              audioChunks.push(data.data);
              break;
            case "blocked":
              fullResponse = data.message;
              setResponse(fullResponse);
              setMessages((prev) => [
                ...prev,
                { role: "user", content: message, timestamp: new Date().toISOString() },
                { role: "assistant", content: data.message, timestamp: new Date().toISOString() },
              ]);
              break;
            case "done":
              clearTimeout(timeout);
              if (data.response) fullResponse = data.response;
              setMessages((prev) => [
                ...prev,
                { role: "user", content: message, timestamp: new Date().toISOString() },
                {
                  role: "assistant",
                  content: fullResponse,
                  timestamp: new Date().toISOString(),
                  metadata: { tools: data.tools_used },
                },
              ]);
              setResponse(fullResponse);
              setState("speaking");

              if (audioChunks.length > 0) {
                const combined = audioChunks.join("");
                await playAudio(combined);
              } else if (data.audio) {
                await playAudio(data.audio);
              } else {
                setState("idle");
              }
              resolve();
              break;
            case "error":
              clearTimeout(timeout);
              setError(data.message);
              setState("error");
              reject(new Error(data.message));
              break;
          }
        };

        ws.send(
          JSON.stringify({
            type: "text",
            message,
            conversation_id: conversationId,
            avatar_session_id: avatarSessionRef.current,
            voice_id: options.voiceId,
          })
        );
      });
    },
    [connectWebSocket, conversationId, options.voiceId, playAudio]
  );

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (blob.size === 0) {
          setState("idle");
          return;
        }

        setState("thinking");
        try {
          const result = await api.sendVoice(
            blob,
            conversationId || undefined,
            avatarSessionRef.current || undefined,
            options.voiceId || undefined
          );

          setConversationId(result.conversation_id);
          setTranscript(result.transcript || "");
          setResponse(result.response || "");

          setMessages((prev) => [
            ...prev,
            {
              role: "user",
              content: result.transcript || "",
              timestamp: new Date().toISOString(),
            },
            {
              role: "assistant",
              content: result.response || "",
              timestamp: new Date().toISOString(),
              metadata: { tools: result.tools_used, blocked: result.blocked },
            },
          ]);

          if (result.audio_base64) {
            await playAudio(result.audio_base64);
          } else {
            setState("idle");
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : "Voice processing failed");
          setState("error");
        }
      };

      recorder.start(250);
      setIsRecording(true);
      setState("listening");
      setTranscript("");
    } catch {
      setError("Microphone access denied");
      setState("error");
    }
  }, [conversationId, options.voiceId, playAudio]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  const interrupt = useCallback(async () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (avatarSessionRef.current) {
      try {
        await api.interruptAvatar(avatarSessionRef.current);
      } catch {
        /* ignore */
      }
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "interrupt", avatar_session_id: avatarSessionRef.current })
      );
    }
    setState("idle");
  }, []);

  const sendText = useCallback(
    async (message: string) => {
      if (!message.trim()) return;
      try {
        await sendTextStream(message.trim());
      } catch {
        /* error already set */
      }
    },
    [sendTextStream]
  );

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      audioRef.current?.pause();
    };
  }, []);

  return {
    state,
    messages,
    conversationId,
    transcript,
    response,
    activeTools,
    isRecording,
    error,
    analyser: analyserRef.current,
    startRecording,
    stopRecording,
    sendText,
    interrupt,
    setMessages,
    setConversationId,
  };
}
