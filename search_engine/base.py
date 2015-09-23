"""
Building a search engine
http://aakashjapi.com/fuckin-search-engines-how-do-they-work/

First, an inverted index is constructed for a corpus of documents.
input: [doc1, doc2, ...]
output: {token1: {doc_name1: [pos1, pos2, ...]}, ...}, ...}


Dependencies:
key-value store for inverted index and all query operations (Redis)
relational database for storing raw documents for retrieval (Postgres)
redis-server ~/.redis/se/redis.conf


TODO:
Put docs in database, read them from there. They will have:
id (PK), path (unique, NK), content, size, and date_added

Mixin with static constants, inherited by both index class and query class, like TOKEN_NAMESPACE.

When a query is executed, the index for each token in the query can be read into python memory from Redis. This means that Redis can store a JSON blob for each token, which should occupy much less space than storing the whole inverted index in Python, which makes it easy to persist and update the full index using RDB.

import os
import psutil
process = psutil.Process(os.getpid())
print(process.memory_info()[0] / float(2 ** 20))
1813.26171875 (MB of memory usage. I'd like to compare this with a redis database storing the same JSON). I'd also like to see the memory usage if the file names were integers instead of file names.

"""
from stemming.porter2 import stem
import re, redis

class Base(object):
    """Base mixin with helper functions and a connection to
    key-value store and DB."""

    red = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    stopwords = set(['a', 'able', 'about', 'across', 'after', 'aint', 'all', 'almost', 'also', 'am', 'among', 'an', 'and', 'any', 'are', 'arent', 'as', 'at', 'be', 'because', 'been', 'but', 'by', 'can', 'cannot', 'cant', 'could', 'couldnt', 'couldve', 'dear', 'did', 'didnt', 'do', 'does', 'doesnt', 'dont', 'either', 'else', 'ever', 'every', 'for', 'from', 'get', 'got', 'had', 'has', 'hasnt', 'have', 'he', 'hed', 'her', 'hers', 'hes', 'him', 'his', 'how', 'howd', 'however', 'howll', 'hows', 'i', 'id', 'if', 'ill', 'im', 'in', 'into', 'is', 'isnt', 'it', 'its', 'ive', 'just', 'least', 'let', 'like', 'likely', 'may', 'me', 'might', 'mightnt', 'mightve', 'most', 'must', 'mustnt', 'mustve', 'my', 'neither', 'no', 'nor', 'not', 'of', 'off', 'often', 'on', 'only', 'or', 'other', 'our', 'own', 'rather', 'said', 'say', 'says', 'she', 'shes', 'should', 'shouldnt', 'shouldve', 'since', 'so', 'some', 'than', 'that', 'thatll', 'thats', 'the', 'their', 'them', 'then', 'there', 'theres', 'these', 'they', 'theyd', 'theyll', 'theyre', 'theyve', 'this', 'tis', 'to', 'too', 'twas', 'urllink', 'us', 'wants', 'was', 'wasnt', 'we', 'wed', 'well', 'were', 'werent', 'what', 'whatd', 'whats', 'when', 'whend', 'whenll', 'whens', 'where', 'whered', 'wherell', 'wheres', 'which', 'while', 'who', 'whod', 'wholl', 'whom', 'whos', 'why', 'whyd', 'whyll', 'whys', 'will', 'with', 'wont', 'would', 'wouldnt', 'wouldve', 'yet', 'you', 'youd', 'youll', 'your', 'youre', 'youve'])

    # HELPER FUNCTIONS FOR CLEANING
    def remove_punctuation(self, s):
        table_del = {ord(c): None for c in '\'’'}
        table_space = {ord(c): ' ' for c in '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'}
        return s.translate(table_del).translate(table_space)

    # ignore lines with html tags
    ignore_pattern = re.compile('</?\w+>')
    def tokenize(self, s):
        if self.ignore_pattern.search(s):
            return []
        return [stem(token) for token in
            self.remove_punctuation(s.strip().lower()).split() if token not in self.stopwords]



