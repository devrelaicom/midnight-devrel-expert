"""Join a latest relnote against latest release into a staleness verdict."""
import json, sys
from . import lib

def verdict(relnote_version, stable, all_stable):
    if relnote_version is None:
        gap = list(all_stable)
    else:
        gap = [v for v in all_stable if lib.cmp_release(v, relnote_version) > 0]
    if stable is not None:
        gap = [v for v in gap if lib.cmp_release(v, stable) <= 0]
    behind = len(gap)
    return {
        "latest_relnote": relnote_version,
        "latest_stable": stable,
        "behind": behind,
        "stale": behind > 0,
        "more_than_one_behind": behind > 1,
        "gap_versions": gap,
    }

def main(argv=None):
    argv = argv or sys.argv[1:]
    relnote, stable, all_stable = json.loads(argv[0]), json.loads(argv[1]), json.loads(argv[2])
    print(json.dumps(verdict(relnote, stable, all_stable)))

if __name__ == "__main__":
    main()
