# Audio Intelligence Features

All Audio Intelligence features are enabled via boolean parameters on the `POST /v2/transcript` request.

## Speaker Diarization

- Enable with `speaker_labels: true`
- Response includes `utterances` array with `speaker`, `text`, `start`, `end`
- Each word also gets a `speaker` field

## PII Redaction

- Enable with `redact_pii: true`
- `redact_pii_policies`: array of policy strings. Common policies include:
  - `person_name`
  - `phone_number`
  - `email_address`
  - `us_social_security_number`
  - `credit_card_number`
  - `date_of_birth`
- `redact_pii_sub`: `"hash"` or `"entity_type"`
- `redact_pii_audio: true` generates audio with PII beeped out
- `redact_pii_audio_quality`: `"mp3"` or `"wav"`

**IMPORTANT:** Redacted audio files expire after 24 hours.

**IMPORTANT:** PII redaction only affects the `text` property — other feature outputs (entity detection, summarization, etc.) may still expose sensitive data in their results.

## Sentiment Analysis

- Enable with `sentiment_analysis: true`
- Response includes `sentiment_analysis_results` array
- Each result has `text`, `sentiment` (POSITIVE/NEGATIVE/NEUTRAL), `confidence`, `speaker`

## Entity Detection

- Enable with `entity_detection: true`
- Response includes `entities` array with `entity_type`, `text`, `start`, `end`

## Summarization

- Enable with `summarization: true`
- `summary_model`: `"informative"`, `"conversational"`, or `"catchy"`
- `summary_type`: `"bullets"`, `"bullets_verbose"`, `"gist"`, `"headline"`, `"paragraph"`
- If you specify one of `summary_model`/`summary_type`, you must provide both
- `conversational` model requires `speaker_labels` or `multichannel` enabled
- **Mutually exclusive with `auto_chapters`**

## Auto Chapters

- Enable with `auto_chapters: true`
- Response includes `chapters` array with `summary`, `gist`, `headline`, `start`, `end`
- **Mutually exclusive with `summarization`**

## Topic Detection (IAB Taxonomy)

- Enable with `iab_categories: true`
- Response includes `iab_categories_result` with `results` and `summary`

## Content Moderation

- Enable with `content_safety: true`
- `content_safety_confidence`: adjustable threshold (25-100, default 50)
- Detects categories including hate speech, violence, drugs, profanity, etc.
- Response includes `content_safety_labels` with results per segment

## Auto Highlights

- Enable with `auto_highlights: true`
- Extracts key phrases from the transcript
- Response includes `auto_highlights_result` with `results` array
