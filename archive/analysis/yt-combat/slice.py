import sys
p,lo,hi=sys.argv[1:];lo=int(lo,16);hi=int(hi,16);active=False
for l in open(p):
 if len(l)>10 and l[4]==':' and l[9]==' ':
  try:a=int(l[5:9],16)
  except:continue
  active=lo<=a<=hi
 if active:print(l,end='')
