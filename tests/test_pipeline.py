import tempfile
import unittest
from pathlib import Path

from src.pipeline import HighlightExtractor, LocalFileTranscriptSource, NoteFormatter


class TestPipeline(unittest.TestCase):
    def test_local_source_reads_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("hello", encoding="utf-8")
            source = LocalFileTranscriptSource(str(path))
            self.assertEqual(source.fetch_transcript("Any"), "hello")

    def test_highlights_keyword_first(self):
        transcript = """General intro
Demand is improving in core markets.
We see margin expansion in Q4.
Other detail
"""
        highlights = HighlightExtractor(max_highlights=3).extract(transcript)
        self.assertEqual(len(highlights), 2)
        self.assertIn("Demand is improving", highlights[0].text)

    def test_markdown_output(self):
        formatter = NoteFormatter()
        note = formatter.format_markdown(
            "Acme",
            [],
            "Some transcript text",
        )
        self.assertIn("# Acme Tegus Transcript Note", note)
        self.assertIn("## Transcript Excerpt", note)


if __name__ == "__main__":
    unittest.main()
