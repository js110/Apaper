#!/usr/bin/env python3
"""Local numeric/traceability audit. This is not submission approval."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent

def main():
    manuscript=(ROOT/'paper_a.tex').read_text()
    bibliography=(ROOT/'references.bib').read_text()
    checks=[]
    def check(name,passed):
        checks.append(dict(check=name,passed=bool(passed)))
    check('appendix is referenced explicitly without duplicated prefix',r'Appendix~\ref{app:receiver}' in manuscript and 'Appendix Appendix' not in manuscript)
    check('decision table names inconsistent state', 'Inconsistent' in manuscript)
    check('signed-box prehash assumption explicit', 'collision resistance' in manuscript and 'MiMC' in manuscript)
    check('composed conditional acceptance bound present', r'\\label{prop:composition}' in manuscript and 'varepsilon_{\\mathrm{ctx}}' in manuscript)
    check('privacy boundary covers report guessing', 'low-entropy or enumerable space' in manuscript and r'\\label{tab:privacy-boundary}' in manuscript)
    check('canonical code and manuscript repositories separated', 'https://github.com/js110/ZCRSC-PAPER' in manuscript and 'https://github.com/js110/Apaper' in manuscript and 'Repository access is currently restricted' not in manuscript)
    check('point baseline table populated and sourced', '2 & 408 & 164 & 268' in manuscript and '3 & 612 & 164 & 396' in manuscript and 'point\\_baseline.go' in manuscript)
    summary=json.loads((ROOT/'experiments/results_summary.json').read_text())
    cluster=summary['focus_seed_cluster_wrong_decisive']
    check('focus zero-error cluster bound recorded', cluster['clusters']==30 and cluster['clusters_with_any_wrong_decisive']==0 and abs(cluster['one_sided_exact_upper95_if_zero']-0.09503385285530419)<1e-15)
    scientific=json.loads((ROOT/'evidence/scientific_recheck_20260922.json').read_text())
    check('scientific regeneration audit passes',scientific['full_regeneration'] and scientific['passed']==scientific['total']==29)
    metadata=json.loads((ROOT/'evidence/reference_metadata_recheck_20260922.json').read_text())['records']
    check('18 DOI records successfully retrieved',len(metadata)==18 and all(r['retrieved'] for r in metadata))
    check('DOI titles authors years and pages agree',all(all(r.get(k) is True for k in ('title_matches','author_surnames_match','year_matches','pages_match')) for r in metadata))
    check('author order matches user-supplied metadata',
          re.findall(r'\\author\[aff1\]\{([^}]+)\}',manuscript)==
          ['Lili He','Sheng Jiang','Linghui Lyu',r'Lei Zhang\corref{cor1'])
    check('corresponding author and email match user-supplied metadata',
          r'\author[aff1]{Lei Zhang\corref{cor1}}' in manuscript and
          r'\cortext[cor1]{Corresponding author: Lei Zhang.}' in manuscript and
          r'\ead{8213662@163.com}' in manuscript)
    check('shared affiliation matches user-supplied metadata',
          r'\affiliation[aff1]{organization={College of Information and Electronic Technology, Jiamusi University},' in manuscript and
          'city={Jiamusi},postcode={154007},country={China}}' in manuscript)
    expected_funding=('This work was supported in part by the Heilongjiang Provincial University Teacher Scientific Research Business Fee under Grant 2018-KYYWF0941, '
                      'in part by the Heilongjiang Provincial Natural Science Foundation Joint Fund Cultivation Project under Grant PL2024F002, '
                      'in part by the National Foreign Expert Key Support Project under Grant D2O25O185, '
                      'and in part by the Heilongjiang Provincial Undergraduate University Excellent Young Teacher Fundamental Research Support Plan under Grant YQJH2024239.')
    check('funding wording exactly matches user-supplied statement',expected_funding in manuscript)
    citations=set(k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',manuscript) for k in group.split(','))
    keys=set(re.findall(r'@\w+\{([^,]+),',bibliography))
    check('all cited keys exist',citations<=keys)
    check('no unused bibliography entries', keys==citations)
    resource_keys={'gnark','GraphGNSSData','SemaphoreDocs'}
    check('at least 20 cited scholarly works excluding software and documentation',len(citations-resource_keys)>=20)
    venue_keys={'Shen2024','Ghani2025','Mdee2022','Sultana2024','Wang2025ZKAuth'}
    check('five selected Vehicular Communications articles cited',venue_keys<=citations)
    comparison=re.search(r'\\label\{tab:related-work\}(.*?)\\end\{table\}',manuscript,re.S)
    comparison_text=comparison.group(1) if comparison else ''
    comparison_cites=re.findall(r'\\cite\{([^}]+)\}',comparison_text)
    check('comparison separately cites eight related systems',len(comparison_cites)==8 and
          set(comparison_cites)=={'Zheng2025BARM','Zhou2024','Shen2024','BFTPoLoc','PG','CRSF','ZKLP','VehiclePolicy'})
    check('comparison includes present work and protocol-abort distinction',
          r'\textbf{This work}' in comparison_text and
          'four decisions are valid, invalid, ambiguous, and inconsistent' in comparison_text and
          'missing signatures instead cause protocol abort' in comparison_text)
    bbl=(ROOT/'paper_a.bbl').read_text()
    check('compiled bibliography count matches actual citations',len(re.findall(r'\\bibitem(?:\[[^\]]*\])?\{',bbl))==len(citations))
    added_metadata=json.loads((ROOT/'evidence/added_reference_metadata_20260915.json').read_text())
    check('14 historical DOI metadata records retained',added_metadata['count']==14)
    recent_metadata=json.loads((ROOT/'evidence/recent_reference_metadata_20260916.json').read_text())
    check('six recent replacement DOI records retained',recent_metadata['count']==len(recent_metadata['entries'])==6)
    years={}
    for entry in re.split(r'(?=@\w+\{)',bibliography):
        key=re.match(r'@\w+\{([^,]+),',entry)
        year=re.search(r'\byear\s*=\s*\{(\d{4})\}',entry)
        if key and year:
            years[key.group(1)]=int(year.group(1))
    check('all cited entries have an auditable publication year',set(years)==citations)
    check('CRSF citation uses current arXiv v3','2609.01096v3' in bibliography and '2609.01096v1' not in bibliography)
    older_exceptions={'Marzullo1990','Groth2016','MiMC2016','GraphGNSSData'}
    check('only three original methods and pinned data remain outside five-year window',
          {k for k,y in years.items() if y<2022}==older_exceptions)
    # Current selection has no borderline late-2021 publication. All non-exceptions
    # are from 2022 onward and inside the five-year window at this revision date.
    rows=re.findall(r'\$\((\d),(\d)\)\$&([^\n]+)',manuscript)
    # Each shape occurs twice: depth table then subset table.
    observed={}
    for n,d,text in rows:
        backend='depth' if (n,d) not in observed else 'subset'
        observed[n,d]=backend
        prefix='zkdepth' if backend=='depth' else 'subset'
        result=json.loads((ROOT/f'experiments/{prefix}_n{n}_d{d}_formal.json').read_text())
        values=text.split('&')
        check(f'{backend} ({n},{d}) constraints',int(values[0].replace(',',''))==result['constraints'])
        prove_index=2 if backend=='depth' else 1
        check(f'{backend} ({n},{d}) prove median',abs(float(values[prove_index])-result['prove_median_ms'])<=.0051)
        verify_index=4 if backend=='depth' else 2
        verify_text=re.match(r'[0-9.]+',values[verify_index]).group()
        check(f'{backend} ({n},{d}) verify median',abs(float(verify_text)-result['verify_median_ms'])<=.00051)
        if backend=='depth':
            check(f'depth ({n},{d}) setup seconds',abs(float(values[1])-result['setup_ms']/1000)<=.0051)
            check(f'depth ({n},{d}) prove p95',abs(float(values[3])-float(np.quantile(result['prove_ms'],.95)))<=.0051)
            verify95=float(re.match(r'[0-9.]+',values[5]).group())
            check(f'depth ({n},{d}) verify p95',abs(verify95-float(np.quantile(result['verify_ms'],.95)))<=.00051)
        check(f'{backend} ({n},{d}) 30 samples',result['repetitions']==len(result['prove_ms'])==len(result['verify_ms'])==30)
        check(f'{backend} ({n},{d}) proof size',result['proof_bytes']==164)
    check('ten circuit conditions included',len(rows)==10)
    zklp_repro=json.loads((ROOT/'experiments/zklp_same_runner.json').read_text())
    ours_repro=json.loads((ROOT/'experiments/ours_same_runner_subset_n3_d2.json').read_text())
    recent_comp=json.loads((ROOT/'experiments/recent_work_comparison.json').read_text())
    check('pinned ZKLP reproduction commit',
          zklp_repro['upstream_commit']=='e8e321524982ddd9dddea37db6fa352529db62c4')
    check('ZKLP same-runner values retained',
          zklp_repro['constraints']==19467 and abs(zklp_repro['prove_median_ms']-515.529)<1e-9 and
          abs(zklp_repro['verify_median_ms']-1.7385)<1e-9 and zklp_repro['proof_bytes']==196)
    check('our matched-runner subset values retained',
          ours_repro['constraints']==32474 and abs(ours_repro['prove_median_ms']-645.136)<1e-9 and
          abs(ours_repro['verify_median_ms']-1.5475)<1e-9 and ours_repro['proof_bytes']==164)
    check('recent-work comparison policy forbids ranking',
          recent_comp['comparison_policy']['purpose']=='Recent-work context, not a performance ranking.')
    check('recent-work numbers appear in manuscript',
          '19,467 & 515.53 & 1.739 & 196 & 140' in manuscript and
          '32,474 & 645.14 & 1.547 & 164 & 556' in manuscript)
    semantic=json.loads((ROOT/'experiments/semantic_results.json').read_text())
    counts=semantic['seed_counts']
    check('64800 semantic event observations',sum(c['inside']+c['outside'] for condition in counts.values() for c in condition['robust_depth'])==64800)
    check('12 assumption-respecting conditions contain no robust errors',all(
        c['false_accept']==c['false_reject']==0
        for key,condition in counts.items()
        if key.startswith(('calibrated_independent','calibrated_correlated')) and key.endswith(('byz_0','byz_1'))
        for c in condition['robust_depth']))
    trace=json.loads((ROOT/'experiments/trace_results.json').read_text())
    ablation=json.loads((ROOT/'experiments/miscoverage_ablation.json').read_text())
    check('six ablation rows',len(ablation['rows'])==6)
    for row in ablation['rows']:
        filename='semantic_results.json' if row['r']==0 else f"semantic_results_r{row['r']}.json"
        source=json.loads((ROOT/'experiments'/filename).read_text())
        stats=source['aggregate'][row['condition']]['robust_depth']
        check(f"ablation {row['condition']} r={row['r']} matches source",all(
            abs(row[m]-stats[m]['mean'])<1e-12 for m in ('false_accept_rate','false_reject_rate','decisive_coverage')))
    ablation_table=re.findall(r'(Calibrated|Undercovered)&([012])&([0-9.]+)&([0-9.]+)&([0-9.]+)',manuscript)
    check('six ablation rows in manuscript',len(ablation_table)==6)
    for model,r,fa,fr,coverage in ablation_table:
        prefix='calibrated_' if model=='Calibrated' else 'undercovered_'
        row=next(v for v in ablation['rows'] if v['r']==int(r) and v['condition'].startswith(prefix))
        check(f'ablation manuscript {model} r={r}',all(abs(float(text)-100*row[key])<=.0051 for text,key in
            ((fa,'false_accept_rate'),(fr,'false_reject_rate'),(coverage,'decisive_coverage'))))
    check('trace SHA256 and row count',trace['rows']==787 and
          trace['sha256']==hashlib.sha256((ROOT/'experiments/UrbanNav_TST_GT_raw.txt').read_bytes()).hexdigest())
    sys.path.insert(0, str(ROOT/'experiments'))
    from run_receiver_calibration import load_data, chronological_split, radius_order_statistic, describe
    receiver=json.loads((ROOT/'experiments/receiver_calibration.json').read_text())
    gt, sol, headers, residuals=load_data(ROOT/'experiments/graphgnss_tst2')
    cal, gap, evaluation=chronological_split(residuals)
    radius, rank=radius_order_statistic([row['score_m'] for row in cal])
    check('receiver diagnostic rederived from raw positions',receiver['calibration']==json.loads(json.dumps(describe(cal,radius))) and
          receiver['evaluation']==json.loads(json.dumps(describe(evaluation,radius))))
    check('receiver diagnostic chronological sizes',len(residuals)==157 and (len(cal),len(gap),len(evaluation))==(78,10,69))
    check('receiver diagnostic radius and rank',receiver['radius_m']==radius and receiver['calibration_rank']==rank==76)
    check('receiver raw source hashes',all(s['sha256']==hashlib.sha256((ROOT/'experiments/graphgnss_tst2'/s['filename']).read_bytes()).hexdigest() for s in receiver['sources']))
    check('receiver protocol hash',receiver['protocol_sha256']==hashlib.sha256((ROOT/'experiments/calibration_protocol.md').read_bytes()).hexdigest())
    check('receiver data limitations retained',not receiver['online_causal_evaluation'] and not receiver['multisource_calibration'] and not receiver['independent_trials'])
    check('receiver table matches raw containment',r'Reported $3\sigma$ rectangle&8/78&0/69' in manuscript and
          r'Calibrated square (0.863506~m)&76/78&2/69' in manuscript and
          [receiver[s][k] for s in ('calibration','evaluation') for k in ('receiver_3sigma_contained','calibrated_square_contained')]==[8,76,0,2])
    check('receiver radius in manuscript',abs(radius-.863506)<.00000051 and '0.863506~m' in manuscript)
    sweep_dir=ROOT/'experiments/compile_sweep_20260915T010554Z'
    sweep=json.loads((sweep_dir/'results.json').read_text())
    sweep_plan=json.loads((sweep_dir/'plan.json').read_text())
    check('compile sweep completes planned schedule',len(sweep)==len(sweep_plan['jobs'])==32 and
          all(all(row[key]==job[key] for key in ('n','d','k','backend')) for row,job in zip(sweep,sweep_plan['jobs'])))
    check('compile sweep outcomes retained',sum(r['status']=='ok' for r in sweep)==27 and
          sum(r['status']=='rss_limit' for r in sweep)==5 and
          all('constraints' not in r for r in sweep if r['status']!='ok'))
    check('compile sweep implementation hashes',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sweep_plan['sources'].items()))
    lookup={(r['backend'],r['n'],r['d'],r['k']):r for r in sweep}
    for d in (2,3):
        for n in (4,8,12,16):
            cells=[]
            for backend,k in [('depth',n-1),('subset',n-1),('subset',n-2),('subset',n//2)]:
                r=lookup[(backend,n,d,k)]
                cells.append(format(r['constraints'],',') if r['status']=='ok' else 'RL')
            check(f'compile sweep table n={n} d={d}',f'{d}&{n}&'+ '&'.join(cells) in manuscript)
    check('compile sweep logs agree with completed counts',all(
        any(line.startswith('RESULT_JSON:') and json.loads(line[12:])['constraints']==r['constraints']
            for line in (sweep_dir/r['log']).read_text().splitlines())
        for r in sweep if r['status']=='ok'))
    check('submission manuscript has no internal draft banner', 'Author-review draft' not in manuscript)
    log=(ROOT/'paper_a.log').read_text()
    check('no overfull boxes','Overfull' not in log)
    check('no oversized floating tables or figures','Float too large' not in log)
    check('no undefined references or citations','undefined' not in log.lower())
    check('JISA elsarticle 3.5 class used','Document Class: elsarticle 2026/01/09, 3.5:' in log)
    compliance=(ROOT/'venue_template_jisa/COMPLIANCE.md').read_text()
    check('JISA template provenance retained','elsarticle 3.5' in compliance and '2026-01-09' in compliance)
    check('numeric bibliography style present',(ROOT/'elsarticle-num.bst').is_file())
    check('PDF is newer than manuscript and local class',
          (ROOT/'paper_a.pdf').stat().st_mtime >= max((ROOT/f).stat().st_mtime for f in ('paper_a.tex','elsarticle.cls','references.bib')))
    paths=[ROOT/'paper_a.tex',ROOT/'references.bib']+sorted((ROOT/'experiments').glob('*formal.json'))+[
        ROOT/'experiments/semantic_results.json',ROOT/'experiments/trace_results.json',ROOT/'experiments/paired_comparison.json']
    paths+=sorted((ROOT/'prototype/zkdepth').glob('*.go'))+[ROOT/'prototype/zkdepth/go.mod',ROOT/'prototype/zkdepth/go.sum',ROOT/'prototype/zkdepth/cmd/bench/main.go']
    paths+=sorted((ROOT/'experiments').glob('*.py'))+sorted((ROOT/'prototype').glob('*.py'))
    paths+=[ROOT/'experiments/semantic_results_r1.json',ROOT/'experiments/semantic_results_r2.json',ROOT/'experiments/miscoverage_ablation.json']
    paths+=[ROOT/'experiments'/name for name in ('receiver_calibration.json','receiver_residuals.csv','calibration_protocol.md')]
    paths+=sorted((ROOT/'experiments/graphgnss_tst2').glob('*'))
    paths+=[ROOT/'evidence/gateway_validation.json',ROOT/'evidence/literature_sources.json']
    paths+=[ROOT/'evidence'/f for f in ('literature_update_20260915.md','added_reference_metadata_20260915.json','citation_validation.json')]
    paths+=[ROOT/'evidence'/f for f in ('literature_recency_20260917.md','recent_reference_metadata_20260916.json')]
    paths+=[ROOT/'evidence/comparison_table_20260917.md']
    paths+=[ROOT/'experiments'/f for f in ('zklp_same_runner.json','ours_same_runner_subset_n3_d2.json','recent_work_comparison.json','build_recent_work_comparison.py')]
    paths+=[ROOT/'audit_scientific.py']
    paths+=[ROOT/'audit_style.py']
    paths+=[ROOT/'submission_disclosure_notes.md']
    paths+=[ROOT/'evidence'/f for f in ('style_integrity_20260923.json','style_rewrite_20260923.diff','style_revision_20260923_zh.md')]
    paths+=[ROOT/'evidence'/f for f in ('check_reference_metadata.py','scientific_recheck_20260922.json','reference_metadata_recheck_20260922.json','manuscript_recheck_20260923_zh.md')]
    paths+=[ROOT/f for f in ('elsarticle.cls','elsarticle-num.bst','export_latex.py','venue_template_jisa/COMPLIANCE.md')]
    paths+=[ROOT/f for f in ('author_information_provenance.md','submission_confirmations_zh.md')]
    paths += [p for p in sweep_dir.iterdir() if p.suffix in ('.json','.log')]
    paths += [ROOT/'prototype/zkdepth/cmd/compilebench/main.go',ROOT/'figures/render_compile_sweep.py',ROOT/'figures/compile_scalability_manifest.json']
    sources=[]
    for i,path in enumerate(paths,1):
        sources.append(dict(id=f'E{i:03}',path=str(path.relative_to(ROOT)),
            sha256_at_audit=hashlib.sha256(path.read_bytes()).hexdigest(),
            agent_check='local file inspected', human_verification='pending',
            date_checked='2026-09-22'))
    (ROOT/'evidence/source_manifest.json').write_text(json.dumps(dict(
        sources=sources,note='Hashes record audit-time artifacts, not historical benchmark source hashes.'),indent=2)+'\n')
    # Claim hashes map every table row to the corresponding measured record.
    with (ROOT/'evidence/claims.csv').open('w',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['claim_id','claim_sha256','source_id','locator','human_verification'])
        for i,(n,d,row) in enumerate(rows,1):
            prefix='zkdepth' if i<=5 else 'subset'
            source=next(s for s in sources if s['path']==f'experiments/{prefix}_n{n}_d{d}_formal.json')
            writer.writerow([f'C{i:03}',hashlib.sha256(row.encode()).hexdigest(),source['id'],'constraints; prove_median_ms; verify_median_ms','pending'])
    report=dict(checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),
                submission_ready=False,scope='numeric, compilation and supplied-metadata checks only; not novelty, calibration, security, or journal approval')
    (ROOT/'evidence/artifact_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if report['passed']!=report['total']: raise SystemExit(1)

if __name__=='__main__': main()
