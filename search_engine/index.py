import codecs, json
from .base import Base

class Index(Base):
    """Class for building and updating inverted index with
    tf-idf scores for all terms and documents."""
    def __init__(self):
        self.lcl_idx = {}

    # DOC <--> ID
    def assign_id_to_doc(self, doc):
        """Creates a bidirectional HSET mapping between a document and an
        auto-incrementing id. Uses a pipeline (transaction) to ensure
        bidirectional integrity. Returns the id for the document."""
        doc_id = self.red.hget('doc_to_id', doc)
        if doc_id is None:
            doc_id = 0 if self.red.get('doc_id') is None else self.red.get('doc_id')
            self.red.pipeline().incr('doc_id').hset('doc_to_id', doc, doc_id). \
                hset('id_to_doc', str(doc_id), doc).execute()
        return doc_id

    def assign_magnitude_to_doc(self, magnitude, doc_id):
        """Uses an HSET to assign a magnitude to every doc."""
        self.red.hset('doc_to_magnitude', doc_id, max(magnitude,1))

    # CREATING LCL IDX
    def doc_to_tokens(self, doc_path):
        """Accepts a doc_path, reads the doc, and returns a list of all tokens
        in the doc. It stems the tokens, removes punctuation, strips whitespace,
        removes stopwords, and makes tokens entirely lowercase."""
        with codecs.open(doc_path, 'r', encoding='utf-8', errors='ignore') as doc:
            doc_tokens = []
            for line in doc.readlines():
                doc_tokens.extend(self.tokenize(line))
            return doc_tokens

    def idx_one_doc(self, tokens):
        """
        input: [token1, token2, ...]
        output: {token1: [1, 7], token2: [2, 434], ...}
        """
        doc_idx = {}
        for idx, token in enumerate(tokens):
            if token in doc_idx.keys():
                doc_idx[token].append(idx)
            else:
                doc_idx[token] = [idx]
        return doc_idx

    def add_doc_to_lcl_idx(self, doc_path, doc_name=None):
        """
        This adds the doc_name/doc_idx pair to the lcl idx.
        This allows the lcl idx to be built incrementally,
        one doc at a time.

        Replaces doc_name values with doc_id values, to save space.
        Also assign and cache magnitude for each doc processed.

        input: doc_name -> {token1: [1, 7], token2: [2, 434], ...}
        output: {token1: {doc_id1: [pos1, pos2, ...]}, ...}
        """
        doc_id = self.assign_id_to_doc(doc_path) if doc_name is None \
            else self.assign_id_to_doc(doc_name)

        doc_idx = self.idx_one_doc(self.doc_to_tokens(doc_path))
        magnitude = 0
        for token, positions in doc_idx.items():
            if token not in self.lcl_idx:
                self.lcl_idx[token] = {}
            self.lcl_idx[token][doc_id] = positions
            magnitude += len(positions)**2
        self.assign_magnitude_to_doc(magnitude**0.5, doc_id)
        return self.lcl_idx

    # MERGING LCL IDX WITH FULL IDX
    def merge_lcl_idx_with_full_idx(self):
        """
        Merges the lcl idx into the full idx in the key-value store.
        input: {token1: {doc_id1: [pos1, pos2, ...]}, ...}, ...}
        """
        for token, lcl_docs in self.lcl_idx.items():
            full_docs = json.loads(self.red.hget('full_idx', token)) \
                if self.red.hexists('full_idx', token) else {}
            for doc, positions in lcl_docs.items():
                full_docs[doc] = positions
            self.red.hset('full_idx', token, json.dumps(full_docs))
        self.red.save()




