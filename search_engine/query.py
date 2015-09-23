import json, math
from .base import Base

class Query(Base):
    """Handles queries using the index built up by index.py"""
    def __init__(self):
        pass

    def _one_token_query(self, token):
        """Returns the doc dict for the token, if it exists."""
        return json.loads(self.red.hget('full_idx', token)) \
            if self.red.hexists('full_idx', token) else {}

    def _free_text_query(self, query, all_match=True):
        """Returns the document set matching the terms in
        the query."""
        doc_set, partial_idx = set(), dict()
        tokens = self.tokenize(query)

        if not tokens:
            return None, None, None
        if all_match:
            docs = self._one_token_query(tokens[0])
            doc_set = set(docs.keys()) if docs is not None else set()

        for token in tokens:
            docs = self._one_token_query(token)
            partial_idx[token] = docs if docs is not None else {}
            if all_match:
                doc_set = doc_set.intersection(set(docs.keys()))
            else:
                doc_set = doc_set.union(set(docs.keys()))
        return doc_set, tokens, partial_idx

    def free_text_one_match(self, query):
        """Returns union of docs returned for each token."""
        doc_set, tokens, partial_idx = self._free_text_query(query, False)
        return [] if doc_set is None else self._rank_docs(doc_set, tokens, partial_idx)

    def free_text_all_match(self, query):
        """Returns intersection of docs returned for each token."""
        doc_set, tokens, partial_idx = self._free_text_query(query, True)
        return [] if doc_set is None else self._rank_docs(doc_set, tokens, partial_idx)

    def ordered_text(self, query):
        ds, tokens, partial_idx = self._free_text_query(query, True)
        if ds is None:
            return []
        doc_set = set()
        for doc in ds:
            positions = set(partial_idx[tokens[0]][doc])
            for i, token in enumerate(tokens[1:]):
                positions = positions.intersection(set(
                    [pos-i-1 for pos in partial_idx[token][doc]]
                ))
            if len(positions):
                doc_set.add(doc)
        return [] if not doc_set else self._rank_docs(doc_set, tokens, partial_idx)

    def _rank_docs(self, doc_set, tokens, partial_idx):
        """Ranks all docs that matched query, by first computing
        tf-idf for each token in query, and then computing the dot
        product of this tf-idf vector with the tf-idf vector for
        each doc."""

        # idf need be computed only once for each token, while tf must be computed for each
        # (token,doc) tuple. This computation is fast because partial_idx already contains
        # the doc->position_list dictionary for each token in the query, and the magnitudes of
        # all documents have also be precomputed. For a real service, results of queries could
        # also be cached with Redis and EXPIRED every so often.
        token_idf, query_tf = {}, {}
        num_docs = self.red.hlen('doc_to_magnitude')
        for token in tokens:
            token_idf[token] = math.log(num_docs/max(1,len(partial_idx[token])))
            query_tf[token] = len([t for t in tokens if t == token])

        doc_score = {}
        for doc in doc_set:
            score = 0
            for token, idf in token_idf.items():
                doc_tf = 0
                if token in partial_idx and doc in partial_idx[token]:
                    doc_tf = len(partial_idx[token][doc])
                score += idf * query_tf[token] * doc_tf
            doc_score[doc] = score/float(self.red.hget('doc_to_magnitude', doc))
        return sorted(doc_score.items(), key=lambda x: x[1], reverse=True)


