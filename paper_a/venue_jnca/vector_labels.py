"""Restore exact scientific labels after tracing model-generated artwork.

All additions are SVG text, lines, circles and rectangles. No raster images.
Coordinates are in the model's 1672 x 941 canvas. Originals are retained.
"""
import xml.etree.ElementTree as ET
from html import escape
import re

NS='http://www.w3.org/2000/svg'
BLUE='#07528d'; INK='#09254a'; PALE='#e1f2fc'; TEAL='#d4f2f2'

def correct_labels(path, name):
    root=ET.parse(path).getroot()
    parts=[]
    def rect(x,y,w,h,c='white',stroke=None):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"'+(f' stroke="{stroke}" stroke-width="1.5"' if stroke else '')+'/>')
    def typeset(s):
        s=escape(s).replace('Fₖ','F_k').replace('Uᵢ','U_i')
        return re.sub(r'([FU])_([ki])', r'\1<tspan baseline-shift="sub" font-size="70%">\2</tspan>', s)
    def text(x,y,lines,size=26,bold=False,anchor='start',color=INK):
        if isinstance(lines,str): lines=[lines]
        for i,line in enumerate(lines):
            parts.append(f'<text x="{x}" y="{y+i*size*1.22}" font-family="Times New Roman" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{typeset(line)}</text>')
    def label(x,y,w,h,lines,size=26,bold=False,face='white',align='start'):
        rect(x,y,w,h,face)
        text(x+(w/2 if align=='middle' else 3),y+size+3,lines,size,bold,align)
    def line(x,y,xx,yy,color=BLUE,width=3,dash=''):
        parts.append(f'<path d="M{x},{y} L{xx},{yy}" fill="none" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    if name=='system_architecture':
        label(458,35,988,111,'Public task context',40,True,PALE,'middle')
        text(950,132,'policy P  |  k = n − f − r  |  roster  |  report  |  nonce  |  expiry',25,anchor='middle')
        label(152,278,277,88,['Evidence issuers','RSU / beacon / provider'],25,True,PALE)
        label(765,268,300,92,'Vehicle / prover',32,True,PALE)
        text(768,345,'On-board computation',25)
        label(1350,278,288,86,'Verification gateway',27,True,PALE)
        text(1353,348,'Trusted validator',25)
        label(164,405,256,85,['Signed uncertainty','boxes Uᵢ'],27)
        label(164,535,256,84,['EdDSA / MiMC','signatures'],27)
        label(164,665,256,43,'Authenticated roster',25)
        label(712,387,340,65,['Private witness: signed','boxes + signatures'],24,False,TEAL)
        label(771,480,285,75,['Construct threshold-','supported feasible set Fₖ'],23)
        label(771,568,285,68,['Compute four-valued','decision'],25)
        label(771,664,285,44,'Generate Groth16 proof',23)
        label(690,738,370,56,['Public outputs:','report, decision, proof'],23,False,PALE)
        for y,s in [(395,'Trusted task snapshot'),(462,'Check nonce and expiry'),(528,'Reconstruct public inputs'),(594,'Verify proof'),(661,'Consume verified nonce')]:
            label(1355,y,280,44,s,23)
        label(1350,728,282,78,['Valid → accept report;','otherwise reject / hold'],23,False,TEAL)
        label(1085,299,144,30,'nonce + expiry',18,False,'white','middle')
        label(447,456,140,66,['signed boxes +','signatures'],20,False,'white','middle')
        label(1080,541,148,66,['report +','decision + proof'],20,False,'white','middle')
        label(642,845,529,64,['Threshold support verifies semantic compliance','without revealing the underlying boxes.'],23,False,'#f7faff','middle')
    elif name=='decision_counterexample':
        label(380,25,1057,65,['Example parameters','Ω = [−4, 8] ∩ ℤ,  P = [0, 8] ∩ ℤ,  (n, f, r, k) = (3, 1, 0, 2)'],25,False,PALE)
        # Use exact common coordinates; do not inherit model axis drift.
        for top,axis,segs in [(133,377,[(-4,4,223,'U₁ = [−4, 4]','#0860ad'),(-2,6,285,'U₂ = [−2, 6]','#008d91'),(2,4,342,'U₃ = [2, 4]','#c82b32')]),(463,625,[(-2,4,572,'F₂ = [−2, 4]','#0860ad')]),(707,848,[(2,4,806,'U₁ ∩ U₂ ∩ U₃ = [2, 4]','#586b80')])]:
            rect(460,top,767,axis-top+52)
            def xx(v): return 480+(v+4)*56.6666667
            rect(xx(0),top,xx(8)-xx(0),axis-top,PALE)
            line(xx(-1),top+43,xx(-1),axis,INK,2.5,'8 7')
            text(xx(-1),top+30,'z* = −1',25,anchor='middle')
            text(xx(4),top+30,'P = [0, 8]',28,anchor='middle',color=BLUE)
            line(480,axis,1218,axis,INK,2)
            for v in range(-4,9,2):
                line(xx(v),axis,xx(v),axis+12,INK,2)
                text(xx(v),axis+43,str(v).replace('-','−'),27,anchor='middle')
            for lo,hi,y,s,c in segs:
                line(xx(lo),y,xx(hi),y,c,6)
                for v in (lo,hi): parts.append(f'<circle cx="{xx(v)}" cy="{y}" r="10" fill="{c}"/>')
                text(xx(hi)+22,y+9,s,24)
        label(122,128,305,49,'Signed evidence',31,True)
        for y,s,c in [(207,'U₁ = [−4, 4]   Honest',PALE),(278,'U₂ = [−2, 6]   Honest',PALE),(349,'U₃ = [2, 4]   Byzantine','#ffeded')]: label(128,y,280,51,s,23,False,c)
        label(1270,232,355,144,['Both honest intervals cover','the true state z* = −1;','the Byzantine interval','excludes it.'],24,False,PALE)
        label(1310,151,303,45,'Key observation',26,True,PALE)
        label(122,466,310,48,'Threshold support',30,True)
        label(146,555,285,91,['F₂ = [−2, 4]','supported by ≥ 2 issuers'],24,False,PALE)
        label(1321,473,316,67,['Supported by at least','k = 2 issuers.'],24,False,PALE)
        label(1302,570,333,84,['F₂ intersects inside and','outside P → Ambiguous.'],23,False,'#fff5d5')
        label(122,709,315,48,'All-source overlap',30,True)
        label(146,800,284,91,['U₁ ∩ U₂ ∩ U₃ = [2, 4]','intersection of all sources'],22,False,PALE)
        label(1343,732,292,153,['Entirely inside P;','would falsely accept','if using all-source','intersection alone.'],24,False,'#ffeded')
    elif name=='protocol_sequence':
        for x,w,title,subtitle in [(139,241,'Administrator','Configure task and policy'),(550,278,'Verification gateway','Trusted validator'),(1038,232,'Vehicle / prover','On-board computation'),(1450,200,'Evidence issuers','RSU / beacon / provider')]:
            label(x,26,w,66,title,24,True,PALE)
            text(x+3,79,subtitle,19)
        label(201,121,318,86,['Configure task','Policy P, threshold k,','verifying key, ordered roster'],22,False,PALE)
        label(683,167,285,57,['Issue challenge','Nonce ν, expiry e'],23,False,TEAL)
        label(1104,193,403,53,['Request evidence','Signed boxes for report R'],23,False,PALE)
        label(1142,274,375,33,'c = H(ver, task, ν, e, H(R)) mod q',20,False,TEAL)
        label(1124,333,332,58,['Return signed boxes','Signed boxes Uᵢ and signatures'],22,False,PALE)
        label(1100,413,358,42,'Compute decision and proof',23,True,PALE)
        label(1163,450,291,98,['Compute decision δ from','threshold-supported set Fₖ','','Generate Groth16 proof π'],20,False,PALE)
        label(709,468,272,56,['Submit report','Report R, decision δ, proof π'],21,False,PALE)
        label(660,548,326,33,'Verify and process',25,True,PALE)
        for y,s in [(587,'Check nonce exists and is unexpired'),(628,'Reconstruct public inputs'),(668,'Verify proof and decision'),(708,'Accept report only if δ = Valid'),(748,'Consume nonce after verified proof')]:
            label(692,y,292,30,s,16)
        label(151,808,183,40,'Failure case',26,True,'#fff4f4')
        label(385,807,1230,42,'Unknown / expired nonce, substituted context, invalid proof, or mismatched decision → reject or abort',21,False,'#fff4f4')
        label(1097,879,548,45,['A failed proof does not consume the challenge.','A verified submission atomically consumes the nonce.'],17,False,PALE)
    # Reset number badges as precise circles and native glyphs.
    badges={'system_architecture':[(654,504,'1'),(654,591,'2'),(654,680,'3')], 'decision_counterexample':[(65,155,'1'),(65,495,'2'),(65,743,'3')], 'protocol_sequence':[(165,143,'1'),(635,185,'2'),(1065,210,'3'),(1087,352,'4'),(1060,428,'5'),(666,486,'6'),(627,563,'7')]}
    for x,y,n in badges[name]:
        radius=32 if name=='decision_counterexample' else 22
        parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{BLUE}"/>')
        text(x,y+10,n,31,True,'middle','white')
    group=ET.fromstring('<g xmlns="'+NS+'">'+''.join(parts)+'</g>')
    root.append(group)
    ET.register_namespace('',NS)
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
