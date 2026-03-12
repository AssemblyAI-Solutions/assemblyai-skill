# Speech Understanding

## Overview

Speech Understanding provides post-transcription intelligence features including translation, speaker identification, and custom formatting.

- Available via the `speech_understanding` object in a transcript request (inline) OR via a separate endpoint (post-hoc on existing transcripts).
- Endpoint: `POST https://llm-gateway.assemblyai.com/v1/understanding`
  - EU: `https://llm-gateway.eu.assemblyai.com/v1/understanding`
- Auth header: `Authorization: API_KEY` (no `Bearer` prefix)
- Can be used inline during transcription or post-hoc on existing transcripts.

## Translation

Translates transcript text into one or more target languages. Supports 100+ languages.

### Parameters

- `target_languages` (array of strings): Language codes to translate into (e.g., `["es", "fr", "de"]`).
- `formal` (boolean): When `true`, uses formal tone in translation.
- `match_original_utterance` (boolean): When `true`, maintains speaker mapping so each translated utterance corresponds to the original speaker's utterance.

### Example Request

```json
{
  "transcript_id": "abc123",
  "speech_understanding": {
    "translation": {
      "target_languages": ["es", "fr"],
      "formal": true,
      "match_original_utterance": true
    }
  }
}
```

### Example Response

```json
{
  "translation": {
    "es": [
      {
        "speaker": "A",
        "original": "Hello, how are you?",
        "translation": "Hola, ¿cómo está usted?"
      }
    ],
    "fr": [
      {
        "speaker": "A",
        "original": "Hello, how are you?",
        "translation": "Bonjour, comment allez-vous ?"
      }
    ]
  }
}
```

## Speaker Identification

Distinct from diarization. Maps generic speaker labels (Speaker A, Speaker B) to actual names or roles. Requires diarization (`speaker_labels: true`) to be enabled first.

### Parameters

- `speaker_type` (string): `"role"` or `"name"`.
- `known_values` (array of strings): Simple list of known speaker names or roles. Max 35 characters each.
- `speakers` (array of objects): More detailed speaker descriptions. Each object can include:
  - `name` (string)
  - `description` (string)
  - `company` (string)
  - `title` (string)

Use either `known_values` or `speakers`, not both.

### Example with known_values

```json
{
  "transcript_id": "abc123",
  "speech_understanding": {
    "speaker_identification": {
      "speaker_type": "name",
      "known_values": ["Alice", "Bob", "Charlie"]
    }
  }
}
```

### Example with speakers

```json
{
  "transcript_id": "abc123",
  "speech_understanding": {
    "speaker_identification": {
      "speaker_type": "role",
      "speakers": [
        {
          "name": "Dr. Smith",
          "description": "The interviewer asking questions",
          "company": "Acme Corp",
          "title": "Head of Recruiting"
        },
        {
          "name": "Jane Doe",
          "description": "The candidate being interviewed",
          "company": "Previous Inc",
          "title": "Software Engineer"
        }
      ]
    }
  }
}
```

## Custom Formatting

Automatically formats dates, phone numbers, and emails in the transcript text.

### Parameters

All booleans:

- `date`: Format dates in transcript text.
- `phone_number`: Format phone numbers in transcript text.
- `email`: Format email addresses in transcript text.
- `format_utterances`: Apply formatting to utterance-level text as well.

### Example

```json
{
  "transcript_id": "abc123",
  "speech_understanding": {
    "custom_formatting": {
      "date": true,
      "phone_number": true,
      "email": true,
      "format_utterances": true
    }
  }
}
```

## Using via Transcript Request

Include the `speech_understanding` object directly in the `POST /v2/transcript` body to run Speech Understanding features inline during transcription.

### Example

```json
POST https://api.assemblyai.com/v2/transcript
Authorization: API_KEY

{
  "audio_url": "https://example.com/audio.mp3",
  "speaker_labels": true,
  "speech_understanding": {
    "translation": {
      "target_languages": ["es"],
      "formal": false,
      "match_original_utterance": true
    },
    "speaker_identification": {
      "speaker_type": "name",
      "known_values": ["Alice", "Bob"]
    },
    "custom_formatting": {
      "date": true,
      "phone_number": true,
      "email": true,
      "format_utterances": true
    }
  }
}
```

The Speech Understanding results will be included in the transcript response once it completes.

## Using via Understanding Endpoint

Send a `POST` request with a `transcript_id` and `speech_understanding` object to run Speech Understanding features post-hoc on an existing transcript.

### Example

```bash
curl -X POST "https://llm-gateway.assemblyai.com/v1/understanding" \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_id": "abc123",
    "speech_understanding": {
      "translation": {
        "target_languages": ["de"],
        "formal": true,
        "match_original_utterance": false
      },
      "speaker_identification": {
        "speaker_type": "role",
        "known_values": ["Doctor", "Patient"]
      }
    }
  }'
```

The response will contain the results of the requested Speech Understanding features.
