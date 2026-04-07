# Voice Agent Integrations

AssemblyAI supports four paths for building voice agents:

1. **Speech-to-Speech API** — single WebSocket for full voice agent (speech-in → LLM → speech-out)
2. **LiveKit Agents** — fastest path to deployment using U3 Pro STT
3. **Pipecat (by Daily)** — open-source, maximum customizability using U3 Pro STT
4. **Direct WebSocket** — fully custom STT builds (see `streaming.md`)

## Speech-to-Speech API

AssemblyAI's Speech-to-Speech API is a single WebSocket that handles the full voice agent loop: speech-in → LLM → speech-out. It includes built-in VAD, TTS, tool calling, and barge-in handling.

**Note:** Requires a credit card on file to activate.

### Connection

```
wss://speech-to-speech.us.assemblyai.com/v1/realtime
Authorization: Bearer YOUR_API_KEY
```

Audio format: PCM16, 24kHz mono, base64-encoded, ~50ms chunks (2400 bytes).

### Client Events

| Event | Description |
|-------|-------------|
| `input.audio` | Send audio chunk: `{"type": "input.audio", "audio": "<base64>"}` |
| `session.update` | Configure session: `system_prompt`, `greeting`, `tools`, `turn_detection` |
| `session.resume` | Reconnect to an existing session: `{"type": "session.resume", "session_id": "..."}` |
| `tool.result` | Return tool call result back to the agent |

### Server Events

| Event | Description |
|-------|-------------|
| `session.ready` | Session is initialized and ready |
| `session.updated` | Session configuration has been updated |
| `input.speech.started` | VAD detected speech start (for barge-in) |
| `input.speech.stopped` | VAD detected speech end |
| `transcript.user.delta` | Partial user transcript |
| `transcript.user` | Final user transcript |
| `reply.started` | Agent is starting a reply |
| `reply.audio` | Agent audio chunk (base64 PCM16 24kHz) |
| `transcript.agent` | Agent's reply text |
| `reply.done` | Agent reply complete |
| `tool.call` | Agent wants to call a tool |
| `error` | Non-fatal error |
| `session.error` | Fatal session error |

### Session Resume

Sessions are preserved for **30 seconds** after disconnection. Reconnect using `session.resume` with the session ID to continue without losing context.

### Example session.update

```json
{
  "type": "session.update",
  "system_prompt": "You are a helpful customer support agent for Acme Corp.",
  "greeting": "Hello! How can I help you today?",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "lookup_order",
        "description": "Look up an order by order ID",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {"type": "string"}
          },
          "required": ["order_id"]
        }
      }
    }
  ]
}
```

---

## Recommended Model (STT-based paths)

**`u3-rt-pro`** (Universal-3 Pro Streaming) is the recommended model for all new voice agent work.

| Feature | u3-rt-pro | universal-streaming-english | universal-streaming-multilingual |
|---------|-----------|------------------------------|----------------------------------|
| Turn detection | Punctuation-based | Confidence-based | Confidence-based |
| Custom prompting (beta) | Yes | No | No |
| Keyterms boosting | Yes | Yes | Yes |
| Speaker diarization | Yes | Yes | Yes |
| Dynamic mid-session updates | Yes | Yes | Yes |
| Multilingual code switching | Yes | No | Yes |
| Languages | 6 (en, es, fr, de, it, pt) | English only | Multiple |

`end_of_turn_confidence_threshold` does NOT work with u3-rt-pro — it only applies to older universal-streaming models.

## Turn Detection (u3-rt-pro)

1. User pauses for `min_turn_silence` (e.g., 100ms)
2. Model checks for terminal punctuation (`.` `?` `!`)
3. If found: turn ends immediately (`end_of_turn: true`)
4. If not found: partial emitted, listening continues
5. If silence reaches `max_turn_silence`: turn forced to end regardless

## Silence Settings by Use Case

| Profile | min_turn_silence | max_turn_silence | Use Case |
|---------|-----------------|-----------------|----------|
| **Fast** | 100ms | 800ms | IVR, yes/no, quick confirmations |
| **Balanced** | 100ms | 1000ms | Most voice agents (recommended default) |
| **Patient** | 200ms | 2000ms | Entity dictation: emails, phone numbers, addresses |

Low `min_turn_silence` can split entities (phone numbers, emails) across turns. Dynamically increase `max_turn_silence` to 2000-3000ms during entity collection phases, then reduce it afterward.

---

## LiveKit Integration

### Setup

```bash
# For u3-rt-pro (requires livekit-agents >= 1.4.4)
pip install "livekit-agents[assemblyai,silero,codecs]~=1.0" python-dotenv livekit-plugins-turn-detector~=1.0
```

Required env vars: `ASSEMBLYAI_API_KEY`, `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, plus LLM/TTS provider keys.

### Turn Detection Modes

#### STT-based (recommended for u3-rt-pro)

```python
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import assemblyai, silero

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    session = AgentSession(
        stt=assemblyai.STT(
            model="u3-rt-pro",
            min_turn_silence=100,
            max_turn_silence=1000,
            vad_threshold=0.3,
        ),
        vad=silero.VAD.load(activation_threshold=0.3),
        turn_detection="stt",
        min_endpointing_delay=0,  # CRITICAL: avoid additive 500ms delay
    )
    await session.start(room=ctx.room, agent=Assistant())
    await session.generate_reply(instructions="Greet the user and offer your assistance.")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
```

Run with `python voice_agent.py dev`, test at `https://agents-playground.livekit.io/`.

#### MultilingualModel (LiveKit's own turn detection)

```python
from livekit.plugins.turn_detector.multilingual import MultilingualModel

session = AgentSession(
    turn_detection=MultilingualModel(),
    stt=assemblyai.STT(model="u3-rt-pro", vad_threshold=0.3),
    vad=silero.VAD.load(activation_threshold=0.3),
    min_endpointing_delay=0.5,
    max_endpointing_delay=3.0,
)
```

Other modes: **VAD-only** (purely silence-based) and **Manual** (explicit `session.commit_user_turn()`, `session.clear_user_turn()`, `session.interrupt()`).

### LiveKit Pitfalls

| Pitfall | Fix |
|---------|-----|
| `max_turn_silence` defaults to **100ms** in LiveKit (API default is 1000ms) | Always set `max_turn_silence=1000` explicitly |
| `min_endpointing_delay` adds **500ms** on top of AssemblyAI endpointing | Set `min_endpointing_delay=0` in STT mode |
| Silero VAD default threshold is 0.5, AssemblyAI default is 0.3 | Set both to 0.3 — mismatch creates a dead zone delaying interruption |
| u3-rt-pro requires livekit-agents >= 1.4.4 | Check version before debugging |

---

## Pipecat Integration

### Setup

```bash
pip install "pipecat-ai[assemblyai,openai,cartesia]"
# or swap providers:
pip install "pipecat-ai[assemblyai,anthropic,elevenlabs]"
```

### Turn Detection Modes

#### Pipecat-controlled (default, recommended)

```python
from pipecat.services.assemblyai.stt import AssemblyAISTTService
from pipecat.services.assemblyai.config import AssemblyAIConnectionParams

stt = AssemblyAISTTService(
    api_key=os.getenv("ASSEMBLYAI_API_KEY"),
    connection_params=AssemblyAIConnectionParams(
        speech_model="u3-rt-pro",
        min_turn_silence=100,
    ),
    vad_force_turn_endpoint=True,  # Default — Pipecat controls turns
)
```

In Pipecat mode, VAD + Smart Turn analyzer controls endpointing. `max_turn_silence` auto-syncs with `min_turn_silence`. A `ForceEndpoint` message is sent to AssemblyAI when silence is detected.

#### AssemblyAI's built-in turn detection

```python
stt = AssemblyAISTTService(
    api_key=os.getenv("ASSEMBLYAI_API_KEY"),
    connection_params=AssemblyAIConnectionParams(
        speech_model="u3-rt-pro",
        min_turn_silence=100,
        max_turn_silence=1000,
    ),
    vad_force_turn_endpoint=False,  # AssemblyAI controls turns
)
```

### Keyterms Boosting

```python
stt = AssemblyAISTTService(
    api_key=os.getenv("ASSEMBLYAI_API_KEY"),
    connection_params=AssemblyAIConnectionParams(
        speech_model="u3-rt-pro",
        min_turn_silence=100,
        keyterms_prompt=["Xiomara", "Saoirse", "Pipecat", "AssemblyAI"],
    ),
)
```

### Dynamic Mid-Session Updates

```python
from pipecat.frames.frames import STTUpdateSettingsFrame
from pipecat.services.assemblyai.stt import AssemblyAISTTSettings

await task.queue_frame(
    STTUpdateSettingsFrame(
        delta=AssemblyAISTTSettings(
            connection_params=AssemblyAIConnectionParams(
                keyterms_prompt=["NewName", "NewCompany"],
                min_turn_silence=200,
                max_turn_silence=3000,
            )
        )
    )
)
```

### Speaker Diarization

```python
stt = AssemblyAISTTService(
    api_key=os.getenv("ASSEMBLYAI_API_KEY"),
    connection_params=AssemblyAIConnectionParams(
        speech_model="u3-rt-pro",
        speaker_labels=True,
    ),
    speaker_format="<Speaker {speaker}>{text}</Speaker {speaker}>",
)
```

### Pipecat Pitfall

`keyterms_prompt` and `prompt` cannot be used simultaneously — choose one.

---

## Barge-In / Interruption Handling

Monitor `SpeechStarted` events from AssemblyAI:
```json
{"type": "SpeechStarted", "timestamp": 14400, "confidence": 0.79}
```

On detection: stop TTS playback immediately, switch to listening mode, wait for full turn before responding.

---

## Dynamic Configuration by Conversation Stage

Both frameworks support updating parameters mid-session without reconnecting:

| Stage | Configuration |
|-------|--------------|
| Caller identification | Boost specific names via `keyterms_prompt` |
| Entity dictation (email, phone) | Increase `max_turn_silence` to 3000ms |
| Yes/no questions | Use prompt anticipating short responses |
| Payment collection | Boost card brand terms + extend silence |

---

## Latency Optimization

1. **Set `min_endpointing_delay=0`** in LiveKit STT mode — default 500ms is additive
2. **Use 16kHz sample rate** — higher rates don't improve accuracy
3. **Synchronize VAD thresholds** — set both local VAD and AssemblyAI `vad_threshold` to 0.3
4. **Avoid audio preprocessing/noise cancellation** before sending to AssemblyAI — artifacts cause more harm than background noise
5. **Only enable features you need** — skip `speaker_labels` unless required
6. **Use dynamic configuration** to adjust silence only when needed

### Latency Breakdown

| Component | Latency |
|-----------|---------|
| Network transmission | ~50ms |
| Speech-to-text processing | 200-300ms (sub-300ms P50) |
| `min_turn_silence` check | 100ms+ (configurable) |
| `max_turn_silence` fallback | 1000ms+ (only if no terminal punctuation) |

---

## Telnyx Telephony Integration

### Via LiveKit
SIP trunking routes phone calls into LiveKit rooms. Configure inbound/outbound trunks and dispatch rules.

### Via Pipecat
WebSocket media streaming with TeXML. **Critical: Telnyx uses 8kHz audio**, not 16kHz:

```python
transport = TelnyxTransport(
    # ...
    audio_in_sample_rate=8000,
    audio_out_sample_rate=8000,
)
```

---

## Scaling

- Free tier: 5 new streams/minute
- Pay-as-you-go: 100 new streams/minute
- No hard cap on concurrent streams
- Automatic 10% capacity increase every 60 seconds at 70%+ utilization

---

## Accuracy Enhancement Priority

1. **Keyterms prompting** (highest impact) — up to 100 terms, max 50 chars each
2. **Dynamic configuration updates** — contextual adaptation per conversation stage
3. **Silence threshold tuning** — entity preservation
4. **Avoid preprocessing noise cancellation** — artifacts hurt more than noise
