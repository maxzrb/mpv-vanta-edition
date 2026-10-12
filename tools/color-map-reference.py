"""独立 float64 连续色彩参考：PQ、IPT、默认 perceptual 与 spline；不调用播放器。"""
import math
from functools import lru_cache

M1=2610/16384;M2=2523/32;C1=3424/4096;C2=2413/128;C3=2392/128


def clamp(x,lo=0,hi=1):return min(max(x,lo),hi)
def mix(a,b,k):return a+(b-a)*k
def smooth(a,b,x):
    k=clamp((x-a)/(b-a));return k*k*(3-2*k)
def pq(x):
    v=max(x,0)**M1;return ((C1+C2*v)/(1+C3*v))**M2
def unpq(x):
    v=max(x,0)**(1/M2);return (max(v-C1,0)/(C2-C3*v))**(1/M1)
def matvec(m,v):return [sum(a*b for a,b in zip(row,v)) for row in m]
def matmul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def inv(m):
    a=[list(row)+[int(i==j) for j in range(3)] for i,row in enumerate(m)]
    for i in range(3):
        pivot=max(range(i,3),key=lambda j:abs(a[j][i]));a[i],a[pivot]=a[pivot],a[i]
        scale=a[i][i];a[i]=[x/scale for x in a[i]]
        for j in range(3):
            if i!=j:
                scale=a[j][i];a[j]=[x-scale*y for x,y in zip(a[j],a[i])]
    return [r[3:] for r in a]


def rgb_xyz(gamut):
    vertices={'709':[(.64,.33),(.30,.60),(.15,.06)],'2020':[(.708,.292),(.170,.797),(.131,.046)]}[gamut]
    m=[[x/y for x,y in vertices],[1,1,1],[(1-x-y)/y for x,y in vertices]]
    white=[.3127/.3290,1,(1-.3127-.3290)/.3290]
    scale=matvec(inv(m),white)
    return [[v*scale[j] for j,v in enumerate(row)] for row in m]


IPT=[[.4,.4,.2],[4.455,-4.851,.396],[.8056,.3572,-1.1628]]
IPT_INV=[[1,.0975689,.205226],[1,-.113876,.133217],[1,.0326151,-.676887]]
HPE=[[.40024,.70760,-.08081],[-.22630,1.16532,.04570],[0,0,.91822]]
CROSS=[[.92,.04,.04],[.04,.92,.04],[.04,.04,.92]]


class Gamut:
    def __init__(self,name,minimum,maximum,cpu_approximation=False):
        self.forward=matmul(matmul(CROSS,HPE),rgb_xyz(name));self.backward=inv(self.forward)
        self.minimum=minimum;self.maximum=maximum
        self.imin=pq(minimum);self.imax=pq(maximum)
        self.cpu_approximation=cpu_approximation
    def rgb_ipt(self,rgb):return matvec(IPT,[pq(v) for v in matvec(self.forward,rgb)])
    def ipt_rgb(self,ipt):
        return matvec(self.backward,[self.decode(v) for v in matvec(IPT_INV,ipt)])
    def decode(self,v):
        if not self.cpu_approximation:return unpq(v)
        # CPU表有1024个有效节点，另加一个边界保护节点。
        x=clamp(v)*1023;i=int(x);k=x-i
        return mix(unpq(i/1023),unpq(min(i+1,1023)/1023),k)
    @property
    def min_rgb(self):return self.decode(self.imin)-1e-6
    @property
    def max_rgb(self):return self.decode(self.imax)+1e-6
    def contains(self,i,c,h):
        ipt=[i,c*math.cos(h),c*math.sin(h)];cones=matvec(IPT_INV,ipt)
        if min(cones)<self.imin or max(cones)>self.imax:return False
        rgb=self.ipt_rgb(ipt)
        return min(rgb)>=self.min_rgb and max(rgb)<=self.max_rgb
    def boundary(self,i,h):
        if i<=self.imin or i>=self.imax:return 0
        lo,hi=0,.5
        while hi-lo>max(i*5e-5,1e-9):
            c=(lo+hi)/2
            if self.contains(i,c,h):lo=c
            else:hi=c
        return (lo+hi)/2
    @lru_cache(maxsize=2048)
    def peak(self,h):
        # 黄金分割独立求给定色相的最大可表达色度。
        lo,hi=self.imin,self.imax;phi=(math.sqrt(5)-1)/2
        a=hi-phi*(hi-lo);b=lo+phi*(hi-lo)
        ac=self.boundary(a,h);bc=self.boundary(b,h)
        while hi-lo>5e-5:
            if ac>bc:
                hi,b,bc=b,a,ac;a=hi-phi*(hi-lo);ac=self.boundary(a,h)
            else:
                lo,a,ac=a,b,bc;b=lo+phi*(hi-lo);bc=self.boundary(b,h)
        return (a,ac) if ac>bc else (b,bc)


def perceptual_ipt(ipt,src,dst):
    i,p,t=ipt;c=math.hypot(p,t);h=math.atan2(t,p)
    si,sc=src.peak(h);di,dc=dst.peak(h)
    mapped=dst.rgb_ipt(src.ipt_rgb(ipt))
    k=smooth(.3,1,c/max(sc,dc))* .8
    ipt=[mix(a,b,k) for a,b in zip(ipt,mapped)]
    speak=dst.ipt_rgb([si,sc*math.cos(h),sc*math.sin(h)])
    result=dst.ipt_rgb(ipt);mx=max(result);mn=min(result)
    sat=1-max(mn,0)/max(mx,1e-6);ext=max(max(speak),mx)
    def soft(value):
        peak=ext/dst.max_rgb;x=min(value/dst.max_rgb,peak);j=.7
        if x<=j or peak<=1:return value
        a=-j*j*(peak-1)/(j*j-2*j+peak)
        b=(j*j-2*j*peak+peak)/max(1e-6,peak-1)
        scale=(b+j)**2/(b-a)
        return scale*(x+a)/(x+b)*dst.max_rgb
    result=[clamp(mix(v,soft(v),sat),dst.min_rgb,dst.max_rgb) for v in result]
    return dst.rgb_ipt(result)


def perceptual(rgb,minimum=0,maximum=203/10000,cpu_approximation=False):
    src=Gamut('2020',minimum,maximum,cpu_approximation);dst=Gamut('709',minimum,maximum,cpu_approximation)
    ipt=perceptual_ipt(src.rgb_ipt(rgb),src,dst)
    # 最终 GPU 的 IPT 解码使用标准连续 PQ，即使 CPU 生成表采用近似。
    final=Gamut('709',minimum,maximum)
    return final.ipt_rgb(ipt)


class PerceptualTable:
    def __init__(self,maximum,size=(48,32,256)):
        self.size=size;self.src=Gamut('2020',0,maximum,True);self.dst=Gamut('709',0,maximum,True)
        self.final=Gamut('709',0,maximum)
    @lru_cache(maxsize=4096)
    def vertex(self,i,c,h):
        I=i/(self.size[0]-1)*self.src.imax;C=c/(self.size[1]-1)*.5
        H=(h/(self.size[2]-1)-.5)*2*math.pi
        ipt=perceptual_ipt([I,C*math.cos(H),C*math.sin(H)],self.src,self.dst)
        # 生成表的P/T偏置32767，GPU采样后减去32768；独立保留该一个码值差。
        values=[round(ipt[0]*65535),round(ipt[1]*65535+32767),round(ipt[2]*65535+32767)]
        return [clamp(v,0,65535)/65535 for v in values]
    def sample(self,rgb):
        ipt=self.src.rgb_ipt(rgb);I,P,T=ipt
        pos=[clamp(I/self.src.imax),clamp(2*math.hypot(P,T)),clamp(math.atan2(T,P)/(2*math.pi)+.5)]
        indices=[v*(n-1) for v,n in zip(pos,self.size)];low=[int(v) for v in indices];frac=[v-i for v,i in zip(indices,low)]
        result=[0,0,0]
        for bits in range(8):
            ix=[min(i+((bits>>j)&1),self.size[j]-1) for j,i in enumerate(low)]
            weight=math.prod(frac[j] if (bits>>j)&1 else 1-frac[j] for j in range(3))
            value=self.vertex(*ix)
            result=[a+weight*b for a,b in zip(result,value)]
        return self.final.ipt_rgb([result[0],result[1]-32768/65535,result[2]-32768/65535])


def spline(value,source_min,source_max,source_avg,target_min,target_max):
    # PQ 域的 ST2094 膝点及双曲样条连续解；不经播放器查找表。
    rel=clamp((source_avg-source_min)/(source_max-source_min),.1,.8) if source_avg else .4
    x=mix(source_min,source_max,rel);adapted=mix(target_min,target_max,rel)
    tuning=1-smooth(.8,.4,rel)*smooth(.1,.4,rel)
    strength=mix(.4,1,tuning)
    strength=mix(1,strength,smooth(target_min,mix(target_min,target_max,.1),x))
    y=clamp(mix(x,adapted,strength),mix(target_min,target_max,.1),mix(target_min,target_max,.8))
    slope=(y-target_min)/(x-source_min)
    ratio=clamp(1.5*(source_max/target_max-1),.2,1.2)
    slope=slope**(.5*ratio)
    lo=source_min-x;hi=source_max-x;outlo=target_min-y;outhi=target_max-y
    pk=(slope*lo-outlo)/(outlo*lo);qk=(slope*hi-outhi)/(outhi*hi)
    v=clamp(value,source_min,source_max)-x
    return slope*v/(1+(qk if v>0 else pk)*v)+y


def dynamic_target(source_peak,source_avg,target_peak):
    p=pq(target_peak/10000);s=pq(source_peak/10000);f=pq(source_avg/10000)
    t=clamp(.5*(p+f-.09)+math.hypot(.5*(p-f+.09),.04),p,s)
    return unpq(t)*10000,target_peak/(unpq(t)*10000)
