import AssemblyAI, {
  Transcript,
  LemurTaskResponse,
  PiiPolicy,
} from "assemblyai";

// Initialize the AssemblyAI client.
// A single API key gives access to transcription, PII redaction, and LeMUR (Claude-powered).
const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

// ---------------------------------------------------------------------------
// 1. Transcribe with PII redaction
// ---------------------------------------------------------------------------
async function transcribeWithPiiRedaction(
  audioUrl: string
): Promise<Transcript> {
  const transcript = await client.transcripts.transcribe({
    audio_url: audioUrl,
    // Enable PII redaction and specify the entity types to redact.
    redact_pii: true,
    redact_pii_policies: [
      PiiPolicy.PersonName,
      PiiPolicy.PhoneNumber,
      PiiPolicy.UsSocialSecurityNumber,
      // You can add more policies such as:
      // PiiPolicy.EmailAddress,
      // PiiPolicy.CreditCardNumber,
    ],
    // Choose how redacted text appears in the transcript.
    // "hash" replaces PII with #### characters.
    redact_pii_sub: "hash",
  });

  if (transcript.status === "error") {
    throw new Error(
      `Transcription failed: ${transcript.error}`
    );
  }

  return transcript;
}

// ---------------------------------------------------------------------------
// 2. Extract action items from the redacted transcript using LeMUR + Claude
// ---------------------------------------------------------------------------
async function extractActionItems(
  transcriptId: string
): Promise<LemurTaskResponse> {
  const response = await client.lemur.task({
    transcript_ids: [transcriptId],
    // LeMUR lets you pick the underlying model. Use Claude for best results.
    final_model: "anthropic/claude-3-5-sonnet",
    prompt: `You are analyzing a customer support call transcript.
Extract every action item that was discussed or promised during the call.
For each action item provide:
  - description: a short summary of the task
  - owner: who is responsible ("agent" or "customer")
  - priority: "high", "medium", or "low"
  - deadline: any mentioned deadline, or "none mentioned"

Return the result as a JSON array of objects with those four keys.
Only return the JSON array, no extra commentary.`,
  });

  return response;
}

// ---------------------------------------------------------------------------
// 3. Analyze sentiment from the redacted transcript using LeMUR + Claude
// ---------------------------------------------------------------------------
async function analyzeSentiment(
  transcriptId: string
): Promise<LemurTaskResponse> {
  const response = await client.lemur.task({
    transcript_ids: [transcriptId],
    final_model: "anthropic/claude-3-5-sonnet",
    prompt: `You are analyzing a customer support call transcript.
Provide a sentiment analysis with the following structure (JSON):
{
  "overall_sentiment": "positive" | "negative" | "neutral" | "mixed",
  "customer_sentiment": "positive" | "negative" | "neutral" | "mixed",
  "agent_sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_shifts": [
    {
      "from": "<sentiment>",
      "to": "<sentiment>",
      "trigger": "<brief description of what caused the shift>"
    }
  ],
  "summary": "<2-3 sentence summary of the emotional arc of the call>"
}

Return only the JSON object, no extra commentary.`,
  });

  return response;
}

// ---------------------------------------------------------------------------
// 4. Orchestrate the full pipeline
// ---------------------------------------------------------------------------
interface CallAnalysis {
  transcriptId: string;
  redactedText: string;
  actionItems: unknown;
  sentiment: unknown;
}

async function analyzeCall(audioUrl: string): Promise<CallAnalysis> {
  console.log("Starting transcription with PII redaction...");
  const transcript = await transcribeWithPiiRedaction(audioUrl);
  console.log(`Transcription complete. ID: ${transcript.id}`);
  console.log(`Redacted transcript:\n${transcript.text}\n`);

  // Run action-item extraction and sentiment analysis in parallel — both
  // operate on the same already-redacted transcript so there is no data
  // leakage of PII to the LLM.
  console.log("Extracting action items and sentiment via LeMUR (Claude)...");
  const [actionItemsResponse, sentimentResponse] = await Promise.all([
    extractActionItems(transcript.id),
    analyzeSentiment(transcript.id),
  ]);

  const actionItems = JSON.parse(actionItemsResponse.response);
  const sentiment = JSON.parse(sentimentResponse.response);

  console.log("\n--- Action Items ---");
  console.log(JSON.stringify(actionItems, null, 2));

  console.log("\n--- Sentiment Analysis ---");
  console.log(JSON.stringify(sentiment, null, 2));

  return {
    transcriptId: transcript.id,
    redactedText: transcript.text!,
    actionItems,
    sentiment,
  };
}

// ---------------------------------------------------------------------------
// 5. Process multiple calls
// ---------------------------------------------------------------------------
async function processSupportCalls(audioUrls: string[]): Promise<void> {
  const results: CallAnalysis[] = [];

  for (const [index, url] of audioUrls.entries()) {
    console.log(`\n========== Processing call ${index + 1} of ${audioUrls.length} ==========`);
    try {
      const analysis = await analyzeCall(url);
      results.push(analysis);
    } catch (err) {
      console.error(`Failed to process ${url}:`, err);
    }
  }

  console.log("\n========== All calls processed ==========");
  console.log(`Successfully analyzed ${results.length} / ${audioUrls.length} calls.`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const sampleAudioUrls = [
  "https://storage.example.com/support-calls/call-001.mp3",
  "https://storage.example.com/support-calls/call-002.mp3",
];

processSupportCalls(sampleAudioUrls).catch(console.error);
