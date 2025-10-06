# AI Science Shorts Studio 🎬🤖

**HackOdisha 5.0 Project | Team: Sons of SatyaMurthy**

## 🎯 Project Overview

AI Science Shorts Studio is an automated video generation platform that creates engaging 30-60 second vertical videos from scripts using AI-powered workflows. Built with **Orkes Conductor** for workflow orchestration and **Akash Network** for decentralized GPU compute.

## 🚀 What It Does

**One-Click Video Generation:**
- Input: Text script or topic
- Output: Professional vertical video with AI-generated visuals, voiceover, and captions
- Perfect for: Educational content, social media, science communication

**Two Generation Modes:**
1. **Script Provided**: User provides script → Generate visuals + audio
2. **AI-Written Script**: Topic input → AI writes script → Generate complete video

## 🏗️ Architecture

### **The Cast (Who Does What)**

* **Next.js Frontend (UI):** Single-page interface to start runs and watch live status. Never talks to Akash or Orkes directly—only to your backend.
* **FastAPI Backend (Control Plane):** Single public API that orchestrates everything. Starts runs, manages Orkes workflows, calls Akash GPU services, handles Cloudflare R2 artifacts, and streams live updates to frontend.
* **Orkes Conductor (The Brain):** Workflow engine that executes step-by-step pipeline (facts → script → storyboard → media generation → TTS → assembly → finish). Handles retries, timeouts, and optional human-in-the-loop.
* **Akash Network (The Muscle):** Decentralized GPU infrastructure hosting model services:
  * `t2i` (text-to-image, FLUX/SDXL)
  * `i2v` (image-to-video, AnimateDiff/SVD)
  * `ffmpeg` (video assembly, overlays, audio mixing)
* **Cloudflare R2 (Artifacts):** S3-compatible storage for all media assets. Everything private with pre-signed URLs.
* **External APIs:** LLM for script generation, TTS for voiceover (with self-hosted fallback).

### **How They Connect (HTTP Only)**

* **Frontend → Backend:** HTTPS requests only. Browser never touches Akash, Orkes, or R2 directly.
* **Backend → Orkes:** Starts workflows via API. Orkes calls back to backend task endpoints.
* **Backend ↔ Akash:** Backend calls warm GPU endpoints with pre-signed R2 URLs for media I/O.
* **Backend ↔ R2:** Generates short-lived upload/download URLs for all artifacts.
* **Backend ↔ APIs:** Direct calls to LLM/TTS with server-side keys.

### **Complete Video Generation Flow**

1. **User clicks Generate** → Frontend sends options to backend → Backend creates `run_id`, starts Orkes workflow, returns immediately
2. **Frontend navigates to /run/{id}** → Subscribes to server-sent events for live updates
3. **Orkes executes pipeline** by calling backend endpoints:
   * **CollectFacts:** Gather trending topics, write facts.json to R2
   * **WriteScript:** LLM generates ≤120 word script, store script.json
   * **StoryboardPlan:** Create shots.json (prompts, timing, motion selection)
   * **GenerateMedia:** Parallel generation of 5 stills + 1-2 animated clips via Akash
   * **TextToSpeech:** Generate narration.wav with timing map
   * **GenerateCaptions:** Build captions.srt aligned to audio
   * **AssembleSegments:** Akash ffmpeg combines all assets into final.mp4
   * **NotifyComplete:** Emit final event with cost breakdown
4. **Frontend shows progress** → Live step updates, final video player, cost estimate

## 💰 Why Akash Network?

**Cost Efficiency:**
- Traditional Cloud: $2-5 per video
- **Akash Network**: $0.02-0.03 per video
- 60-100x cost reduction

**Decentralized Benefits:**
- No vendor lock-in
- Permissionless access to GPU compute
- Global distribution of processing power
- Censorship-resistant content creation

**Technical Requirements:**
- GPU-intensive AI models (FLUX.1, Stable Video Diffusion)
- Parallel processing for multiple video segments
- Scalable infrastructure for batch processing

## 🎯 Target Market & Impact

**Primary Users:**
- Educators and science communicators
- Content creators and influencers
- Educational institutions
- Science organizations and NGOs

**Market Problem:**
- High cost of professional video production
- Technical barriers to AI-powered content creation
- Centralized platforms limiting creative freedom

**Our Solution:**
- Democratizes professional video creation
- Reduces production cost by 99%
- Enables rapid content iteration and testing

## 🏆 HackOdisha 5.0 Track Alignment

**Orkes Conductor AI Track:**
- Complex AI workflow orchestration
- Multi-step pipeline with conditional logic
- Real-time monitoring and error handling
- Human-in-the-loop capabilities

**Akash Network Tracks:**
- **Best Use of Akash GPUs**: Multiple GPU-intensive AI models
- **Best Use of Akash AI**: Complete AI pipeline deployment
- **Best Deployment**: Auto-scaling, cost-optimized infrastructure
- **Ready to Launch**: Clear business model and market demand

## 🛠️ Technical Stack

**Frontend:** Next.js, React, Tailwind CSS
**Backend:** FastAPI (Python), server-sent events
**Workflow:** Orkes Conductor
**Compute:** Akash Network (warm GPU leases)
**AI Models:** FLUX.1/SDXL (t2i), AnimateDiff/SVD (i2v), TTS
**Storage:** Cloudflare R2 (private buckets + pre-signed URLs)
**Video Processing:** FFmpeg on Akash
**State Management:** Redis for idempotent task results

## 🚧 Development Plan (36-Hour Hackathon)

### **Phase 1: Infrastructure Setup (Hours 0-12)**
- Deploy FastAPI backend with public URL for Orkes callbacks
- Set up warm Akash GPU lease with t2i/i2v/ffmpeg endpoints
- Configure Orkes Conductor with task definitions and retry policies
- Create Cloudflare R2 bucket with CORS for pre-signed URLs

### **Phase 2: Pipeline Integration (Hours 12-24)**
- Implement all Orkes task endpoints in backend
- Test complete workflow: facts → script → storyboard → media → assembly
- Build Next.js frontend with SSE streaming and video player
- Integration testing with real GPU workloads

### **Phase 3: Demo & Polish (Hours 24-36)**
- End-to-end testing with multiple video generations
- Performance optimization and error handling
- Live demo preparation with cost tracking
- Judge presentation materials

## 📊 What Judges Will See

1. **One-Click Generation**: User clicks Generate → Live Orkes DAG fills step-by-step
2. **Decentralized Proof**: Open Akash lease panel/logs to show GPU execution
3. **Cost Transparency**: Real-time cost chip showing GPU minutes × hourly rate
4. **Live Workflow**: Server-sent events stream each pipeline step completion
5. **Final Result**: Professional vertical video plays in-browser with source attribution

## 🎬 Expected Output

**Input**: "Explain quantum computing in 45 seconds"
**Output**: Professional video with:
- 5 AI-generated visuals from SDXL
- Synchronized voiceover from TTS
- Ken Burns transitions
- Professional captions
- Vertical format (720x1280)

## 🔮 Future Roadmap

**Phase 1 (Post-Hackathon):**
- Multi-language support
- Advanced animation options
- Social media platform integration

**Phase 2:**
- Live streaming integration
- Collaborative editing features
- Analytics and performance tracking

**Phase 3:**
- Enterprise white-label solutions
- API marketplace for developers
- Advanced AI personalization

## 🙏 Akash Network Credit Request

We're requesting Akash credits to:
- Deploy and test AI models during development
- Run extensive demos during HackOdisha 5.0
- Showcase cost comparison against traditional cloud providers
- Demonstrate real-world scalability of decentralized compute

**Estimated Usage:**
- Development: 20 GPU hours
- Testing: 15 GPU hours  
- Demo: 10 GPU hours

**Cost Reality:**
- Per video: 4-6 GPU minutes on RTX 3090/4090
- Wall-clock time: ~60-90 seconds when warm
- Estimated cost: $0.02-0.03 per video vs $2+ on traditional cloud