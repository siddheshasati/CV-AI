# CV AI: Conversational - Implementation Report

## 1. Adding a Photorealistic Human-like Interface

To add a human-like interface that closely resembles a real human and can actively speak and respond to prompts, we transitioned from a static UI image to a real-time **WebRTC** (Web Real-Time Communication) streaming video integration. 

### In-Depth Implementation Details:
- **Streaming Avatar API (HeyGen):** We utilized a third-party avatar streaming service (HeyGen) to generate the photorealistic video. HeyGen takes in text prompts and dynamically synthesizes both the audio and the lip-syncing video frames of a high-fidelity digital human on their remote servers.
- **WebRTC Peer Connection (`RTCPeerConnection`):** We replaced the static `<img>` fallback in the frontend with a native HTML5 `<video autoPlay playsInline>` element. We orchestrated a WebRTC handshake:
  1. The client requests a secure session token and ICE servers from our backend.
  2. The browser creates an `RTCPeerConnection` and generates a local Session Description Protocol (SDP) offer.
  3. The offer is sent to the backend, which forwards it to HeyGen, receiving a remote SDP answer in return.
  4. The client sets this remote description and begins exchanging ICE candidates for NAT traversal.
- **Media Binding:** Once the connection is established, the `ontrack` event fires, and the incoming media stream (containing the remote audio and video tracks) is bound to the `srcObject` of our `<video>` element, rendering the live photorealistic avatar directly in the DOM.
- **Dynamic Task Queuing:** When the user speaks or types a prompt, our backend orchestrates the LLM. As the LLM streams the response, the backend sends asynchronous `speak` tasks containing the text directly to the active HeyGen session, causing the avatar to seamlessly lip-sync the response in real-time.

## 2. Tools and Models Used

The architecture was built using a combination of specialized, cutting-edge AI models and robust web tools chosen for their low latency, high quality, and developer experience.

### Backend Infrastructure
- **FastAPI (Python):** Chosen for its native asynchronous capabilities (`asyncio`) and WebSockets support, allowing high-throughput concurrent connections necessary for real-time streaming pipelines.
- **OpenAI GPT-4o / Gemini 1.5 Pro (LLM):** Chosen as the core reasoning engine for their exceptional natural language processing, low time-to-first-token (TTFT), and robust function-calling capabilities.

### Video Generation & Voice
- **HeyGen Streaming Avatar API:** Chosen because it provides state-of-the-art, photorealistic video generation with ultra-low latency WebRTC streaming. Unlike traditional video rendering which takes minutes, HeyGen processes text into lip-synced video in under a second.
- **ElevenLabs (Fallback TTS):** Chosen for its unparalleled voice realism and emotion control. We use ElevenLabs when the user opts out of the video avatar but still wants high-fidelity conversational audio.

### Frontend Technologies
- **Next.js & React:** Chosen for its component-based architecture and robust state management.
- **WebRTC API:** Native browser API chosen because it is the industry standard for sub-second latency, peer-to-peer media streaming, outperforming HLS or traditional WebSocket binary streaming.

## 3. Reducing Lag and Latency in the Pipeline

Achieving conversational fluidity requires extreme latency optimizations across the entire stack. We implemented several advanced techniques to reduce the "Time to First Byte" (TTFB) of the video generation:

- **Sentence-Level Concurrent Buffering:** Instead of waiting for the LLM to generate the entire paragraph before sending it to the avatar API, we implemented a rolling sentence buffer. As the LLM streams tokens, we use Regex `([.!?;]+)` to detect sentence boundaries. As soon as a single sentence is complete, it is asynchronously dispatched to the avatar. This reduces the TTFB from several seconds down to a few hundred milliseconds.
- **Eliminating Double-Audio Processing:** We bypassed the intermediate ElevenLabs text-to-speech step when the avatar session is active. By routing the raw text directly to HeyGen (which handles its own internal TTS and video rendering simultaneously), we eliminated an unnecessary network hop and prevented double-audio echoes.
- **WebRTC UDP Transport:** By utilizing WebRTC instead of TCP-based WebSockets for media transport, the video frames and audio are streamed over UDP. This avoids TCP head-of-line blocking, ensuring that packet loss results in minor visual artifacts rather than catastrophic buffering delays, preserving the real-time conversational flow.
