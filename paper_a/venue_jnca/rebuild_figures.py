from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib import rcParams
p=Path(__file__).resolve().parent
rcParams['font.family']='DejaVu Sans';rcParams['font.size']=10
INK='#24354b'; BLUE='#2a618a';GREEN='#287d72';LIGHT='#f4f7fa';ORANGE='#ba6136'
def box(ax,x,y,w,h,title,content='',stroke=BLUE,face=LIGHT,fs=9):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.026',linewidth=1.3,edgecolor=stroke,facecolor=face))
 ax.text(x+w/2,y+h-.10,title,fontsize=10.4,weight='bold',ha='center',va='center',color=INK)
 if content: ax.text(x+w/2,y+h/2-.04,content,ha='center',va='center',fontsize=fs,linespacing=1.45,color=INK)
def arrow(ax,x,y,xx,yy,color=BLUE):ax.add_patch(FancyArrowPatch((x,y),(xx,yy),arrowstyle='-|>',mutation_scale=14,linewidth=1.6,color=color))
# Fig 1 architecture
fig,ax=plt.subplots(figsize=(11.4,5.8));ax.set_xlim(0,12);ax.set_ylim(0,6);ax.axis('off')
box(ax,.30,1.0,2.35,3.9,'Evidence issuers',"RSU / beacon / provider\n\nSigned boxes $U_i$\nEdDSA/MiMC signatures\n\nFixed authenticated roster",fs=11)
box(ax,3.6,1.0,4.55,3.9,'Vehicle / prover',"Private witness: $U_1,\\ldots,U_n$\n\n1. Threshold support: $\\mathcal{F}_k$\n2. Four-valued classification\n3. Groth16 proof generation\n\nPublic: report, policy, decision",fs=11,stroke=GREEN)
box(ax,9.0,1.0,2.72,3.9,'Verification gateway',"Trusted task + roster\nCheck nonce and expiry\nReconstruct public inputs\nVerify proof\nConsume valid nonce\n\nValid: accept\nOthers: do not accept",fs=10.3)
box(ax,3.58,5.16,4.6,.64,'Public task context',"policy $P$   |   $k=n-f-r$   |   roster   |   report",fs=10)
arrow(ax,2.65,2.95,3.6,2.95);ax.text(3.11,3.28,'boxes +\nsignatures',ha='center',fontsize=9)
arrow(ax,8.16,2.95,9.0,2.95);ax.text(8.59,3.23,'proof +\ndecision',ha='center',fontsize=9)
arrow(ax,9.2,4.9,8.17,4.9);ax.text(8.55,5.04,'nonce + expiry',ha='center',fontsize=8.2)
ax.plot([5.9,5.9],[5.15,4.9],color=BLUE,lw=1.3)
fig.tight_layout(pad=.3);fig.savefig(p/'system_architecture.png',dpi=600);fig.savefig(p/'system_architecture.svg');plt.close(fig)
# Fig 2 explicit interval counterexample with axis lines
fig,axs=plt.subplots(3,1,figsize=(10.8,5.3),sharex=True)
for ax in axs:ax.set_xlim(-4.5,8.5);ax.set_ylim(0,1);ax.set_yticks([]);ax.spines[['top','left','right']].set_visible(False);ax.axvspan(0,8,color='#def2ef',alpha=.7);ax.axvline(-1,ls='--',color='black',lw=1.2);ax.set_xticks(range(-4,9,2))
# U1 U2 U3 and support
segments=[[(-4,4,'$U_1$'),(-2,6,'$U_2$'),(2,4,'$U_3$')],[(-2,4,'$\\mathcal{F}_2$')],[(2,4,'$U_1\\cap U_2\\cap U_3$')]]
for ax,slist in zip(axs,segments):
 for j,(lo,hi,label) in enumerate(slist):
  y=.72-j*.22;ax.plot([lo,hi],[y,y],color=[BLUE,GREEN,ORANGE][j%3],lw=6,solid_capstyle='butt');ax.plot([lo,hi],[y,y],'|',color=INK,ms=13);ax.text(hi+.18,y,label,color=INK,fontsize=11,va='center')
axs[0].set_ylabel('Signed evidence',rotation=0,labelpad=73,va='center')
axs[1].set_ylabel('Threshold support',rotation=0,labelpad=73,va='center')
axs[2].set_ylabel('All-source overlap',rotation=0,labelpad=73,va='center')
axs[0].text(-4.35,.05,'$z^*=-1$: true state outside $P$',fontsize=9)
axs[1].text(-4.35,.05,'$\\mathcal{F}_2=[-2,4]$: Ambiguous',fontsize=9)
axs[2].text(-4.35,.05,'$[2,4]\\subseteq P$: false acceptance if used alone',fontsize=9)
axs[2].set_xlabel('Integer coordinate (policy $P=[0,8]$, shaded area)')
fig.subplots_adjust(left=.19,right=.92,hspace=.52,bottom=.12,top=.96)
fig.savefig(p/'decision_counterexample.png',dpi=600);fig.savefig(p/'decision_counterexample.svg');plt.close(fig)
# Fig3 sequence
fig,ax=plt.subplots(figsize=(10.8,6));ax.set_xlim(0,12);ax.set_ylim(0,8);ax.axis('off')
cols=[2,6,10.2];titles=['Vehicle / prover','Evidence issuers','Gateway'];
for x,t in zip(cols,titles):
 ax.text(x,7.68,t,ha='center',va='center',color=INK,weight='bold',fontsize=11);ax.plot([x,x],[.85,7.36],ls='--',lw=1.2,color='#899aaa')
def msg(y,start,end,title):
 arrow(ax,cols[start],y,cols[end],y);ax.text((cols[start]+cols[end])/2,y+.11,title,ha='center',va='bottom',fontsize=9.5,color=INK,bbox={'facecolor':'white','edgecolor':'none','pad':1.5})
msg(6.90,0,2,'1. Request challenge')
msg(6.23,2,0,'2. Nonce + expiry')
msg(5.56,0,1,'3. Task / report context $c$')
msg(4.89,1,0,'4. Signed uncertainty boxes')
box(ax,.75,3.96,2.53,.52,'Compute decision + ZK proof',stroke=GREEN,fs=8)
msg(3.39,0,2,'5. Report + proof + decision')
box(ax,8.30,2.29,3.74,.77,'Check expiry + public inputs','Groth16 verification',fs=10)
box(ax,8.30,1.21,3.74,.77,'Atomic nonce consumption','Only after a verified Valid decision',fs=9,stroke=GREEN)
ax.text(6,.55,'Missing signature: abort  •  failed proof: retry until expiry  •  consumed nonce: reject replay',ha='center',fontsize=9,color=INK)
fig.subplots_adjust(left=.03,right=.98,bottom=.04,top=.97)
fig.savefig(p/'protocol_sequence.png',dpi=600);fig.savefig(p/'protocol_sequence.svg');plt.close(fig)
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
print('created accurate publication figures')