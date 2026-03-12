"""
Dental Office Voice Agent — LiveKit + AssemblyAI STT Pipeline

This agent handles inbound patient calls for scheduling dental appointments.
It uses AssemblyAI's real-time streaming transcription via the LiveKit Agents
framework to accurately capture patient names, procedure types, and dates.
"""

import logging
from datetime import datetime

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.stt import StreamAdapter
from livekit.plugins import assemblyai as aai_plugin
from livekit.plugins import openai as openai_plugin
from livekit.plugins import silero

logger = logging.getLogger("dental-voice-agent")
logger.setLevel(logging.INFO)


def prewarm(proc: JobProcess):
    """Preload the Silero VAD model so it's ready when a call connects."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entrypoint: sets up the STT pipeline and voice agent for each call."""

    # ------------------------------------------------------------------
    # 1. AssemblyAI STT configuration
    # ------------------------------------------------------------------
    # AssemblyAI's real-time transcriber handles streaming audio and
    # returns high-accuracy transcripts.  We supply a custom word list
    # so that dental-specific terms and common procedure names are
    # recognised reliably.
    stt = aai_plugin.STT(
        word_boost=[
            # Procedure types patients commonly mention
            "cleaning",
            "crown",
            "root canal",
            "filling",
            "extraction",
            "veneer",
            "implant",
            "whitening",
            "bridge",
            "denture",
            "orthodontics",
            "braces",
            "Invisalign",
            "periodontal",
            "scaling",
            "x-ray",
            "panoramic",
            # Common dental-office vocabulary
            "hygienist",
            "dentist",
            "orthodontist",
            "copay",
            "insurance",
            "PPO",
            "HMO",
            "deductible",
        ],
        # Increase the boost weight so these terms are strongly preferred
        # when the acoustic signal is ambiguous.
        boost_param="high",
        # Encoding expected from LiveKit audio frames
        encoding=aai_plugin.AudioEncoding.PCM_S16LE,
        sample_rate=16000,
    )

    # ------------------------------------------------------------------
    # 2. LLM (conversation brain)
    # ------------------------------------------------------------------
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a friendly, professional receptionist at Bright Smile "
            "Dental Office. Your job is to help patients schedule, reschedule, "
            "or cancel dental appointments over the phone.\n\n"
            "During every call you must collect:\n"
            "  1. The patient's full name (first and last). Always confirm "
            "     the spelling.\n"
            "  2. The type of procedure or visit (e.g. cleaning, crown, "
            "     root canal, consultation).\n"
            "  3. The preferred date and time for the appointment.\n\n"
            "After collecting all three pieces of information, read them back "
            "to the patient for confirmation before finalising.\n\n"
            "Be concise and warm. If the patient is unclear, ask clarifying "
            "questions. Today's date is "
            f"{datetime.now().strftime('%A, %B %d, %Y')}."
        ),
    )

    chat_llm = openai_plugin.LLM(
        model="gpt-4o",
        temperature=0.4,
    )

    # ------------------------------------------------------------------
    # 3. TTS (voice output back to the patient)
    # ------------------------------------------------------------------
    tts = openai_plugin.TTS(
        model="tts-1",
        voice="nova",
    )

    # ------------------------------------------------------------------
    # 4. Assemble the voice pipeline
    # ------------------------------------------------------------------
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=stt,
        llm=chat_llm,
        tts=tts,
        chat_ctx=initial_ctx,
        # Allow a slightly longer pause before the agent considers the
        # caller's turn "finished" — patients often pause when recalling
        # dates or procedure names.
        min_endpointing_delay=0.8,
    )

    # ------------------------------------------------------------------
    # 5. Lifecycle hooks for logging / downstream integrations
    # ------------------------------------------------------------------
    @agent.on("user_speech_committed")
    def on_user_speech(msg: llm.ChatMessage):
        """Log every finalised user utterance for QA / audit purposes."""
        logger.info(f"Patient said: {msg.content}")

    @agent.on("agent_speech_committed")
    def on_agent_speech(msg: llm.ChatMessage):
        logger.info(f"Agent said: {msg.content}")

    # ------------------------------------------------------------------
    # 6. Connect and start the agent
    # ------------------------------------------------------------------
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant (the patient calling in)
    participant = await ctx.wait_for_participant()
    logger.info(f"Patient connected: {participant.identity}")

    # Start the pipeline — the agent will greet the patient automatically.
    agent.start(ctx.room, participant)
    await agent.say(
        "Thank you for calling Bright Smile Dental Office! "
        "My name is Nova. How can I help you today?",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
