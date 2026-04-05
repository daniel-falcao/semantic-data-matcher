"""
Core semantic matching logic using sentence-transformers.
Supports Excel (.xlsx) and CSV (.csv) input files.
"""

import torch
from sentence_transformers import SentenceTransformer, util


class SemanticMatcher:
    """
    Encapsulates the NLP model and semantic similarity logic.
    Loads the domain table once and reuses embeddings across calls.
    """

    DEFAULT_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'

    def __init__(self, domain_descriptions: list[str], model_name: str = DEFAULT_MODEL):
        """
        Args:
            domain_descriptions: List of text strings from the domain reference table.
            model_name: HuggingFace sentence-transformers model identifier.
        """
        self.model = SentenceTransformer(model_name)
        self.domain_descriptions = domain_descriptions
        self.domain_embeddings = self.model.encode(
            domain_descriptions,
            convert_to_tensor=True,
            show_progress_bar=True,
        )

    def find_best_match(self, text: str, threshold: float = 0.75) -> tuple[int | None, float]:
        """
        Returns the index of the best matching domain entry and its similarity score.

        Args:
            text: Input text to match.
            threshold: Minimum cosine similarity score to consider a valid match.

        Returns:
            (index, score) if match found above threshold, else (None, score).
        """
        if not isinstance(text, str) or not text.strip():
            return None, 0.0

        text_embedding = self.model.encode(text, convert_to_tensor=True)
        similarities = util.cos_sim(text_embedding, self.domain_embeddings)[0]
        best_idx = torch.argmax(similarities).item()
        best_score = similarities[best_idx].item()

        if best_score >= threshold:
            return best_idx, best_score
        return None, best_score
