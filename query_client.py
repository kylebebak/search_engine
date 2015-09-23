import sys

import redis

from search_engine import query

red = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
search = query.Query()
qu = sys.argv[1]

def format_result(result):
    return '{:<60}: {}'.format(red.hget('id_to_doc', result[0]), result[1])


for res in search.free_text_all_match(qu):
    print(format_result(res))

print()
for res in search.ordered_text(qu):
    print(format_result(res))
