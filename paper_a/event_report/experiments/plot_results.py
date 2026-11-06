#!/usr/bin/env python3
"""Render figures from the recorded local prototype experiment."""
from pathlib import Path
import csv
import io
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

root = Path(__file__).resolve().parent.parent
def read_samples(name):
    lines = (root / 'experiments' / name).read_text().splitlines()
    header = lines.index('sample,prove_ns,verify_ns,proof_bytes,public_witness_bytes')
    rows = []
    for line in lines[header+1:]:
        fields = line.split(',')
        if len(fields) == 5 and fields[0].isdigit():
            rows.append([int(x) for x in fields])
    if len(rows) != 30:
        raise ValueError(f'expected 30 measured samples in {name}, got {len(rows)}')
    return rows
base=read_samples('benchmark.log')
region=read_samples('region_benchmark.log')
accountability=read_samples('accountability_benchmark.log')
active=read_samples('revocation_benchmark.log')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42})
fig, axes = plt.subplots(1,2,figsize=(7.1,2.8))
for ax, col, title in ((axes[0],1,'Proof generation'), (axes[1],2,'Proof verification')):
    for rows, label, color, marker in ((base,'Rectangle','#1f5d87','o'),(region,'Region','#b35920','x'),(accountability,'Accountability','#427849','^'),(active,'Active credential','#80548b','+')):
        values = [r[col]/1e6 for r in rows]
        ax.scatter(range(1,len(values)+1),values,s=15,color=color,alpha=.76,marker=marker,label=label)
        ax.axhline(statistics.median(values),color=color,linestyle='--',linewidth=.85)
    ax.set(title=title,xlabel='Measured run',ylabel='Time (ms)',xlim=(0,31))
    ax.grid(axis='y',color='0.88',linewidth=.6)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, frameon=False, loc='lower center', ncol=4, fontsize=8)
fig.tight_layout(rect=(0, .11, 1, 1))
fig.savefig(root/'benchmark.pdf',bbox_inches='tight')

fig, ax=plt.subplots(figsize=(7.1,3.45))
ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
def box(x,y,w,h,title,sub,colour):
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08,rounding_size=0.1',linewidth=1,edgecolor=colour,facecolor='white')
    ax.add_patch(p); ax.text(x+w/2,y+h*.67,title,ha='center',va='center',fontsize=9,fontweight='bold',color=colour)
    ax.text(x+w/2,y+h*.28,sub,ha='center',va='center',fontsize=7.1,color='#333333')
def arrow(a,b,label,offset=(0,0),color='#455a64'):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=10,linewidth=1,color=color))
    ax.text((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1],label,fontsize=7,ha='center',va='center',color='#222222',bbox=dict(facecolor='white',edgecolor='none',pad=.8))
box(3.5,4,3,0.75,'Registration authority','participant credential and issuer certificate','#355c7d')
box(.25,1.8,2.25,.9,'Event issuer','observes; signs event receipt','#8d5524')
box(3.85,1.8,2.3,.9,'Participant','encrypts report; creates proof','#146557')
box(7.45,1.8,2.3,.9,'Gateway','verifies; checks task tag','#6c477d')
box(7.45,.1,2.3,.75,'Report recipient','authenticates and decrypts','#426d7f')
arrow((4.2,4),(1.3,2.72),'issuer certificate',(-.4,.13))
arrow((5,4),(5,2.72),'credential',(.5,0))
arrow((3.85,2.5),(2.52,2.5),'context, holder',(0,.18))
arrow((2.52,1.98),(3.85,1.98),'signed event',(0,-.18))
arrow((7.45,2.5),(6.18,2.5),'challenge',(0,.18))
arrow((6.18,1.98),(7.45,1.98),'proof, tag, envelope',(0,-.18))
arrow((8.6,1.8),(8.6,.86),'verified envelope',(.75,0))
fig.tight_layout(pad=.2);fig.savefig(root/'architecture.pdf',bbox_inches='tight')
