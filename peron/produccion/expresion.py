"""Hace la entonación más expresiva: lleva el tono medio a TARGET Hz y multiplica sus variaciones por GAIN."""
import sys, parselmouth, numpy as np
from parselmouth.praat import call
inp,out,target,gain=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
s=parselmouth.Sound(inp)
p=s.to_pitch(pitch_floor=60,pitch_ceiling=400).selected_array['frequency']; med=np.median(p[p>0])
m=call(s,"To Manipulation",0.01,60,400)
pt=call(m,"Extract pitch tier")
call(pt,"Formula",f"{target}*exp({gain}*ln(self/{med}))")
call([pt,m],"Replace pitch tier")
r=call(m,"Get resynthesis (overlap-add)")
r.save(out,"WAV")
