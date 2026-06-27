const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const api = {
  baseUrl: API_URL,
  wsUrl: WS_URL,

  async health() {
    const res = await fetch(`${API_URL}/api/v1/health`);
    return res.json();
  },

  async getSettings() {
    const res = await fetch(`${API_URL}/api/v1/settings`);
    return res.json();
  },

  async updateSettings(data: Partial<UserSettings>) {
    const res = await fetch(`${API_URL}/api/v1/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async getConversations() {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations`);
    return res.json();
  },

  async getConversation(id: string) {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations/${id}`);
    return res.json();
  },

  async deleteConversation(id: string) {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations/${id}`, { method: "DELETE" });
    return res.json();
  },

  async sendVoice(
    audioBlob: Blob,
    conversationId?: string,
    avatarSessionId?: string,
    voiceId?: string
  ) {
    const form = new FormData();
    form.append("audio", audioBlob, "recording.webm");
    if (conversationId) form.append("conversation_id", conversationId);
    if (avatarSessionId) form.append("avatar_session_id", avatarSessionId);
    if (voiceId) form.append("voice_id", voiceId);

    const res = await fetch(`${API_URL}/api/v1/chat/voice`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async sendText(message: string, conversationId?: string) {
    const res = await fetch(`${API_URL}/api/v1/chat/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createAvatarSession(avatarId?: string) {
    const url = avatarId
      ? `${API_URL}/api/v1/avatar/session?avatar_id=${avatarId}`
      : `${API_URL}/api/v1/avatar/session`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) return { error: `HTTP ${res.status}` };
    return res.json();
  },

  async startAvatarSession(sessionId: string) {
    // Start without SDP (legacy / no-op start)
    const res = await fetch(`${API_URL}/api/v1/avatar/session/${sessionId}/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (!res.ok) return { error: `HTTP ${res.status}` };
    return res.json();
  },

  async startAvatarSessionWithSDP(
    sessionId: string,
    sdp: string,
    type: string
  ): Promise<{ sdp?: string; type?: string; error?: string }> {
    const res = await fetch(`${API_URL}/api/v1/avatar/session/${sessionId}/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sdp, type }),
    });
    if (!res.ok) return { error: `HTTP ${res.status}: ${await res.text()}` };
    return res.json();
  },

  async sendIceCandidate(
    sessionId: string,
    candidate: RTCIceCandidateInit
  ): Promise<void> {
    await fetch(`${API_URL}/api/v1/avatar/session/${sessionId}/ice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate: candidate.candidate ?? "",
        sdpMid: candidate.sdpMid ?? null,
        sdpMLineIndex: candidate.sdpMLineIndex ?? null,
        usernameFragment: candidate.usernameFragment ?? null,
      }),
    });
  },

  async interruptAvatar(sessionId: string) {
    const res = await fetch(`${API_URL}/api/v1/avatar/session/${sessionId}/interrupt`, { method: "POST" });
    return res.json();
  },

  async stopAvatarSession(sessionId: string) {
    const res = await fetch(`${API_URL}/api/v1/avatar/session/${sessionId}`, { method: "DELETE" });
    return res.json();
  },

  async getAvatarToken() {
    const res = await fetch(`${API_URL}/api/v1/avatar/token`, { method: "POST" });
    return res.json();
  },
};

export type AssistantState = "idle" | "listening" | "thinking" | "speaking" | "error";

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface UserSettings {
  voice_id: string | null;
  avatar_id: string | null;
  theme: string;
  language: string;
  auto_search: boolean;
  speech_rate: number;
}
