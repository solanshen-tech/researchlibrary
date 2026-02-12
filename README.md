# Company Transcript Note System

This repository provides a starter implementation for a **company research note pipeline**:

1. Fetch transcript text for a target company (starting with local files; Tegus connector scaffold included).
2. Generate concise note highlights.
3. Save markdown notes to Google Drive.
4. Push highlights into a knowledge base endpoint for quick retrieval.

> The Tegus and knowledge-base connectors are intentionally scaffolded so you can plug in your account credentials and preferred API/browser automation flow.

## Architecture

- `TranscriptSource` interface: where transcript text comes from.
- `HighlightExtractor`: generates highlight bullets from transcript text.
- `NoteFormatter`: renders a markdown research note.
- `DriveSink`: writes notes to Google Drive (stub + local fallback).
- `KnowledgeBaseSink`: sends highlight payload to a KB API.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
python -m src.pipeline --company "NVIDIA" --input transcripts/nvidia.txt --config config.json
```

The command above will:
- read transcript text from `--input`
- generate highlights
- write a markdown note in `out/`
- if configured, attempt to sync to Google Drive and your knowledge base endpoint

## Configuration

Copy `config.example.json` to `config.json` and fill in:

- `google_drive.enabled`: true/false
- `google_drive.folder_id`: destination Drive folder
- `knowledge_base.endpoint`: API endpoint where highlights should be posted
- `knowledge_base.api_key_env`: environment variable containing your API key

## Tegus integration options

You can add Tegus retrieval in two practical ways:

1. **Official API (preferred if available on your plan)**
   - Implement `TegusTranscriptSource.fetch_transcript()` in `src/pipeline.py`.
2. **Browser automation fallback**
   - Use Playwright/Selenium with your authenticated Tegus session and export transcript text.
   - Save text then feed it through this pipeline.

## Recommended next steps

1. Implement the Tegus connector with your account flow.
2. Replace `GoogleDriveSink.upload_markdown()` stub with Drive API upload.
3. Replace KB sink payload format to match your KB schema.
4. Add scheduling (cron/GitHub Actions) for recurring company updates.
