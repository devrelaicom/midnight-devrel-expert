"""Highest existing relnote for an item. Pure core + thin dir shell."""
import json, sys, os
from . import lib

def highest_relnote(filenames, file_prefix):
    best = None
    for name in filenames:
        if not name.endswith(".mdx"):
            continue
        version = lib.filename_to_version(name, file_prefix)
        if version is None:
            continue
        if best is None or lib.cmp_release(version, best["version"]) > 0:
            best = {"version": version, "filename": name}
    return best

def main(argv=None):
    argv = argv or sys.argv[1:]
    directory, file_prefix = argv[0], argv[1]
    names = os.listdir(directory) if os.path.isdir(directory) else []
    print(json.dumps(highest_relnote(names, file_prefix)))

if __name__ == "__main__":
    main()
