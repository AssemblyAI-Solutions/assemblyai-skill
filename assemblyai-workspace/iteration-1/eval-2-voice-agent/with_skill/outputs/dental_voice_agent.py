"""
Dental Office Voice Agent — LiveKit + AssemblyAI STT Pipeline

Handles patient calls for scheduling appointments. Uses AssemblyAI's u3-rt-pro
streaming model with keyterms boosting for dental vocabulary and dynamic
configuration to adjust silence thresholds when collecting patient details.

Requirements:
    pip install "livekit-agents[assemblyai,silero,codecs]~=1.0" \
                "livekit-plugins-turn-detector~=1.0" python-dotenv

Environment variables:
    ASSEMBLYAI_API_KEY
    LIVEKIT_URL
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET
    (Plus your LLM and TTS provider keys, e.g. OPENAI_API_KEY)
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import assemblyai, silero

load_dotenv()

# Dental-specific terms that callers are likely to say.
# keyterms_prompt improves recognition of proper nouns, procedure names,
# and other domain vocabulary that the base model may mis-transcribe.
DENTAL_KEYTERMS = [
    # Common procedures
    "cleaning", "prophylaxis", "scaling", "root planing",
    "crown", "veneer", "bridge", "implant", "extraction",
    "root canal", "filling", "composite", "amalgam",
    "whitening", "Invisalign", "braces", "orthodontics",
    "denture", "partial denture", "periodontal",
    "wisdom tooth", "wisdom teeth", "molar", "bicuspid",
    "night guard", "retainer", "bonding", "sealant",
    # Insurance and scheduling terms
    "copay", "deductible", "PPO", "HMO", "Delta Dental",
    "Cigna", "MetLife", "Aetna", "Guardian",
    # Common name fragments that are easily misheard
    "Dr. Patel", "Dr. Nguyen", "Dr. Garcia", "Dr. Kim",
    "hygienist",
]


class DentalAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly receptionist for a dental office. "
                "Help patients schedule appointments. Collect the patient's "
                "full name, the type of procedure or reason for the visit, "
                "and their preferred date and time. Confirm each detail back "
                "to the caller before finalizing."
            ),
        )


def build_stt() -> assemblyai.STT:
    """
    Configure AssemblyAI STT for the dental scheduling use case.

    Key choices:
    - u3-rt-pro: recommended model for voice agents, punctuation-based
      turn detection, and supports keyterms boosting + prompting.
    - Balanced silence profile (100ms / 1000ms): good default for
      conversational appointment scheduling.
    - vad_threshold=0.3: matches the Silero VAD threshold to avoid a
      dead zone that would delay barge-in / interruption detection.
    - keyterms_prompt: boosts dental vocabulary so procedure names,
      insurance providers, and doctor names are transcribed accurately.
    """
    return assemblyai.STT(
        model="u3-rt-pro",
        min_turn_silence=100,
        max_turn_silence=1000,
        vad_threshold=0.3,
        keyterms_prompt=DENTAL_KEYTERMS,
    )


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=build_stt(),
        vad=silero.VAD.load(activation_threshold=0.3),
        # Let AssemblyAI's punctuation-based turn detection drive
        # endpointing — it is more accurate than pure silence for
        # natural conversation.
        turn_detection="stt",
        # CRITICAL: set to 0 so LiveKit does not add its default 500ms
        # on top of AssemblyAI's own endpointing latency.
        min_endpointing_delay=0,
        # --- Add your LLM and TTS plugins here, e.g.: ---
        # llm=openai.LLM(model="gpt-4o-mini"),
        # tts=openai.TTS(model="gpt-4o-mini-tts"),
    )

    await session.start(room=ctx.room, agent=DentalAssistant())

    # Kick off the conversation with a greeting.
    await session.generate_reply(
        instructions=(
            "Greet the caller warmly. Let them know this is the dental "
            "office and ask how you can help them today."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
