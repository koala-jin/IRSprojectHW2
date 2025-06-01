from sentence_transformers import util
import numpy as np

class SemanticSearcher:
    def __init__(self, embedder, documents, field='title+abstract'):
        self.embedder = embedder
        self.field = field
        self.raw_docs = documents
        self.doc_embeddings = self.embedder.encode([self._get_field_content(doc) for doc in documents])

    def _get_field_content(self, doc):
        if self.field == "title":
            return doc["title"]
        elif self.field == "abstract":
            return doc["abstract"]
        elif self.field == "authors":
            return doc["authors"]
        elif self.field == "category":
            return doc["category"]
        else:
            return doc["title"] + " " + doc["abstract"]

    def search(self, query, top_k=1000, sort_by="relevance"):
        query_embedding = self.embedder.encode([query])[0]
        similarities = util.cos_sim(query_embedding, self.doc_embeddings)[0].cpu().numpy()

        if sort_by == "relevance":
            top_indices = similarities.argsort()[::-1]
        elif sort_by == "date":
            top_indices = sorted(range(len(self.raw_docs)), key=lambda i: self.raw_docs[i]["published"], reverse=True)
        else:
            top_indices = similarities.argsort()[::-1]

        return [(self.raw_docs[i]["id"], float(similarities[i])) for i in top_indices[:top_k]]