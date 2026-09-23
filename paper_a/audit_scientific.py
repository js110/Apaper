#!/usr/bin/env python3
"""Independent author-side consistency checks; never overwrites raw results."""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments'))
sys.path.insert(0, str(ROOT / 'prototype'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reproduce', action='store_true')
    args = parser.parse_args()
    checks = []

    def check(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})

    def read(name):
        return json.loads((ROOT / name).read_text())

    def compare_record(name, regenerated, stored):
        # JSON round trips turn tuples into lists. Compare integer counts and
        # structure exactly; allow only last-bit differences in floating summaries.
        regenerated = json.loads(json.dumps(regenerated))
        discrepancies = []
        max_difference = 0.0

        def compare(a, b, path):
            nonlocal max_difference
            if isinstance(a, dict) and isinstance(b, dict):
                if a.keys() != b.keys():
                    discrepancies.append(path + ': keys differ')
                for key in a.keys() & b.keys():
                    compare(a[key], b[key], path + '/' + key)
            elif isinstance(a, list) and isinstance(b, list):
                if len(a) != len(b):
                    discrepancies.append(path + ': length differs')
                for i, (left, right) in enumerate(zip(a, b)):
                    compare(left, right, path + '/' + str(i))
            elif isinstance(a, float) and isinstance(b, float):
                difference = abs(a-b)
                max_difference = max(max_difference, difference)
                if not math.isfinite(difference) or difference > 1e-12:
                    discrepancies.append(f'{path}: {a} != {b}')
            elif a != b:
                discrepancies.append(f'{path}: {a!r} != {b!r}')

        compare(regenerated, stored, '')
        check(name, not discrepancies)
        checks[-1]['max_float_difference'] = max_difference
        checks[-1]['discrepancies'] = discrepancies[:10]
        if discrepancies:
            print(discrepancies[:10], flush=True)

    metrics = ('false_accept_rate', 'false_reject_rate', 'ambiguous_rate',
               'evidence_failure_rate', 'decisive_coverage', 'decisive_accuracy')
    for budget, filename in enumerate(('semantic_results.json', 'semantic_results_r1.json', 'semantic_results_r2.json')):
        data = read('experiments/' + filename)
        valid_counts = valid_rates = valid_summaries = True
        for condition, methods in data['seed_counts'].items():
            for method, rows in methods.items():
                recalculated = []
                for index, row in enumerate(rows):
                    total = row['inside'] + row['outside']
                    decisive = row['robust_valid'] + row['robust_invalid']
                    valid_counts &= total == 80 and sum(row[k] for k in
                        ('robust_valid', 'robust_invalid', 'ambiguous', 'evidence_failure')) == total
                    valid_counts &= row['correct_decisive'] + row['false_accept'] + row['false_reject'] == decisive
                    numbers = (row['false_accept'], row['false_reject'], row['ambiguous'],
                               row['evidence_failure'], decisive, row['correct_decisive'])
                    denominators = (row['outside'], row['inside'], total, total, total, decisive)
                    rates = {k: a / b if b else None for k, a, b in zip(metrics, numbers, denominators)}
                    valid_rates &= rates == data['seed_results'][condition][method][index]
                    recalculated.append(rates)
                for metric in metrics:
                    values = [r[metric] for r in recalculated if r[metric] is not None]
                    stat = data['aggregate'][condition][method][metric]
                    valid_summaries &= len(values) == stat['defined_seeds']
                    if values:
                        mean = sum(values) / len(values)
                        half = 1.96 * math.sqrt(sum((x - mean)**2 for x in values) /
                            (len(values) - 1) / len(values)) if len(values) > 1 else 0
                        valid_summaries &= all(abs(stat[k] - v) < 1e-12 for k, v in
                            [('mean', mean), ('ci95_low', mean-half), ('ci95_high', mean+half)])
                    else:
                        valid_summaries &= all(stat[k] is None for k in ('mean', 'ci95_low', 'ci95_high'))
        check(f'r={budget}: all event-count partitions', valid_counts)
        check(f'r={budget}: all seed rates rederived from counts', valid_rates)
        check(f'r={budget}: all means and normal intervals rederived', valid_summaries)
        if args.reproduce:
            from run_semantic_evaluation import run
            print(f'Reproducing synthetic r={budget} (64,800 observations)', flush=True)
            design = data['design']
            repeat = run(argparse.Namespace(seeds=design['seeds'],
                events_per_seed=design['events_per_seed_per_condition'],
                seed_base=design['seed_base'], sources=design['sources'],
                assumed_byzantine=design['assumed_byzantine'], miscoverage_budget=budget))
            compare_record(f'r={budget}: regenerated record matches (float tolerance 1e-12)', repeat, data)

    data = read('experiments/semantic_results.json')
    selected = [v for k, v in data['aggregate'].items()
                if k.startswith('calibrated_') and k.endswith(('byz_0', 'byz_1'))]
    check('abstract coverage means from twelve conditions', len(selected) == 12 and
        round(100*np.mean([v['robust_depth']['decisive_coverage']['mean'] for v in selected]), 2) == 87.52 and
        round(100*np.mean([v['fixed_margin']['decisive_coverage']['mean'] for v in selected]), 2) == 75.63)
    focus = data['seed_results']['calibrated_correlated__radius_4__byz_1']
    differences = np.array([a['decisive_coverage'] - b['decisive_coverage'] for a, b in
                           zip(focus['robust_depth'], focus['fixed_margin'])])
    bootstrap = np.random.default_rng(20260905).choice(differences, (10000, 30)).mean(axis=1)
    paired = read('experiments/paired_comparison.json')
    check('paired bootstrap regenerated', abs(100*differences.mean()-paired['mean_percentage_points']) < 1e-12 and
          np.allclose(100*np.quantile(bootstrap, [.025, .975]), paired['bootstrap95_percentage_points'], atol=1e-12))

    for prefix in ('zkdepth', 'subset'):
        for path in sorted((ROOT/'experiments').glob(prefix + '_*_formal.json')):
            result = json.loads(path.read_text())
            check(path.stem + ': stored medians agree with raw timings',
                  result['prove_median_ms'] == float(np.median(result['prove_ms'])) and
                  result['verify_median_ms'] == float(np.median(result['verify_ms'])))
    manifest = read('figures/figure_manifest.json')
    check('four experimental figures retain matching source hashes', all(
        hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in manifest['sources'].items()))
    check('experimental figure renderer matches recorded hash',
        hashlib.sha256((ROOT/'figures/render_results.py').read_bytes()).hexdigest() == manifest['script_sha256'])
    with (ROOT/'figures/backend_costs_data.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    check('all 300 plotted proving times match raw observations', len(rows) == 300 and all(
        float(r['prove_ms']) == read('experiments/' + ('zkdepth' if r['backend'] == 'Lower-corner' else 'subset') +
            f"_n{r['n']}_d{r['d']}_formal.json")['prove_ms'][int(r['repetition'])-1] for r in rows))

    if args.reproduce:
        import run_trace_evaluation as replay
        print('Reproducing both trajectory replay modes (47,220 event evaluations)', flush=True)
        with tempfile.TemporaryDirectory(prefix='paper-a-replay-audit-') as directory:
            original_here = replay.HERE
            replay.HERE = Path(directory)
            shutil.copyfile(ROOT/'experiments/UrbanNav_TST_GT_raw.txt', replay.HERE/'UrbanNav_TST_GT_raw.txt')
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    replay.main()
                repeated = json.loads((replay.HERE/'trace_results.json').read_text())
            finally:
                replay.HERE = original_here
        original = read('experiments/trace_results.json')
        added_counts = []
        for mode, record in repeated['results'].items():
            for method, stats in record['aggregate'].items():
                for metric, stat in stats.items():
                    old = original['results'][mode]['aggregate'][method][metric]
                    if 'defined_seeds' not in old:
                        added_counts.append(stat.pop('defined_seeds'))
        check('replay schema-only added defined-seed counts all equal 30',
              len(added_counts) == 60 and set(added_counts) == {30})
        compare_record('trajectory replay matches apart from documented added seed-count metadata', repeated, original)

    report = {'scope': 'Local consistency and deterministic regeneration, not external peer review or deployment validation',
              'full_regeneration': args.reproduce, 'checks': checks,
              'passed': sum(c['passed'] for c in checks), 'total': len(checks)}
    (ROOT/'evidence/scientific_recheck_20260922.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if report['passed'] != report['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
