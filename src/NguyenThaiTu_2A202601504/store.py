from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": doc.metadata,
            "embedding": self._embedding_fn(doc.content)
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_emb = self._embedding_fn(query)
        import math
        mag_q = math.sqrt(sum(x*x for x in query_emb))
        
        results = []
        for r in records:
            emb = r["embedding"]
            mag_r = math.sqrt(sum(x*x for x in emb))
            if mag_q == 0.0 or mag_r == 0.0:
                sim = 0.0
            else:
                sim = _dot(query_emb, emb) / (mag_q * mag_r)
            results.append({
                "id": r["id"],
                "content": r["content"],
                "metadata": r["metadata"],
                "score": sim
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return
            
        if self._use_chroma and self._collection is not None:
            ids = [d.id for d in docs]
            documents = [d.content for d in docs]
            embeddings = [self._embedding_fn(d.content) for d in docs]
            metadatas = [d.metadata if d.metadata else {} for d in docs]
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        else:
            for d in docs:
                self._store.append(self._make_record(d))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            res = self._collection.query(query_embeddings=[query_emb], n_results=top_k)
            results = []
            if res and res.get("ids") and len(res["ids"]) > 0:
                for i in range(len(res["ids"][0])):
                    score = res["distances"][0][i] if res.get("distances") else 0.0
                    results.append({
                        "id": res["ids"][0][i],
                        "content": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "score": -score  # distance is lower better, convert to score where higher is better
                    })
                results.sort(key=lambda x: x["score"], reverse=True)
            return results
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)
            
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_emb], 
                n_results=top_k,
                where=metadata_filter
            )
            results = []
            if res and res.get("ids") and len(res["ids"]) > 0:
                for i in range(len(res["ids"][0])):
                    score = res["distances"][0][i] if res.get("distances") else 0.0
                    results.append({
                        "id": res["ids"][0][i],
                        "content": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "score": -score
                    })
                results.sort(key=lambda x: x["score"], reverse=True)
            return results
        else:
            filtered_records = []
            for r in self._store:
                match = True
                for k, v in metadata_filter.items():
                    if r["metadata"].get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(r)
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            try:
                # Delete by id
                res1 = self._collection.get(ids=[doc_id])
                has_exact = len(res1["ids"]) > 0
                if has_exact:
                    self._collection.delete(ids=[doc_id])
                
                # Delete by metadata
                res2 = self._collection.get(where={"doc_id": doc_id})
                has_meta = len(res2["ids"]) > 0
                if has_meta:
                    self._collection.delete(ids=res2["ids"])
                    
                return has_exact or has_meta
            except Exception:
                return False
        else:
            initial_len = len(self._store)
            self._store = [
                r for r in self._store 
                if r["id"] != doc_id and r["metadata"].get("doc_id") != doc_id
            ]
            return len(self._store) < initial_len
