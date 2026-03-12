import os
import assemblyai as aai

# Configure the API key from environment variable
aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]

# Path to the meeting recording
audio_file = os.path.expanduser("~/recordings/standup.mp3")

# Configure transcription with speaker labels and summarization
config = aai.TranscriptionConfig(
    speaker_labels=True,
    summarization=True,
    summary_model=aai.SummarizationModel.informative,
    summary_type=aai.SummarizationType.bullets,
)

# Create transcriber and transcribe the file
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_file, config=config)

if transcript.status == aai.TranscriptStatus.error:
    print(f"Transcription failed: {transcript.error}")
    raise SystemExit(1)

# Print full transcript with speaker labels
print("=== Transcript with Speaker Labels ===\n")
for utterance in transcript.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.text}\n")

# Print summary
print("=== Summary ===\n")
print(transcript.summary)
