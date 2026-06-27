"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { api, type AssistantState } from "@/lib/api";

interface AvatarPlayerProps {
  state: AssistantState;
  avatarId?: string | null;
  onSessionReady?: (sessionId: string) => void;
  className?: string;
}

export function AvatarPlayer({ state, avatarId, onSessionReady, className }: AvatarPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [sessionInfo, setSessionInfo] = useState<{ id: string } | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const isSpeaking = state === "speaking";
  const isThinking = state === "thinking";
  const isListening = state === "listening";

  useEffect(() => {
    let currentSessionId: string | null = null;
    let isActive = true;

    async function initSession() {
      try {
        setIsInitializing(true);
        // 1. Create Session
        const sessionRes = await api.createAvatarSession(avatarId || undefined);
        if (sessionRes.error || !isActive) {
          setIsInitializing(false);
          return;
        }

        const sessionId = sessionRes.session_id;
        currentSessionId = sessionId;
        const iceServers = sessionRes.ice_servers || [{ urls: "stun:stun.l.google.com:19302" }];

        // 2. Setup WebRTC
        const pc = new RTCPeerConnection({ iceServers });
        pcRef.current = pc;

        pc.ontrack = (event) => {
          if (videoRef.current && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
          }
        };

        pc.onicecandidate = (event) => {
          if (event.candidate) {
          api.sendIceCandidate(sessionId, event.candidate).catch(() => {});
          }
        };

        pc.addTransceiver("video", { direction: "recvonly" });
        pc.addTransceiver("audio", { direction: "recvonly" });

        // 3. Negotiate SDP
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const startRes = await api.startAvatarSessionWithSDP(
          sessionId,
          offer.sdp as string,
          offer.type as string
        );

        if (startRes.error || !isActive) {
          setIsInitializing(false);
          return;
        }

        await pc.setRemoteDescription(new RTCSessionDescription({
          type: startRes.type as RTCSdpType,
          sdp: startRes.sdp,
        }));

        setSessionInfo({ id: sessionId });
        if (onSessionReady) onSessionReady(sessionId);
      } catch (err) {
        // Fallback handled by sessionInfo remaining null
      } finally {
        if (isActive) setIsInitializing(false);
      }
    }

    initSession();

    return () => {
      isActive = false;
      if (pcRef.current) {
        pcRef.current.close();
        pcRef.current = null;
      }
      if (currentSessionId) {
        api.stopAvatarSession(currentSessionId).catch(() => {});
      }
    };
  }, [avatarId, onSessionReady]);

  return (
    <div className={cn("relative aspect-[3/4] w-full max-w-sm overflow-hidden rounded-3xl bg-black", className)}>
      <div className="absolute inset-0 bg-gradient-to-b from-violet-500/10 to-transparent z-10 pointer-events-none" />

      {isInitializing && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/50 backdrop-blur-sm">
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-2 w-2 rounded-full bg-violet-400"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
          </div>
        </div>
      )}

      {/* WebRTC Video Stream */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className={cn(
          "absolute inset-0 h-full w-full object-cover transition-opacity duration-1000",
          sessionInfo ? "opacity-100" : "opacity-0"
        )}
      />

      {/* Fallback avatar image if WebRTC not ready yet */}
      {!sessionInfo && (
        <motion.img
          src="/avatar.png"
          alt="Avatar Fallback"
          className="absolute inset-0 h-full w-full object-cover"
        />
      )}

      {/* Speaking Overlay Effect */}
      {isSpeaking && sessionInfo && (
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
