"""Small persisted dense-vector store; exact cosine search over FAQ sections."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from .contracts import Chunk, Retrieval

DEFAULT_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'


def chunk_faq(text: str) -> list[str]:
    sections = text.split('\n\n')
    chunks = [s.strip() for s in sections if s.strip().startswith('Q:')]
    if not chunks or any('\nA:' not in c for c in chunks):
        raise ValueError('FAQ must contain complete Q/A paragraphs')
    if any(len(c.split()) > 180 for c in chunks):
        raise ValueError('FAQ section too long; split into smaller complete Q/A sections')
    return chunks


class FAQIndex:
    def __init__(self, faq: Path, directory: Path, model: str | None = None, encoder=None):
        self.faq, self.directory = faq, directory
        self.model = model or os.getenv('MINISENSE_EMBEDDING_MODEL',DEFAULT_MODEL)
        self.encoder = encoder
        self._vectors = None
        self._metadata = None

    def _signature(self):
        return {'model':self.model,'sha256':hashlib.sha256(self.faq.read_bytes()).hexdigest(),'format':1}

    def _encode(self, texts):
        if self.encoder is None:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(self.model, device='cpu')
        values = np.asarray(self.encoder.encode(texts,normalize_embeddings=True,show_progress_bar=False),dtype=np.float32)
        norms = np.linalg.norm(values,axis=1,keepdims=True)
        if not np.isfinite(values).all() or (norms == 0).any():
            raise ValueError('Embedding model returned invalid vectors')
        return values / norms

    def ingest(self) -> bool:
        metadata = self.directory/'metadata.json'
        if metadata.exists() and (self.directory/'vectors.npy').exists():
            if json.loads(metadata.read_text(encoding='utf-8'))['signature'] == self._signature():
                return False
        chunks = [Chunk(id=f'faq-{i+1:02}',source=self.faq.name,content=c) for i,c in enumerate(chunk_faq(self.faq.read_text(encoding='utf-8')))]
        vectors = self._encode([c.content for c in chunks])
        self.directory.mkdir(parents=True,exist_ok=True)
        np.save(self.directory/'vectors.npy',vectors,allow_pickle=False)
        metadata.write_text(json.dumps({'signature':self._signature(),'chunks':[c.model_dump() for c in chunks]},ensure_ascii=False,indent=2),encoding='utf-8')
        self._vectors, self._metadata = None, None
        return True

    def retrieve(self, query: str, k: int = 3, threshold: float = .25) -> Retrieval:
        if not query.strip() or not 1 <= k <= 10 or not -1 <= threshold <= 1:
            raise ValueError('Require a nonempty query, k between 1 and 10, threshold between -1 and 1')
        if not (self.directory/'metadata.json').exists():
            raise FileNotFoundError('FAQ index missing: run python -m minisense ingest')
        metadata = json.loads((self.directory/'metadata.json').read_text(encoding='utf-8'))
        if metadata['signature'] != self._signature():
            raise ValueError('FAQ index is stale: run python -m minisense ingest')
        if self._vectors is None:
            self._vectors = np.load(self.directory/'vectors.npy',allow_pickle=False)
        scores = self._vectors @ self._encode([query])[0]
        chunks=[]
        for i in np.argsort(-scores)[:k]:
            if float(scores[i]) >= threshold:
                chunks.append(Chunk(**{**metadata['chunks'][int(i)],'score':float(scores[i])}))
        return Retrieval(query=query,chunks=chunks,limitation=None if chunks else 'No FAQ chunk passed the relevance threshold.')
