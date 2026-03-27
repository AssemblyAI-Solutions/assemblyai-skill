---
name: assemblyai
description: Use when implementing speech-to-text, audio transcription, real-time streaming STT, audio intelligence features, or voice AI using AssemblyAI APIs or SDKs. Use when user mentions AssemblyAI, voice agents, transcription, speaker diarization, PII redaction of audio, LLM Gateway for audio understanding, or applying LLMs to transcripts. Also use when building voice agents with LiveKit or Pipecat that need speech-to-text, or when the user is working with any audio/video processing pipeline that could benefit from transcription, even if they don't mention AssemblyAI by name.
---

# AssemblyAI Speech-to-Text and Voice AI

AssemblyAI provides speech-to-text APIs, audio intelligence models, and an LLM Gateway for applying language models to transcripts. This skill corrects common mistakes that training data gets wrong — deprecated APIs, discontinued SDKs, and non-obvious auth patterns.

## Authentication

**All endpoints use the same header:**
```
Authorization: YOUR_API_KEY
```
**NOT** `Authorization: Bearer ...` — just the raw API key, no Bearer prefix. This is the #1 mistake.

## Base URLs

| Service | US | EU |
|---------|----|----|
| REST API | `https://api.assemblyai.com` | `https://api.eu.assemblyai.com` |
| LLM Gateway | `https://llm-gateway.assemblyai.com/v1` | `https://llm-gateway.eu.assemblyai.com/v1` |
| Streaming v3 | `wss://streaming.assemblyai.com/v3/ws` | `wss://streaming.eu.assemblyai.com/v3/ws` |
| Streaming v2 (legacy) | `wss://api.assemblyai.com/v2/realtime/ws` | — |

## SDKs

| Language | Package | Status |
|----------|---------|--------|
| Python | `pip install assemblyai` | Active |
| JavaScript/TypeScript | `npm i assemblyai` | Active |
| Ruby | `assemblyai` gem | Active |
| Java | `assemblyai-java-sdk` | **Discontinued April 2025** |
| Go | `assemblyai-go-sdk` | **Discontinued April 2025** |
| C# .NET | `AssemblyAI` NuGet | **Discontinued April 2025** |

**Only Python, JS/TS, and Ruby SDKs are maintained.** For Java, Go, or C#, use the REST API directly.

## Speech-to-Text Models

### Pre-Recorded

| Model | Languages | Best For |
|-------|-----------|----------|
| **Universal-3 Pro** | 6 (en, es, de, fr, pt, it) | Highest accuracy, promptable transcription |
| **Universal-2** | 99 | Broadest language coverage |

Use `speech_models` as a priority list with fallback: `["universal-3-pro", "universal-2"]`.

### Streaming

| Model | Languages | Best For |
|-------|-----------|----------|
| **universal-streaming-english** | 6 | Voice agents, ~300ms latency |
| **universal-streaming-multilingual** | 6 | Per-utterance language detection |
| **whisper-rt** | 99+ | Broadest streaming language support, auto-detect only |
| **u3-rt-pro** | 6 | Voice agents — punctuation-based turn detection, promptable |

### Prompting (Universal-3 Pro only)

Two mutually exclusive customization parameters:
- **`prompt`** (string, up to 1500 words): Natural language instructions for transcription style
- **`keyterms_prompt`** (string[], up to 1000 terms): Domain vocabulary for proper nouns, brands, technical terms

**Prompting best practices:**
- Use positive, authoritative instructions — NEVER use negative phrasing ("Don't", "Avoid", "Never") as the model gets confused
- Limit to 3-6 instructions for best results
- Prefix critical instructions with "Non-negotiable:" or "Required:"

## LeMUR is Deprecated

**LeMUR is deprecated (sunset March 31, 2026).** Use the LLM Gateway instead. The LLM Gateway is an OpenAI-compatible API. Key difference: you pass transcript text directly in messages (no `transcript_ids`). Transcribe first, then include `transcript.text` in your prompt.

See `references/llm-gateway.md` for models, tool calling, structured outputs, and examples.

## Key Gotchas

| Gotcha | Details |
|--------|---------|
| `prompt` + `keyterms_prompt` | **Mutually exclusive** — use one or the other |
| `summarization` / `auto_chapters` | **Deprecated.** Use LLM Gateway instead (transcribe → send text to LLM) |
| PII redaction scope | Only redacts words in `text` — other feature outputs (entities, summaries) may still expose sensitive data |
| Upload key scoping | Files uploaded with one API key project cannot be transcribed with a different project's key |
| Structured outputs | NOT supported by Claude models through LLM Gateway — only OpenAI and Gemini |
| U3 Pro turn detection | Uses punctuation (`.` `?` `!`), NOT confidence thresholds — `end_of_turn_confidence_threshold` has no effect |
| Negative prompts | Never use "Don't" or "Avoid" in prompts — rephrase as positive instructions |
| PII audio redaction method | `override_audio_redaction_method: "silence"` replaces PII with silence instead of default beep |
| Language detection | Requires minimum 15 seconds of spoken audio for reliable results |
| LLM Gateway EU region | Only Anthropic Claude and Google Gemini models available — OpenAI models are NOT supported in EU |
| Disfluencies | `disfluencies: true` works on Universal-2 only; for U3 Pro, use prompting instead |

## Common Mistakes

| Mistake | Correction |
|---------|------------|
| `Authorization: Bearer KEY` | `Authorization: KEY` (no Bearer prefix) |
| Using LeMUR API | **Deprecated.** Use LLM Gateway instead |
| Using `summarization` or `auto_chapters` | **Deprecated.** Use LLM Gateway instead (transcribe then summarize via LLM) |
| LeMUR `transcript_ids` with LLM Gateway | Pass transcript text in messages, not IDs |
| `anthropic/claude-...` model IDs | No provider prefix: `claude-sonnet-4-5-20250929` not `anthropic/claude-sonnet-4-5-20250929` |
| Using Java/Go/C# SDKs | **Discontinued.** Use Python, JS/TS, Ruby, or raw API |
| `word_boost` parameter | Use `keyterms_prompt` instead |
| Hardcoding v2 streaming URL | v3 (`/v3/ws`) is current; v2 still works but is legacy |
| Not using `speech_models` | Specify model priority list: `["universal-3-pro", "universal-2"]` |

## Reference Files

Read the relevant reference file based on what the user needs:

| File | When to read |
|------|-------------|
| `references/python-sdk.md` | Python SDK patterns and examples |
| `references/js-sdk.md` | JavaScript/TypeScript SDK patterns |
| `references/streaming.md` | Real-time/streaming STT, v3 protocol, temp tokens, error codes |
| `references/voice-agents.md` | Voice agent integrations: LiveKit, Pipecat, turn detection, latency optimization |
| `references/llm-gateway.md` | Applying LLMs to transcripts, tool calling, available models |
| `references/speech-understanding.md` | Translation, speaker identification, custom formatting |
| `references/audio-intelligence.md` | PII redaction, diarization, summarization, sentiment, chapters |
| `references/api-reference.md` | Full parameter list, export endpoints, webhooks, upload, PII policies |

## API Spec Source of Truth

https://github.com/AssemblyAI/assemblyai-api-spec
