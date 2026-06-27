"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Video, VideoOff, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AssistantState } from "@/lib/api";

interface AvatarPlayerProps {
  state: AssistantState;
  avatarId?: string | null;
  onSessionReady?: (sessionId: string) => void;
  className?: string;
}

export function AvatarPlayer({ state, avatarId, onSessionReady, className }: AvatarPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "connecting" | "ready" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [enabled, setEnabled] = useState(false);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  // Keep sessionIdRef in sync so cleanup always has latest value
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const cleanup = useCallback(async () => {
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    const sid = sessionIdRef.current;
    if (sid) {
      try {
        await api.stopAvatarSession(sid);
      } catch {
        /* ignore cleanup errors */
      }
    }
    setSessionId(null);
    sessionIdRef.current = null;
    setStatus("idle");
    setEnabled(false);
    setErrorMsg("");
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const connectAvatar = useCallback(async () => {
    setStatus("connecting");
    setErrorMsg("");

    try {
      // Step 1: Create HeyGen session — get session_id and ICE servers
      const session = await api.createAvatarSession(avatarId || undefined);
      if (session.error) {
        setErrorMsg(session.error);
        setStatus("error");
        return;
      }

      const sid = session.session_id as string;
      setSessionId(sid);
      sessionIdRef.current = sid;
      // Notify parent immediately so the voice pipeline has the session ID
      onSessionReady?.(sid);

      // Step 2: Create RTCPeerConnection with HeyGen's ICE servers
      const iceServers: RTCIceServer[] = session.ice_servers || [
        { urls: "stun:stun.l.google.com:19302" },
      ];
      const pc = new RTCPeerConnection({ iceServers });
      pcRef.current = pc;

      // Step 3: Set up media track handler — attach stream to video element
      pc.ontrack = (event) => {
        if (videoRef.current && event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
          videoRef.current.play().catch(() => {});
          setStatus("ready");
          setEnabled(true);
        }
      };

      // Step 4: Add transceivers so we get audio+video tracks from HeyGen
      pc.addTransceiver("video", { direction: "recvonly" });
      pc.addTransceiver("audio", { direction: "recvonly" });

      // Step 5: Create SDP offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Step 6: Send SDP offer to HeyGen (via our backend), get SDP answer back
      const sdpAnswer = await api.startAvatarSessionWithSDP(
        sid,
        offer.sdp!,
        offer.type
      );

      if (sdpAnswer.error) {
        throw new Error(sdpAnswer.error);
      }

      if (!sdpAnswer.sdp || !sdpAnswer.type) {
        throw new Error("HeyGen did not return an SDP answer");
      }

      // Step 7: Set HeyGen's SDP answer as remote description
      await pc.setRemoteDescription(
        new RTCSessionDescription({ sdp: sdpAnswer.sdp, type: sdpAnswer.type as RTCSdpType })
      );

      // Step 8: Forward ICE candidates to HeyGen as they are gathered
      pc.onicecandidate = async (event) => {
        if (event.candidate) {
          try {
            await api.sendIceCandidate(sid, event.candidate.toJSON());
          } catch {
            /* non-fatal — some candidates may be redundant */
          }
        }
      };

      // Step 9: Monitor connection state
      pc.oniceconnectionstatechange = () => {
        const iceState = pc.iceConnectionState;
        if (iceState === "connected" || iceState === "completed") {
          // Connection is live; ontrack should fire shortly if not already
        } else if (iceState === "failed" || iceState === "disconnected") {
          setStatus("error");
          setErrorMsg("WebRTC connection failed — check network or avatar ID");
          setEnabled(false);
        }
      };

    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setErrorMsg(msg);
      setStatus("error");
      setEnabled(false);
      // Clean up any partially-created peer connection
      if (pcRef.current) {
        pcRef.current.close();
        pcRef.current = null;
      }
    }
  }, [avatarId, onSessionReady]);

  // Auto-connect avatar immediately
  useEffect(() => {
    if (status === "idle") {
      connectAvatar();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      // Run cleanup synchronously-ish on unmount (fire-and-forget)
      if (pcRef.current) {
        pcRef.current.close();
        pcRef.current = null;
      }
      const sid = sessionIdRef.current;
      if (sid) {
        api.stopAvatarSession(sid).catch(() => {});
      }
    };
  }, []);

  const isSpeaking = state === "speaking";
  const isThinking = state === "thinking";

  return (
    <div className={cn("relative aspect-[3/4] w-full max-w-sm overflow-hidden rounded-3xl", className)}>
      <div className="absolute inset-0 bg-gradient-to-b from-violet-500/10 to-transparent" />

      {/* Live avatar video */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={false}
        className={cn(
          "h-full w-full object-cover transition-opacity duration-500",
          enabled && status === "ready" ? "opacity-100" : "opacity-0 absolute inset-0"
        )}
      />

      {/* Fallback / loading UI */}
      {(!enabled || status !== "ready") && (
        <div className="flex h-full flex-col items-center justify-center gap-4 bg-white/5 p-6 backdrop-blur-xl">
          {status === "connecting" ? (
            <>
              <Loader2 className="h-10 w-10 animate-spin text-violet-400" />
              <p className="text-sm text-muted-foreground">Connecting avatar…</p>
            </>
          ) : (
            <>
              <motion.div
                animate={isSpeaking ? { scale: [1, 1.02, 1] } : {}}
                transition={{ duration: 0.5, repeat: isSpeaking ? Infinity : 0 }}
                className="relative flex h-40 w-40 items-center justify-center rounded-full bg-gradient-to-br from-violet-600/40 to-indigo-600/40"
              >
                <div className="flex h-32 w-32 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 shadow-2xl shadow-violet-500/30">
                  <span className="text-5xl">🤖</span>
                </div>
                {isSpeaking && (
                  <motion.div
                    className="absolute inset-0 rounded-full border-2 border-violet-400"
                    animate={{ scale: [1, 1.15, 1], opacity: [0.8, 0, 0.8] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                  />
                )}
                {isThinking && (
                  <motion.div
                    className="absolute -bottom-2 flex gap-1"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className="h-2 w-2 rounded-full bg-amber-400"
                        animate={{ y: [0, -6, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.1 }}
                      />
                    ))}
                  </motion.div>
                )}
              </motion.div>

              {/* Error message hidden for seamless fallback */}

              <p className="text-center text-sm text-muted-foreground">
                {status === "error"
                  ? "Avatar unavailable — using animated fallback"
                  : "Connecting to avatar..."}
              </p>
            </>
          )}
        </div>
      )}

      {/* Disconnect button (only when connected) */}
      {enabled && (
        <button
          onClick={cleanup}
          className="absolute right-3 top-3 rounded-full bg-black/40 p-2 text-white backdrop-blur transition hover:bg-black/60"
          aria-label="Disconnect avatar"
        >
          <VideoOff className="h-4 w-4" />
        </button>
      )}

      {isSpeaking && enabled && (
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-violet-600/80 px-3 py-1 text-xs font-medium text-white backdrop-blur">
          Speaking...
        </div>
      )}
    </div>
  );
}
