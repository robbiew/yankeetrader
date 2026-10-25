exec(open('analysis/yt-combat/make_fixtures.py').read().split("for kind in")[0].replace("ROOT=Path(__file__).resolve().parent","ROOT=Path('analysis/yt-combat').resolve()"))
for name in ('mines','shields','distance','ten','xannor','nocloak'):
 kind='surrender' if name in ('ten','xannor','nocloak') else 'plasma'
 src=ROOT/'experiments'/('fixture-'+kind);d=ROOT/'experiments'/('fixture-'+name);shutil.copytree(src,d)
 b=bytearray((d/'YTDATA.DAT').read_bytes())
 if name=='mines':
  put(b,152,81,0);put(b,152,85,0);put(b,152,129,10000)
 if name=='shields':
  put(b,152,81,0);put(b,152,85,0);put(b,3,57,101);put(b,3,61,0);put(b,3,53,1000000)
 if name=='distance':
  put(b,152,81,0);put(b,152,85,0);put(b,153,81,1000000);put(b,153,85,3)
 if name in ('ten','xannor'):put(b,151,81,1000)
 if name=='xannor':put(b,151,85,-1)
 if name=='nocloak':put(b,2,125,0)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
