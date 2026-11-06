"""
In-memory Vector Store and Semantic Retriever for SOP Knowledge Base.
Supports dense vector indexing (NumPy/Cosine) and hybrid symptom keyword matching.
"""

from __future__ import annotations
import math
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel
from app.knowledge.loader import SOPDocument, SOPStep, sop_loader


class SearchResult(BaseModel):
    sop: SOPDocument
    score: float
    matched_step: Optional[SOPStep] = None
    reason: str = ""


class VectorStore:
    def __init__(self, loader=sop_loader):
        self.loader = loader
        self.doc_ids: List[str] = []
        self.corpus: List[str] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.dense_matrix: np.ndarray = np.array([])
        self.is_indexed: bool = False
        self.build_index()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize Vietnamese and English technical text into lowercase tokens and character n-grams."""
        clean = re.sub(r"[^\w\s\.\-]", " ", text.lower())
        tokens = [t.strip() for t in clean.split() if len(t.strip()) > 1]
        
        # Add character tri-grams for sub-word matching of technical terms
        subwords = []
        for t in tokens:
            if len(t) >= 4:
                for i in range(len(t) - 2):
                    subwords.append(t[i:i + 3])
        return tokens + subwords

    def build_index(self):
        """Builds in-memory dense TF-IDF & semantic feature vectors for all SOPs."""
        docs = self.loader.all()
        if not docs:
            self.doc_ids = []
            self.dense_matrix = np.array([])
            self.is_indexed = False
            return

        self.doc_ids = [d.sop_id for d in docs]
        self.corpus = []

        # Construct weighted text representation per SOP: Symptoms > Title > Steps > Body
        for d in docs:
            symptoms_repeated = " ".join(d.symptoms * 3)
            title_repeated = f"{d.title} " * 2
            steps_text = " ".join([f"{s.action} {s.instruction_spoken}" for s in d.steps])
            combined = f"{d.sop_id} {title_repeated} {symptoms_repeated} {steps_text} {d.body_text}"
            self.corpus.append(combined)

        # Build vocabulary
        all_tokens_list = [self.tokenize(text) for text in self.corpus]
        vocab_set = set()
        for tokens in all_tokens_list:
            vocab_set.update(tokens)

        self.vocabulary = {token: idx for idx, token in enumerate(sorted(vocab_set))}
        v_size = len(self.vocabulary)
        n_docs = len(self.corpus)

        if v_size == 0 or n_docs == 0:
            return

        # Compute TF and DF
        tf_matrix = np.zeros((n_docs, v_size), dtype=np.float32)
        df = np.zeros(v_size, dtype=np.float32)

        for d_idx, tokens in enumerate(all_tokens_list):
            seen_in_doc = set()
            for t in tokens:
                t_idx = self.vocabulary[t]
                tf_matrix[d_idx, t_idx] += 1.0
                if t_idx not in seen_in_doc:
                    df[t_idx] += 1.0
                    seen_in_doc.add(t_idx)

        # Compute IDF with smooth weighting
        self.idf = np.log((1.0 + n_docs) / (1.0 + df)) + 1.0

        # Compute normalized TF-IDF matrix (dense vector representation)
        tfidf = tf_matrix * self.idf
        norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        self.dense_matrix = tfidf / norms
        self.is_indexed = True

    def _encode_query(self, query: str) -> np.ndarray:
        """Converts query text into a normalized dense vector."""
        if not self.is_indexed or len(self.vocabulary) == 0:
            return np.zeros((1, 1), dtype=np.float32)

        tokens = self.tokenize(query)
        q_vec = np.zeros(len(self.vocabulary), dtype=np.float32)
        for t in tokens:
            if t in self.vocabulary:
                q_vec[self.vocabulary[t]] += 1.0

        q_tfidf = q_vec * self.idf
        norm = np.linalg.norm(q_tfidf)
        if norm > 0:
            q_tfidf = q_tfidf / norm
        return q_tfidf

    def search(self, query: str, top_k: int = 3, threshold: float = 0.15) -> List[SearchResult]:
        """
        Executes hybrid semantic search over SOPs.
        Combines cosine similarity of dense vectors with exact symptom matches.
        """
        if not self.is_indexed or not self.doc_ids:
            return []

        q_vec = self._encode_query(query)
        if np.linalg.norm(q_vec) == 0:
            return []

        # Cosine similarity matrix multiplication
        cosine_scores = np.dot(self.dense_matrix, q_vec)

        query_lower = query.lower()
        results: List[SearchResult] = []

        for idx, doc_id in enumerate(self.doc_ids):
            base_score = float(cosine_scores[idx])
            sop = self.loader.get(doc_id)
            if not sop:
                continue

            # Boost if any symptom matches directly or has high word overlap
            symptom_boost = 0.0
            matched_reason = "semantic similarity"
            for symptom in sop.symptoms:
                sym_lower = symptom.lower()
                if sym_lower in query_lower or query_lower in sym_lower:
                    symptom_boost = max(symptom_boost, 0.45)
                    matched_reason = f"Khớp triệu chứng: '{symptom}'"
                else:
                    # Token overlap
                    q_words = set(query_lower.split())
                    s_words = set(sym_lower.split())
                    common = q_words.intersection(s_words)
                    if len(common) >= 2:
                        symptom_boost = max(symptom_boost, 0.25)

            final_score = base_score + symptom_boost

            if final_score >= threshold:
                results.append(
                    SearchResult(
                        sop=sop,
                        score=round(min(final_score, 1.0), 4),
                        matched_step=sop.steps[0] if sop.steps else None,
                        reason=matched_reason,
                    )
                )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def get_best_sop(self, query: str) -> Optional[Tuple[SOPDocument, float]]:
        """Returns the single top SOP if it meets confidence threshold."""
        matches = self.search(query, top_k=1)
        if matches:
            return matches[0].sop, matches[0].score
        return None


# Global singleton instance
vector_store = VectorStore(sop_loader)
