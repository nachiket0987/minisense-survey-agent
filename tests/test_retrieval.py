from pathlib import Path
import numpy as np
import pytest
from minisense.retrieval import FAQIndex, chunk_faq


class FakeEncoder:
    """Unit-only embedding stand-in; never used by CLI or real evaluation."""

    def encode(self, texts, **kwargs):
        return np.array(
            [[1.0, 0.0] if "wait" in t.lower() else [0.0, 1.0] for t in texts]
        )


def test_chunking_and_cache(tmp_path):
    faq = tmp_path / "faq.txt"
    faq.write_text("Q: Wait time?\nA: Wait ten minutes.\n\nQ: Menu?\nA: Fresh food.")
    index = FAQIndex(faq, tmp_path / "index", encoder=FakeEncoder(), model="unit-test")
    assert len(chunk_faq(faq.read_text())) == 2
    assert index.ingest() is True
    assert index.ingest() is False
    assert index.retrieve("wait", k=1).chunks[0].id == "faq-01"
    faq.write_text("Q: Changed?\nA: Changed.")
    with pytest.raises(ValueError, match="stale"):
        index.retrieve("wait")


def test_missing_and_threshold(tmp_path):
    faq = tmp_path / "faq.txt"
    faq.write_text("Q: Wait?\nA: Wait.")
    index = FAQIndex(faq, tmp_path / "index", encoder=FakeEncoder(), model="unit-test")
    with pytest.raises(FileNotFoundError):
        index.retrieve("x")
    index.ingest()
    assert not index.retrieve("menu", threshold=0.9).chunks
    with pytest.raises(ValueError):
        index.retrieve("x", k=0)


@pytest.mark.integration
def test_real_embeddings(tmp_path):
    faq = Path("data/faq.txt")
    index = FAQIndex(faq, tmp_path / "index")
    index.ingest()
    result = index.retrieve("expected wait times at peak hours", k=2)
    assert any("15–20" in c.content for c in result.chunks)


def test_cache_reloads_after_external_ingestion(tmp_path):
    faq = tmp_path / "faq.txt"
    faq.write_text("Q: Wait?\nA: Wait.\n\nQ: Menu?\nA: Food.")
    a = FAQIndex(faq, tmp_path / "index", encoder=FakeEncoder(), model="unit-test")
    a.ingest()
    assert a.retrieve("wait", k=1).chunks[0].id == "faq-01"
    faq.write_text("Q: Menu?\nA: Food.\n\nQ: Wait?\nA: Wait.")
    b = FAQIndex(faq, tmp_path / "index", encoder=FakeEncoder(), model="unit-test")
    b.ingest()
    assert a.retrieve("wait", k=1).chunks[0].id == "faq-02"
