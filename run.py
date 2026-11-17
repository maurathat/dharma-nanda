"""Run scenarios over a range of seeds and keep the measures.

Usage: python run.py [--only name,name] [--seeds 1-20] [--out runs]
                     [--keep 1] [--watch policy|live|replay] [--first n]
                     [--quiet]
                     [--decisions file.jsonl]

Each run writes <out>/<scenario>/seed-<n>.json. The evidence bundle is kept
beside it (seed-<n>/) for the seeds named by --keep.

--watch live puts you in the watchtower: each case is shown at the terminal
and your answers are saved to the decisions file, so the same run can be
repeated later with --watch replay. Use one scenario and one seed. With
--first n you decide the first n cases and the stand-in policy the rest.
"""

import json
import multiprocessing
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def arg(flag, default):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def span(text):
    lo, _, hi = text.partition("-")
    return range(int(lo), int(hi or lo) + 1)


def run(job):
    name, seed, out, keep = job
    from nandatown.sim.runner import run_lab

    target = os.path.join(out, name)
    bundle, result = run_lab(os.path.join(HERE, "scenarios", name + ".yaml"),
                             target, seed=seed)
    import dharma_nanda as dn

    with open(os.path.join(bundle, "profile.json"), encoding="utf-8") as fh:
        profile = json.load(fh)
    with open(os.path.join(bundle, "events.jsonl"), encoding="utf-8") as fh:
        events = [json.loads(line) for line in fh if '"dn_' in line]
    record = dn.measure(events, dn.cast_of(profile["agents"]),
                        profile["layers"]["data_facts"])
    failed = [s.name for s in result.stages if s.status == "failed"]
    record.update(seed=seed, failed=failed)
    with open(os.path.join(target, f"seed-{seed}.json"), "w") as fh:
        json.dump(record, fh, sort_keys=True)
    final = os.path.join(target, f"seed-{seed}")
    shutil.rmtree(final, ignore_errors=True)
    if seed in keep:
        os.rename(bundle, final)
    else:
        shutil.rmtree(bundle)
    return name, seed, failed


if __name__ == "__main__":
    only = arg("--only", "")
    out = arg("--out", "runs")
    keep = frozenset(span(arg("--keep", "1")))
    watch = arg("--watch", "policy")
    os.environ["DHARMA_WATCH"] = watch
    os.environ["DHARMA_WATCH_FIRST"] = arg("--first", "0")
    os.environ["DHARMA_DECISIONS"] = os.path.abspath(
        arg("--decisions", "decisions.jsonl")) if watch != "policy" else ""
    names = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, "scenarios"))
                   if f.endswith(".yaml"))
    if only:
        names = [n for n in names if n in only.split(",")]
    jobs = [(n, s, out, keep) for n in names for s in span(arg("--seeds",
                                                               "1-20"))]
    first, quiet = int(arg("--first", "0")), "--quiet" in sys.argv
    pool = None
    if watch == "live" or len(jobs) == 1:
        results = map(run, jobs)
    else:
        pool = multiprocessing.Pool()
        results = pool.imap_unordered(run, jobs)
    for name, seed, failed in results:
        if not quiet:
            print(f"{name}\t{seed}\t{','.join(failed) or 'none'}",
                  flush=True)
        if watch == "live" and first:
            with open(os.path.join(out, name, f"seed-{seed}.json")) as fh:
                m = json.load(fh)
            live = min(first, m["watch_cases"])
            saved = m["watch_by_person"] - live
            rest = m["watch_cases"] - m["watch_by_person"]
            print(f"\nYou decided the first {live} cases."
                  + (f" A person's saved answers decided {saved} more."
                     if saved else "")
                  + (f" The stand-in policy decided {rest}." if rest else "")
                  + f" Right: {m['watch_right']} of {m['watch_cases']}.")
        elif watch == "live":
            with open(os.path.join(out, name, f"seed-{seed}.json")) as fh:
                m = json.load(fh)
            with open(os.environ["DHARMA_DECISIONS"]) as fh:
                secs = sorted(json.loads(line).get("seconds", 0)
                              for line in fh)
            print(f"\nYou decided {m['watch_by_person']} of"
                  f" {m['watch_cases']} cases and got"
                  f" {m['watch_person_right']} right. Median time per"
                  f" case: {secs[len(secs) // 2] if secs else 0} seconds;"
                  f" total {sum(secs):.0f} seconds.")
            print(f"Honest sellers suspended: {len(m['honest_suspended'])}"
                  f" of {m['honest']}. Buyers' net: {m['net']:,} cents.")
    if pool:
        pool.close()
        pool.join()
