"""Rebuild the risk-coverage plot.

Figures 1--3 use model-assisted SVG/PDF artwork rebuilt separately by
vectorize_model_figures.py. Original supplied PNGs are retained as references.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

p = Path(__file__).resolve().parent
rcParams['font.family'] = 'DejaVu Sans'
rcParams['font.size'] = 10

# M3 risk-coverage verified operating points (aggregate seed_counts from pinned archive)
D=[('All-source',12.375,100),('Fixed margin',75.6667,0),('Robust set',85.0417,0),('Median point',100,3.375),('Majority center',100,3.5)]
positions={'All-source':(21,93),'Fixed margin':(55,13),'Robust set':(80,23),'Median point':(79,38),'Majority center':(85,49)}
fig,ax=plt.subplots(figsize=(8.1,4.9));
for name,coverage,risk in D:
 ax.plot(coverage,risk,'o',ms=7)
 ax.annotate(name,xy=(coverage,risk),xytext=positions[name],textcoords='data',fontsize=9,
             arrowprops={'arrowstyle':'-','color':'0.45','lw':.8})
ax.set_xlim(0,112);ax.set_ylim(-5,105);ax.set_xlabel('Decisive coverage (%)');ax.set_ylabel('Wrong among decisive decisions (%)');ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(p/'risk_coverage.png',dpi=600);fig.savefig(p/'risk_coverage.svg');plt.close(fig)
print('Rebuilt risk_coverage; preserved vector Figures 1--3.')