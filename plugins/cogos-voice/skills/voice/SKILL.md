---
name: voice
description: Dual-modal communication protocol for voice-enabled AI development. Guides when to speak vs write, non-blocking speech patterns, and anti-patterns. Requires mod3 at localhost:7860. Tools differ by platform — see Platform Context section.
---

# Voice — Dual-Modal Communication

You have a voice. Use it intentionally.

## Platform Context

The voice tooling depends on where this skill is running:

**Hermes (gateway sessions — Telegram, Discord VC):**
- Primary tool: `voice_output(text, mode)` — registered by the `mod3_voice` plugin
  - `mode='audio'`: synthesize and play in the voice channel; no text posted
  - `mode='text'`: post to Discord text channel (or reply text); no audio
  - `mode='both'`: speak AND post text simultaneously
  - `mode='auto'` (default): if in an active voice channel → audio; otherwise → text
- Voice output is INTENTIONAL — calling `voice_output` is the only way audio is delivered. There is no reflex auto-TTS; if you don't call the tool, nothing is spoken.

**Discord VC mode (asymmetric default):** Agent reads voice input, responds in text by default. Call `voice_output(mode='audio')` when you want to speak a response aloud.

**Telegram:** `voice_output(mode='audio')` produces an OGG voice bubble delivered as a native voice message.

**Claude Code (via MCP):**
- `mcp__mcp_cogos_mod3_speak(text, session_id, voice, format='ogg')` — queue speech via mod3
- `mcp__mcp_cogos_mod3_stop(session_id)` — barge-in / cancel current speech
- `mcp__mcp_cogos_mod3_voices()` — list available voices
- `mcp__mcp_cogos_mod3_status()` — health and queue state

**Direct HTTP (any platform):**
```
POST localhost:7860/v1/speak
{"text": "...", "session_id": "..."}
```

---

## The Two Channels

| Channel | Persistence | Latency | Best for |
|---------|-------------|---------|----------|
| **Text** | Permanent (visible in conversation) | Instant | Code, structured data, decisions, diffs, anything the user will reference later |
| **Voice** | Ephemeral (heard once, not in transcript) | ~0.5s TTFA | Context, thinking out loud, status updates, conversational responses, emotional tone |

**The rule:** Voice carries the ephemeral. Text carries the persistent. Don't duplicate — use each channel for what it's good at.

---

## Non-Blocking Speech

`voice_output` (Hermes) and `mcp__mcp_cogos_mod3_speak` (Claude Code) are non-blocking — audio plays via mod3's drain thread while you continue working. This is the core capability: you can talk and act simultaneously.

```
voice_output("Looking into that now, give me a second.")  # returns immediately
# ... do the actual work here while user hears you ...
# ... write the structured result as text ...
```

**Do this:**
- Speak a brief orientation while performing the action
- Write the structured result as text — code, data, analysis
- The user hears your intent and sees your output simultaneously

**Don't do this:**
- Speak the same content you're about to write (redundant)
- Use speech for code, file paths, or anything the user needs to copy
- Block waiting for speech to finish

---

## When to Speak

**Speak when:**
- Acknowledging a request before starting work
- Giving a brief summary while detailed output renders as text
- Responding to conversational/emotional content where tone matters
- Explaining your reasoning while the code writes itself
- Something surprising happens (errors, discoveries, results)

**Write when:**
- Outputting code, configs, structured data
- Anything the user will reference, copy, or search for later
- Detailed technical analysis
- File paths, URLs, commands

**Both simultaneously (the power move):**
- Speak the high-level context while writing the detailed output
- "I found three issues" (voice) + the actual issue list (text)
- "Deploying now" (voice) + the deployment log (text)

---

## Voice Selection

Check `mcp__mcp_cogos_mod3_voices()` (Claude Code) or `voice_output` defaults (Hermes, mod3 default voice) to see what's available. Pick based on the moment:

- **Fast/lightweight voices:** Casual speech, quick acknowledgments, status updates
- **High-quality voices:** Longer, more considered speech where clarity matters
- **Expressive voices:** When emotional tone or emphasis matters

---

## Health and Queue State

Use `mcp__mcp_cogos_mod3_status()` (Claude Code) for service health and queue depth. Check when:
- The user reports audio issues
- You want to diagnose why something sounded wrong
- You're experimenting with different models/speeds

Key signals from the health response:
- `queue_depth` — number of pending jobs; > 0 means current job is queued
- `model_loaded` — whether the TTS model is ready

There is no per-job progress metric API. mod3 serializes playback internally; overlapping calls are queued, not dropped.

---

## Text Formatting for Prosody

Text formatting can affect speech output depending on the TTS engine:
- **ALL CAPS** may add emphasis: "how are YOU doing" stresses "you"
- **Ellipses** add pauses: "well... let me think..."
- **Punctuation** shapes intonation: questions rise, exclamations emphasize
- **Short sentences** produce cleaner prosody than long compound ones

---

## Anti-Patterns

- **Auto-TTS reflexes:** In Hermes, nothing is spoken unless `voice_output` is explicitly called. Don't assume text responses are auto-voiced.
- **Narrating your actions in speech:** Don't say "I'm going to read the file now." Just do it. Speak only when the user benefits from hearing it.
- **Long monologues:** Keep speech concise. If it's more than 3-4 sentences, it should probably be text.
- **Waiting for speech to finish:** The whole point is non-blocking. Don't poll for completion.
- **Using speech as a crutch for filler:** "Let me think about that..." is fine once. Don't stall with voice.
- **Speaking code:** Never. Code is text. Always.

---

## The Philosophy

Voice and text are not redundant channels — they're complementary modalities with different information densities and persistence profiles. Using both simultaneously is not showing off; it's the natural way to communicate when you have both available. A human explaining code talks while pointing at the screen. You speak while writing. Same instinct, same efficiency.

The user hears your intent. The user sees your output. Both arrive together. That's dual-modal communication.
