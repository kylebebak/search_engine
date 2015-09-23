import sys, os

from search_engine import index
idx = index.Index()
path = sys.argv[1]

for dir_entry in os.listdir(path):
    dir_entry_path = os.path.join(path, dir_entry)
    if os.path.isfile(dir_entry_path):
        # use doc names instead of full doc paths
        idx.add_doc_to_lcl_idx(dir_entry_path, dir_entry)
        print('added {0} as {1}'.format(dir_entry_path, dir_entry))

idx.merge_lcl_idx_with_full_idx()
