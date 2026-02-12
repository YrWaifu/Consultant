from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Matcher:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self.article_embeddings = []
        self.article_names: List[str] = []
        self.legal_articles: List[str] = []
        self.model = SentenceTransformer(model_name)

    def fit(self, articles: List[Dict[str, str]]) -> None:
        self.legal_articles: List[str] = [article["body"] for article in articles]
        self.article_names: List[str] = [article["head"] for article in articles]
        self.article_embeddings = self.model.encode(self.legal_articles)

    def predict_relevance(self, text: str, amount_to_display: int = 1) -> List[Dict[str, str, float]]:
        # чтобы не вызывать исключений определим число для возвращаемых статей как самое минимальное
        # из общего кол-ва статей и аргумента
        how_many_to_display: int = min(amount_to_display, len(self.article_embeddings))
        ad_embedding = self.model.encode([text])
        similarities: List[float] = cosine_similarity(ad_embedding, self.article_embeddings)[0]

        # получаем список индексов самых релевантных статей
        top_indices: List[int] = np.argsort(similarities)[::-1][:how_many_to_display]

        results: List[Dict[str, str, float]] = []
        for idx in top_indices:
            results.append({
                'article': self.article_names[idx],
                'text': self.legal_articles[idx],
                'similarity': similarities[idx]
            })

        return sorted(results, key=lambda x: x['similarity'], reverse=True)
