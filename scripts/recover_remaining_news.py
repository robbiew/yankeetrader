"""Capture registration and team-membership newspaper controls in copied DOS worlds."""
import importlib.util
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('news_engine',ROOT/'scripts/recover_broadcast_lifetime.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.RECIPE='remaining-newspaper-membership-v1'

def cases():
    news='C;8;T\r~~1'
    return [
      dict(name='team-join',command='T;3;1;ABCD\r~~~~1;'+news,patches=[],roster=[3]),
      dict(name='team-wrong-password',command='T;3;1;WRNG\r~~~~1;'+news,patches=[],roster=[3]),
      dict(name='team-cancel',command='T;3;0\r~~~~1;'+news,patches=[],roster=[3]),
      dict(name='registration',command='Y\r~~\r~~~~'+news,patches=[],actor='NEWSNEW'),
    ]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args()
    engine.capture(a.destination.resolve(),cases(),4)
