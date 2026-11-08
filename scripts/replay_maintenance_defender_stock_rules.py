"""Bounded before-state admission; guards never select a captured result."""
from replay_qb_graph import mbf

def admit_world(world):
    if type(world)not in(bytes,bytearray)or len(world)!=4151*137:raise ValueError('complete default modeled world required')
    get=lambda r,o:mbf.get(world,r,o)
    day=get(1,81);attacker=get(2419,81);defenders=get(3051,81);stock=get(4054,129)
    if day==308:
        if (attacker,defenders,stock)not in((1,37,37),(1,37,0),(37,1000,37),(37,37,37))or get(2419,85)!=-2:raise ValueError('one of four exact initial defender contexts required')
    elif day==309:
        if attacker!=0 or (defenders,stock)not in((37,37),(37,0),(964,37),(1,37)):raise ValueError('measured extinct-force next-day context required')
        if bytes(world[2418*137+81:2418*137+89])!=bytes.fromhex('0000280000002800'):raise ValueError('exact inherited departure zero pair required')
    else:raise ValueError('only November4/5 before states admitted')
    if (get(3051,85),get(3051,93),get(3051,129),get(2419,93),get(2419,129))!=(-1,3,0,0,0):raise ValueError('linked mine-free Xannor defense and empty origin link required')
    if world[4053*137:4053*137+41]!=b'Gateway Cache'.ljust(41,b' ')or(get(4054,85),get(4054,73),get(4054,117))!=(13,0,0):raise ValueError('neutral zero-bank Gateway Cache required')
    physical={s:int(get(51+s,81))for s in range(1,3001)if get(51+s,81)>0 and get(51+s,85)==-2}
    if physical!=({2368:int(attacker)}if attacker else {}):raise ValueError('only the measured single attacker or extinct handoff admitted')

    if bytes(world[4053*137+73:4053*137+77])!=bytes(4)or bytes(world[4053*137+129:4053*137+133])!=mbf.enc(stock):raise ValueError('exact declared raw governor and stock required')
