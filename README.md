### Search engine
- documents matching the query are found using an inverted index
- documents are ranked using the classic tf-idf scheme

This was inspired by an excellent blog post I found via HN:
http://aakashjapi.com/fuckin-search-engines-how-do-they-work/

To ensure there aren't too many unique tokens (this makes queries faster), tokens are stemmed, punctuation and whitespace are removed, and stopwords are removed. The index supports sub-second queries on a corpus of ~900MB of roughly 20000 docs.

The full list of docs and positions corresponding to each token is stored as a JSON string in a Redis hash, where the token is the key and the JSON string is the value.

### Partitioning
To build a real search engine using this scheme, you would need to partition the index. There are two ways to do this: by token, and by document. Paritioning by token is easy, because the index is composed of key-value pairs where the keys are the tokens. Partitioning by document is more complicated, but for a huge corpus of documents like the internet, it would be necessary.

It's clear that if there are enough documents, the document/position JSON for even one token would not fit in the memory of a single machine. Therefore, independent indices would have to be constructed for chunks of documents in the corpus, and the tokens in the query would be sent to each of these indices. The index for a chunk of documents could then be further partitioned by token if necessary. This would result in clusters of servers such that:
- each cluster is responsible for serving the index for a chunk of documents
- each server in the cluster is responsible for a subset of tokens in that chunk of documents

### LICENSE
This code is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
