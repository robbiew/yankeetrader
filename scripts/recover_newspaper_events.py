"""Recover planet-creation and port-acquisition news in disposable DOS copies."""
import argparse
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('news_capture',ROOT/'scripts/recover_broadcast_lifetime.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.RECIPE='newspaper-creation-acquisition-v1'
engine.GRAPH={1:[100,101],100:[1,101],101:[100,102],102:[101]}
COMMON=[(2,57,100),(2,81,100000),(2,117,0),(3,81,2000),(3,117,1)]
PORT=[(2,57,101),(3053,97,3),(3053,89,777),(3053,61,100),(3053,65,100),(3053,69,100)]
NEWS='C;8;T\r~~1'


def cases():
 out=[]
 def add(name,command,patches=(),family='planet',outcome='none',**extra):
  out.append(dict(name=name,command=command,patches=COMMON+list(patches),family=family,outcome=outcome,**extra))
 def planet(name,reply='Y',name_text='New Eden',confirm='Y',patches=(),**extra):
  add(name,'L\r~~'+reply+'\r~~'+name_text+'\r~~'+confirm+'\r~~~~'+NEWS,patches,**extra)
 planet('planet-create',outcome='created')
 planet('planet-exact-credit',patches=[(2,81,25000)],outcome='created')
 planet('planet-lowercase',reply='y',confirm='y',name_text='News Mixed Planet',outcome='created')
 for tag,reply in [('decline','N'),('default','')]:
  add('planet-'+tag,'L\r~~'+reply+'\r~~~~'+NEWS)
 add('planet-poor','L\r~~~~'+NEWS,[(2,81,24999)])
 add('planet-existing','L;L;'+NEWS,[(2,57,102),(4053,73,2)])
 planet('planet-name-default',confirm='',outcome='created')
 add('planet-name-retry','L\r~~Y\r~~Rejected World\r~~N\r~~Final World\r~~Y\r~~~~'+NEWS,outcome='created')
 add('planet-name-blank','L\r~~Y\r~~\r~~~~'+NEWS)
 planet('planet-zero-turns',patches=[(2,49,0)],outcome='created')
 planet('planet-punctuation',name_text='Public: Atlas & Co',outcome='created')
 planet('planet-name-long',name_text='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv',outcome='created')
 for reserved in ['The Wanderer','Xannoron','Mercenary Base']:
  add('planet-reserved-'+reserved.lower().replace(' ','-'),'L\r~~Y\r~~'+reserved+'\r~~~~'+NEWS)
 add('planet-slots-full','L\r~~Y\r~~~~'+NEWS,[(4051+slot,85,1) for slot in range(2,101)])
 add('planet-repeat','L\r~~Y\r~~New Eden\r~~Y\r~~~~L;L;'+NEWS,outcome='created')
 for name,command,patches,outcome in [
  ('port-buyout-keep','B\r~~Y\r~~~~\r~~Y\r~~~~'+NEWS,[], 'bought'),
  ('port-buyout-rename','B\r~~Y\r~~News Harbor\r~~Y\r~~~~'+NEWS,[], 'bought'),
  ('port-rename-retry','B\r~~Y\r~~Rejected Harbor\r~~N\r~~Final Harbor\r~~Y\r~~~~'+NEWS,[], 'bought'),
  ('port-decline','B\r~~N\r~~~~'+NEWS,[], 'none'),
  ('port-default','B\r~~\r~~~~'+NEWS,[], 'none'),
  ('port-poor','B\r~~~~'+NEWS,[(2,81,30)], 'none'),
  ('port-unowned','B\r~~Y\r~~~~\r~~Y\r~~~~'+NEWS,[(3053,97,0),(3053,89,0),(3,117,0)], 'bought'),
  ('port-self','B\r~~~~'+NEWS,[(3053,97,2),(2,117,1),(3,117,0)], 'none'),
  ('port-no-port','B\r~~~~'+NEWS,[(2,57,100)], 'none'),
  ('port-teammate','B\r~~Y\r~~~~\r~~Y\r~~~~'+NEWS,[(2,89,1),(3,89,1)], 'bought'),
  ('port-zero-turns','B\r~~Y\r~~~~\r~~Y\r~~~~'+NEWS,[(2,49,0)], 'bought'),
  ('port-repeat','B\r~~Y\r~~~~\r~~Y\r~~~~B\r~~~~'+NEWS,[], 'bought'),
 ]:add(name,command,PORT+patches,family='port',outcome=outcome)
 for name,parent,actor in [
  ('planet-creator-reload','planet-create','TESTER'),
  ('port-seller-reload','port-buyout-keep','ENEMY'),
  ('port-renamed-seller-reload','port-buyout-rename','ENEMY'),
  ('port-buyer-reload','port-buyout-keep','TESTER'),
 ]:
  out.append(dict(name=name,command='\r~~~~C;6;1;'+NEWS,patches=[],family='reload',outcome='read',parent=parent,actor=actor,time='00:10:00'))
 return out


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);a=p.parse_args();selected=cases()
 if a.only:
  if set(a.only)-{c['name']for c in selected}:p.error('unknown case')
  selected=[c for c in selected if c['name']in a.only]
  if any(c.get('parent')and c['parent']not in a.only for c in selected):p.error('select parent too')
 if not 1<=a.workers<=8:p.error('workers must be 1–8')
 engine.capture(a.destination.resolve(),selected,a.workers)


if __name__=='__main__':main()
