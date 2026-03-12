import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"

config = aai.TranscriptionConfig(
    speaker_labels=True,
    summarization=True,
    summary_model=aai.SummarizationModel.conversational,
    summary_type=aai.SummarizationType.bullets,
)

transcriber = aai.Transcriber(config=config)
transcript = transcriber.transcribe("~/recordings/standup.mp3")

if transcript.status == aai.TranscriptStatus.error:
    print(f"Transcription failed: {transcript.error}")
    raise SystemExit(1)

print("=== Transcript with Speaker Labels ===\n")
for utterance in transcript.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.text}")

print("\n=== Summary ===\n")
print(transcript.summary)
