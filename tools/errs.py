"""List compiler errors on nodes whose names start with a prefix in a T3D export. Usage: py errs.py file.t3d PREFIX"""
import re, sys
t = open(sys.argv[1], encoding='utf-8', errors='replace').read()
pre = sys.argv[2]
for m in re.finditer(r'Begin Object Name="(' + pre + r'_\d+)"(.*?)\n\s*End Object', t, re.S):
    e = re.search(r'ErrorMsg="(.*)"', m.group(2))
    o = re.findall(r'PinName="([^"]+)"[^\n]*bOrphanedPin=True', m.group(2))
    if e or o: print(m.group(1), (e.group(1)[:240] if e else ''), o)
print(pre, 'nodes', len(set(re.findall(r'Name="(' + pre + r'_\d+)"', t))))
