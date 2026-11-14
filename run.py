"""Run scenarios over a range of seeds and keep the measures.

Usage: python run.py [--only name,name] [--seeds 1-20] [--out runs]
                     [--keep 1] [--watch policy|live|replay]
                     [--decisions file.jsonl]

Each run writes <out>/<scenario>/seed-<n>.json. The evidence bundle is kept
beside it (seed-<n>/) for the seeds named by --keep.

--watch live puts you in the watchtower: each case is shown at the terminal
and your answers are saved to the decisions file, so the same run can be
repeated later with --watch replay. Use one scenario and one seed.
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
    os.environ["DHARMA_DECISIONS"] = os.path.abspath(
        arg("--decisions", "decisions.jsonl")) if watch != "policy" else ""
    names = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, "scenarios"))
                   if f.endswith(".yaml"))
    if only:
        names = [n for n in names if n in only.split(",")]
    jobs = [(n, s, out, keep) for n in names for s in span(arg("--seeds",
                                                               "1-20"))]
    if watch == "live":
        results = map(run, jobs)
    else:
        results = multiprocessing.Pool().imap_unordered(run, jobs)
    for name, seed, failed in results:
        print(f"{name}\t{seed}\t{','.join(failed) or 'none'}", flush=True)
