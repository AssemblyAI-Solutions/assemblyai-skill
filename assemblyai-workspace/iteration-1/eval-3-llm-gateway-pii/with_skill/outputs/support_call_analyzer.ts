import { AssemblyAI, PiiPolicy } from "assemblyai";

// Use the same API key for both transcription and the LLM Gateway
const client = new AssemblyAI({ apiKey: process.env.ASSEMBLYAI_API_KEY! });

const LLM_GATEWAY_URL =
  "https://llm-gateway.assemblyai.com/v1/chat/completions";

interface CallAnalysis {
  actionItems: string;
  sentiment: string;
}

async function analyzeWithLLMGateway(
  prompt: string,
  systemPrompt: string
): Promise<string> {
  const response = await fetch(LLM_GATEWAY_URL, {
    method: "POST",
    headers: {
      // Auth uses raw API key — no "Bearer" prefix
      Authorization: process.env.ASSEMBLYAI_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      // No provider prefix on model IDs
      model: "claude-sonnet-4-5-20250929",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: prompt },
      ],
    }),
  });

  const result = await response.json();
  return result.choices[0].message.content;
}

async function transcribeAndRedact(audioUrl: string) {
  const transcript = await client.transcripts.transcribe({
    audio: audioUrl,
    // Enable speaker diarization so we know who said what
    speaker_labels: true,
    // Enable PII redaction for names, phone numbers, and SSNs
    redact_pii: true,
    redact_pii_policies: [
      PiiPolicy.PersonName,
      PiiPolicy.PhoneNumber,
      PiiPolicy.UsSocialSecurityNumber,
    ],
    // Replace PII with the entity type label (e.g., "[PERSON_NAME]")
    redact_pii_sub: "entity_name",
  });

  if (transcript.status === "error") {
    throw new Error(`Transcription failed: ${transcript.error}`);
  }

  return transcript;
}

async function extractActionItems(
  redactedTranscript: string
): Promise<string> {
  // Claude does not support structured outputs via json_schema on the LLM Gateway,
  // so we instruct it to return JSON in the system prompt instead.
  const systemPrompt = `You are an expert customer support analyst. Extract action items from the transcript.
Return your response as a JSON array where each item has:
- "owner": who is responsible (agent or customer)
- "action": what needs to be done
- "priority": "high", "medium", or "low"
- "deadline": any mentioned deadline, or "not specified"`;

  const userPrompt = `Extract all action items from this customer support call transcript:\n\n<transcript>\n${redactedTranscript}\n</transcript>`;

  return analyzeWithLLMGateway(userPrompt, systemPrompt);
}

async function analyzeSentiment(redactedTranscript: string): Promise<string> {
  const systemPrompt = `You are an expert customer support analyst. Analyze the sentiment and emotional progression of a support call.
Provide:
1. Overall sentiment (positive, negative, neutral, mixed)
2. Customer sentiment at the start vs. end of the call
3. Key moments where sentiment shifted
4. Customer satisfaction likelihood (1-10)
Return your analysis as JSON.`;

  const userPrompt = `Analyze the sentiment of this customer support call:\n\n<transcript>\n${redactedTranscript}\n</transcript>`;

  return analyzeWithLLMGateway(userPrompt, systemPrompt);
}

async function analyzeSupportCall(audioUrl: string): Promise<CallAnalysis> {
  console.log("Step 1: Transcribing audio with PII redaction...");
  const transcript = await transcribeAndRedact(audioUrl);

  // Format speaker-labeled utterances for richer LLM analysis
  const formattedTranscript = transcript
    .utterances!.map((u) => `Speaker ${u.speaker}: ${u.text}`)
    .join("\n");

  console.log("Redacted transcript:\n");
  console.log(formattedTranscript);
  console.log("\n---\n");

  // Note: PII redaction only affects the `text` property.
  // The redacted text is safe to send to the LLM Gateway.

  console.log("Step 2: Extracting action items via LLM Gateway (Claude)...");
  const actionItems = await extractActionItems(formattedTranscript);

  console.log("Step 3: Analyzing sentiment via LLM Gateway (Claude)...");
  const sentiment = await analyzeSentiment(formattedTranscript);

  return { actionItems, sentiment };
}

// --- Main ---

async function main() {
  const audioUrl = "https://example.com/support-call.mp3";

  try {
    const analysis = await analyzeSupportCall(audioUrl);

    console.log("=== Action Items ===");
    console.log(analysis.actionItems);
    console.log("\n=== Sentiment Analysis ===");
    console.log(analysis.sentiment);
  } catch (err) {
    console.error("Analysis failed:", err);
  }
}

main();
