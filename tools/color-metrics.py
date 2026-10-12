"""D65 CIELAB与CIEDE2000独立计算；用Sharma/Wu/Dalal公开34对数据验算。"""
import math, runpy, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
r=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))


def lab_from_linear(rgb):
    xyz=r['matvec'](r['rgb_xyz']('709'),rgb)
    white=(.3127/.329,1,(1-.3127-.329)/.329)
    def f(v):return v**(1/3) if v>(6/29)**3 else v/(3*(6/29)**2)+4/29
    x,y,z=[f(a/b) for a,b in zip(xyz,white)]
    return [116*y-16,500*(x-y),200*(y-z)]


def srgb_decode(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def lab_from_srgb(rgb):return lab_from_linear([srgb_decode(v) for v in rgb])


def icc_linear_transform(path):
    # 从目标ICC读取实际S15.16原色矩阵；不能把Windows标准profile近似成精确709矩阵。
    data=Path(path).read_bytes();tags={};count=struct.unpack_from('>I',data,128)[0]
    for i in range(count):
        tag=data[132+i*12:136+i*12].decode('ascii');offset,size=struct.unpack_from('>II',data,136+i*12)
        if tag in ('rXYZ','gXYZ','bXYZ'):
            assert data[offset:offset+4]==b'XYZ '
            tags[tag]=[v[0]/65536 for v in struct.iter_unpack('>i',data[offset+8:offset+size])]
    pcs=[[tags[tag][i] for tag in ('rXYZ','gXYZ','bXYZ')] for i in range(3)]
    bradford=[[.8951,.2664,-.1614],[-.7502,1.7135,.0367],[.0389,-.0685,1.0296]]
    source=r['matvec'](bradford,[.3127/.329,1,(1-.3127-.329)/.329])
    target=r['matvec'](bradford,[.9642,1,.8249])
    adaptation=r['matmul'](r['inv'](bradford),[[v*target[i]/source[i] for v in row] for i,row in enumerate(bradford)])
    return r['matmul'](r['inv'](pcs),r['matmul'](adaptation,r['rgb_xyz']('709')))


def delta_e_2000(lab1,lab2):
    L1,a1,b1=lab1;L2,a2,b2=lab2
    cbar=(math.hypot(a1,b1)+math.hypot(a2,b2))/2
    G=.5*(1-math.sqrt(cbar**7/(cbar**7+25**7)))
    ap1=(1+G)*a1;ap2=(1+G)*a2
    C1=math.hypot(ap1,b1);C2=math.hypot(ap2,b2)
    h1=math.atan2(b1,ap1)%(2*math.pi) if C1 else 0
    h2=math.atan2(b2,ap2)%(2*math.pi) if C2 else 0
    dh=h2-h1
    if dh>math.pi:dh-=2*math.pi
    elif dh<-math.pi:dh+=2*math.pi
    if C1*C2==0:dh=0
    dH=2*math.sqrt(C1*C2)*math.sin(dh/2)
    Lbar=(L1+L2)/2;Cbar=(C1+C2)/2;hbar=(h1+h2)/2
    if abs(h1-h2)>math.pi:hbar-=math.pi
    if hbar<0:hbar+=2*math.pi
    if C1*C2==0:hbar=h1+h2
    T=1-.17*math.cos(hbar-math.pi/6)+.24*math.cos(2*hbar)+.32*math.cos(3*hbar+math.pi/30)-.20*math.cos(4*hbar-math.radians(63))
    SL=1+.015*(Lbar-50)**2/math.sqrt(20+(Lbar-50)**2)
    SC=1+.045*Cbar;SH=1+.015*Cbar*T
    rotation=-2*math.sqrt(Cbar**7/(Cbar**7+25**7))*math.sin(math.radians(60)*math.exp(-((math.degrees(hbar)-275)/25)**2))
    dL=(L2-L1)/SL;dC=(C2-C1)/SC;dH/=SH
    return math.sqrt(max(0,dL*dL+dC*dC+dH*dH+rotation*dC*dH))


def statistics(values):
    values=sorted(values)
    def percentile(p):
        pos=p*(len(values)-1);i=int(pos);k=pos-i
        return values[i]*(1-k)+values[min(i+1,len(values)-1)]*k
    return dict(count=len(values),maximum=values[-1],mean=sum(values)/len(values),
        p50=percentile(.5),p95=percentile(.95),p99=percentile(.99),p999=percentile(.999))


def self_test(path):
    rows=[list(map(float,line.split())) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows)==34
    errors=[abs(delta_e_2000(v[:3],v[3:6])-v[6]) for v in rows]
    assert max(errors)<.00005,(max(errors),[(i,e) for i,e in enumerate(errors) if e>=.00005])
    for row in rows:assert abs(delta_e_2000(row[:3],row[3:6])-delta_e_2000(row[3:6],row[:3]))<1e-10
    return dict(pairs=len(rows),max_error_vs_four_decimal_reference=max(errors),symmetry_passed=True)


if __name__=='__main__':
    print(self_test(ROOT/'tmp/modernization/gamut-general-20261012/ciede2000testdata.txt'))
