"""Reuse unchanged survivor port economics after explicit friendly-stock admission."""
from replay_maintenance_survivor_ports import replay_ports as _replay_ports
from replay_maintenance_friendly_stock_rules import admit_gateway
from replay_qb_graph import mbf


def replay_ports(before,days,timer_minutes):
    if type(before)is not bytes:raise ValueError('immutable friendly-stock world required')
    admit_gateway(before)
    if [s for s in range(1,3001)if mbf.get(before,51+s,93)==3]!=[3000]:
        raise ValueError('unique actual gateway link required')
    return _replay_ports(before,days,timer_minutes)
