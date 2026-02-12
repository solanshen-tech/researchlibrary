import argparse
import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol
from urllib import request


class TranscriptSource(Protocol):
    def fetch_transcript(self, company: str) -> str:
        """Return transcript text for a company."""


class LocalFileTranscriptSource:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def fetch_transcript(self, company: str) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"Transcript file not found: {self.path}")
        return self.path.read_text(encoding="utf-8")


class TegusTranscriptSource:
    """Scaffold for Tegus integration."""

    def fetch_transcript(self, company: str) -> str:
        raise NotImplementedError(
            "Implement Tegus transcript fetching with your account/API flow."
        )


@dataclass
class Highlight:
    text: str


class HighlightExtractor:
    def __init__(self, max_highlights: int = 8) -> None:
        self.max_highlights = max_highlights

    def extract(self, transcript: str) -> List[Highlight]:
        lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
        selected: List[Highlight] = []
        for line in lines:
            if len(selected) >= self.max_highlights:
                break
            if any(
                token in line.lower()
                for token in ["growth", "risk", "margin", "guidance", "demand", "strategy"]
            ):
                selected.append(Highlight(text=line))

        if not selected:
            selected = [Highlight(text=line) for line in lines[: self.max_highlights]]

        return selected


class NoteFormatter:
    def format_markdown(self, company: str, highlights: List[Highlight], transcript: str) -> str:
        today = dt.datetime.utcnow().strftime("%Y-%m-%d")
        bullets = "\n".join([f"- {h.text}" for h in highlights]) if highlights else "- (No highlights found)"
        excerpt = transcript[:1200]
        return (
            f"# {company} Tegus Transcript Note ({today})\n\n"
            "## Highlights\n"
            f"{bullets}\n\n"
            "## Transcript Excerpt\n"
            f"{excerpt}\n"
        )


class GoogleDriveSink:
    def __init__(self, enabled: bool, folder_id: str = "") -> None:
        self.enabled = enabled
        self.folder_id = folder_id

    def upload_markdown(self, filename: str, content: str) -> None:
        if not self.enabled:
            return
        raise NotImplementedError(
            "Implement Google Drive upload using Google Drive API and OAuth credentials."
        )


class KnowledgeBaseSink:
    def __init__(self, enabled: bool, endpoint: str = "", api_key_env: str = "") -> None:
        self.enabled = enabled
        self.endpoint = endpoint
        self.api_key_env = api_key_env

    def push(self, company: str, highlights: List[Highlight]) -> None:
        if not self.enabled:
            return

        api_key = os.environ.get(self.api_key_env, "")
        payload = {
            "company": company,
            "highlights": [h.text for h in highlights],
            "source": "tegus",
            "timestamp_utc": dt.datetime.utcnow().isoformat(),
        }
        body = json.dumps(payload).encode("utf-8")

        req = request.Request(self.endpoint, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")

        with request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"KB push failed with status={resp.status}")


@dataclass
class AppConfig:
    google_drive_enabled: bool
    google_drive_folder_id: str
    kb_enabled: bool
    kb_endpoint: str
    kb_api_key_env: str


def load_config(path: str) -> AppConfig:
    if not Path(path).exists():
        return AppConfig(False, "", False, "", "")

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    gd = data.get("google_drive", {})
    kb = data.get("knowledge_base", {})

    return AppConfig(
        google_drive_enabled=bool(gd.get("enabled", False)),
        google_drive_folder_id=str(gd.get("folder_id", "")),
        kb_enabled=bool(kb.get("enabled", False)),
        kb_endpoint=str(kb.get("endpoint", "")),
        kb_api_key_env=str(kb.get("api_key_env", "")),
    )


def run(company: str, transcript_source: TranscriptSource, config: AppConfig) -> Path:
    transcript = transcript_source.fetch_transcript(company)
    highlights = HighlightExtractor().extract(transcript)
    note = NoteFormatter().format_markdown(company, highlights, transcript)

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{company.lower().replace(' ', '_')}_note.md"
    out_path = out_dir / filename
    out_path.write_text(note, encoding="utf-8")

    drive = GoogleDriveSink(config.google_drive_enabled, config.google_drive_folder_id)
    drive.upload_markdown(filename, note)

    kb = KnowledgeBaseSink(config.kb_enabled, config.kb_endpoint, config.kb_api_key_env)
    kb.push(company, highlights)

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build company research notes from transcript text")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to local transcript text file (or replace source with Tegus connector)",
    )
    parser.add_argument("--config", default="config.json", help="Path to JSON config")
    args = parser.parse_args()

    config = load_config(args.config)
    source = LocalFileTranscriptSource(args.input)
    out_path = run(args.company, source, config)
    print(f"Note created: {out_path}")


if __name__ == "__main__":
    main()
