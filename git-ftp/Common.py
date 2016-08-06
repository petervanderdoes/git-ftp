import os


def get_empty_tree(repo):
    return repo.tree(repo.git.hash_object('-w', '-t', 'tree', os.devnull))

def format_mode(mode):
    return "%o" % (mode & 0o777)