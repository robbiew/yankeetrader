from pathlib import Path
import io,struct,json,hashlib,sys
sys.path.insert(0,'/private/tmp/ytcalc-read-deps')
import xlrd,olefile,msoffcrypto
from xlrd.formula import decompile_formula,FMLA_TYPE_CELL,colname
source=Path('/Users/robbie/Downloads/ytcalc.xls');raw=source.read_bytes()
f=msoffcrypto.OfficeFile(io.BytesIO(raw));f.load_key(password='VelvetSweatshop');o=io.BytesIO();f.decrypt(o);payload=o.getvalue()
b=xlrd.open_workbook(file_contents=payload,formatting_info=True,on_demand=True)
ole=olefile.OleFileIO(io.BytesIO(payload));stream=ole.openstream('Workbook').read()
formulas={};pos=0
while pos+4<=len(stream):
 op,n=struct.unpack_from('<HH',stream,pos);d=stream[pos+4:pos+4+n]
 if op==0x06 and n>=22:
  row,col=struct.unpack_from('<HH',d);ln=struct.unpack_from('<H',d,20)[0]
  try:formula=decompile_formula(b,d[22:],ln,FMLA_TYPE_CELL,browx=row,bcolx=col)
  except Exception as e:formula='ERROR '+repr(e)
  formulas[(row,col)]=formula
 pos+=4+n
sheets=[]
for s in b.sheets():
 cells=[]
 for r in range(s.nrows):
  for c in range(s.ncols):
   v=s.cell_value(r,c);f=formulas.get((r,c))
   if v!='' or f:
    a=f'{colname(c)}{r+1}';cells.append({'cell':a,'value':v,**({'formula':f} if f else {})})
 sheets.append({'name':s.name,'rows':s.nrows,'columns':s.ncols,'cells':cells})
out={'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'sheets':sheets}
Path('analysis/ytcalc/extracted.json').write_text(json.dumps(out,indent=2)+'\n')
for sh in sheets:
 for cell in sh['cells']:
  if 'formula' in cell:print(f"{sh['name']}!{cell['cell']} = {cell['formula']}  [cached={cell['value']}]")
print('Original unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==out['sha256'])
