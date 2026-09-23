"""Render actual compiled counts and explicit resource-censored cases."""
import csv, hashlib, json, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve()
rows=json.loads((source/'results.json').read_text())
plan=json.loads((source/'plan.json').read_text())
assert len(rows)==len(plan['jobs']), 'Sweep incomplete'
lookup={(r['backend'],r['n'],r['d'],r['k']):r for r in rows}
checks=[]
for backend,prefix in [('depth','zkdepth'),('subset','subset')]:
    for n,d in [(4,2),(4,3),(5,2)]:
        ref=json.loads((HERE.parent/f'experiments/{prefix}_n{n}_d{d}_formal.json').read_text())
        actual=lookup[(backend,n,d,n-1)]
        assert actual['status']=='ok' and actual['constraints']==ref['constraints']
        checks.append(f'{backend} n={n} d={d}: same count as prior benchmark')
styles=[('depth','Depth','#555555','D','-'),('b1','Subset: b=1','#0072B2','o','-'),
        ('b2','Subset: b=2','#D55E00','s','--'),('half','Subset: k=n/2','#009E73','^',':')]
with plt.style.context(HERE/'publication.mplstyle'),plt.rc_context({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8}):
    fig,axes=plt.subplots(1,2,figsize=(6.1,3.2),sharey=True)
    fig.subplots_adjust(left=.11,right=.98,top=.77,bottom=.25,wspace=.16)
    notes=[]
    for ax,d in zip(axes,(2,3)):
        failures=[]
        for key,label,color,marker,ls in styles:
            ns=[4,8,12,16]; vals=[]
            for n in ns:
                k=n-1 if key in ('depth','b1') else n-2 if key=='b2' else n//2
                row=lookup[('depth' if key=='depth' else 'subset',n,d,k)]
                vals.append(row.get('constraints',np.nan))
                if row['status']!='ok': failures.append(f'{label}, n={n}: {row["status"]}')
            ax.plot(ns,vals,color=color,marker=marker,ls=ls,lw=1,ms=4,label=label)
        ax.set(yscale='log',xticks=[4,8,12,16],xlabel='Number of issuers n',title=f'({"a" if d==2 else "b"}) d = {d}')
        ax.grid(axis='y',which='major',color='#E4E7EB',lw=.5)
        notes.extend(f'd={d}: {s}' for s in failures)
    axes[0].set_ylabel('R1CS constraints (log scale)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=2,frameon=False,fontsize=8)
    fig.text(.11,.11,'Missing counts: resource-limited compilations; see accompanying table.',fontsize=7)
    fig.text(.11,.055,'Full signature + geometry relation; 16-bit coordinates; b = n − k.',fontsize=7)
    for suffix in ('pdf','png','svg'): fig.savefig(HERE/f'compile_scalability.{suffix}',dpi=600,facecolor='white',bbox_inches=None)
    plt.close(fig)
fields=sorted(set().union(*(r.keys() for r in rows)))
with (HERE/'compile_scalability_data.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
manifest=dict(source=str(source.relative_to(HERE.parent)),source_sha256=hashlib.sha256((source/'results.json').read_bytes()).hexdigest(),
  checks=checks,resource_limited=notes,description='Full-circuit counts versus roster size. Missing values remain gaps, not zero or predictions.',
  transformations='No smoothing. Log10 vertical scale, raw positive counts. Lines join adjacent measured grid points only; no connection across failures.',
  physical_size_inches=[6.1,3.2],png_dpi=600,matplotlib=matplotlib.__version__)
(HERE/'compile_scalability_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'checks':checks,'failures':notes},indent=2))
