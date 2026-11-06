"""Explicit auxiliary writer for the twelve bounded placement/cache fixtures.

The input world is produced independently by the full before-only record model.
This module opens no target/trace files. It reads only original program literals,
and does not broaden the historical formatter's strict API or score admission.
"""
import datetime
from fractions import Fraction
import math

from replay_maintenance_aux import (
    CRLF, EOF, _matrix_clock, field, literal, name, news,
    original_literals, using,
)


RECORDS = 4151
RECORD_SIZE = 137
MAX_INITIAL_FORCE = 10037


def _whole(value, upper, label):
    if not math.isfinite(value) or value != int(value) or not 0 <= value <= upper:
        raise ValueError('bounded whole ' + label + ' required')
    return int(value)


def _encounter_losses(encounters):
    if not isinstance(encounters, (list, tuple)):
        raise ValueError('explicit modeled encounter sequence required')
    losses = 0
    last_group = 1
    for event in encounters:
        if not isinstance(event, dict):
            raise ValueError('typed modeled encounter required')
        group = event.get('group')
        initial = event.get('initial_force')
        if (type(group) is not int or not last_group < group <= 19 or
                type(initial) is not int or not 1 <= initial <= 10000 or
                type(event.get('force')) is not int or event['force'] != 0 or
                event.get('planet_name') != 'The Wanderer'):
            raise ValueError('only bounded ordinary-group Wanderer deaths are recovered')
        last_group = group
        losses += initial
    if losses > MAX_INITIAL_FORCE:
        raise ValueError('encounter losses exceed the bounded before-force inventory')
    return losses


def _admit_world(before_files, after_world, losses):
    if (type(before_files) is not dict or
            set(before_files) != {'YTDATA.DAT', 'YTNAME.DAT', 'YTNEWS.DAT'} or
            any(type(raw) is not bytes for raw in before_files.values()) or
            type(after_world) is not bytes):
        raise ValueError('three raw before files and independently modeled world required')
    before = before_files['YTDATA.DAT']
    if len(before) != RECORDS * RECORD_SIZE or len(after_world) != len(before):
        raise ValueError('complete default 4151-record worlds required')
    for world in (before, after_world):
        if any(field(world, 1, off) != expected for off, expected in
               ((53, 51), (57, 3051), (61, 4051), (93, 4151))):
            raise ValueError('default record geometry required')
    if before[:11] != b'YTSCORE.ASC' or field(before, 1, 41) != 11:
        raise ValueError('default scoreboard path required')
    for record in range(2, 52):
        if field(before, record, 85) != 0 or field(after_world, record, 85) != 0:
            raise ValueError('active-player rankings/events are outside this profile')
        for offset in range(41, 137, 4):
            if field(before, record, offset) != 0:
                raise ValueError('populated inactive-player assets are outside this profile')
            expected = -1 if offset == 109 else 0
            if field(after_world, record, offset) != expected:
                raise ValueError('unexpected inactive-player modeled asset change')
    for slot in range(1, 101):
        record = 4051 + slot
        if field(before, record, 85) != 0:
            raise ValueError('pre-existing active planets are outside this profile')
        if slot not in (1, 99, 100) and field(after_world, record, 85) != 0:
            raise ValueError('additional active planets are outside this profile')
    if any(field(before, record, 89) != 0 for record in range(3052, 4052)):
        raise ValueError('tax-funded Mercenary recruitment is outside this profile')

    totals = []
    scores = {-1: 0, -2: 0}
    for index, world in enumerate((before, after_world)):
        total = 0
        for sector in range(1, 3001):
            record = 51 + sector
            force = _whole(field(world, record, 81), MAX_INITIAL_FORCE, 'sector force')
            owner = field(world, record, 85)
            if owner not in (-2, -1, 0):
                raise ValueError('foreign human/invalid sector owners are outside this profile')
            total += force
            if index and owner in scores:
                scores[owner] += 100 * force
        if not 10000 - losses <= total <= MAX_INITIAL_FORCE:
            raise ValueError('modeled physical force is outside the initial-fixture budget')
        totals.append(total)
    if totals[0] < 10000 or totals[1] + losses != totals[0]:
        raise ValueError('modeled public casualties must conserve unique physical force')
    return before, scores, totals


def _npc_scoreboard(original, world, date, clock, scores):
    """The source8148/855d/8992 integer-sector NPC score/PRINT USING branch."""
    xannor, mercenary = scores[-1], scores[-2]
    leader = max(xannor, mercenary)
    if not 0 < leader <= 100 * MAX_INITIAL_FORCE:
        raise ValueError('bounded positive NPC score denominator required')
    # Source scores and division use the wider numeric path. These bounded
    # integer fixtures are well away from halfway PRINT USING cases; do not
    # claim arbitrary MBF/decimal rounding from Python's formatter.
    percentages = []
    for score in (xannor, mercenary):
        exact = Fraction(100 * score, leader)
        cents = 100 * exact
        if cents.denominator == 2:
            raise ValueError('halfway NPC percentage formatting is outside this profile')
        percentages.append(float(exact))
    mask = literal(original, b'  ###,###,###,###  ####.##%')
    row = using(mask, [xannor, percentages[0], mercenary, percentages[1]])
    lines = [
        b'', literal(original, b'Y a n k e e   T r a d e r   S c o r e b o a r d'), b'',
        literal(original, b'Last updated at: ') + date.strftime('%m-%d-%Y').encode() + b' ' + clock.encode(), b'',
        literal(original, b'Rank  Rank%        Score        Team   Ports   Player'),
        literal(original, b'==== ======= ================= ====== ======= ================================'), b'',
        literal(original, b'T e a m   R a n k i n g s'), b'',
        literal(original, b'Rank  Rank%        Score        Team   Team Name'),
        literal(original, b'==== ======= ================= ====== ========================================'), b'',
        literal(original, b'N o n  -  H u m a n   P l a y e r s'), b'',
        literal(original, b'    The Xannor       Rank%     The Mercenaries'),
        literal(original, b'================== =========  ================='), row, b'',
    ]
    return CRLF.join(lines) + CRLF + EOF, percentages


def synthesize(before_files, after_world, news_date, news_clock, score_date, score_clock,
               *, encounters=(), events=()):
    """Return five auxiliary outputs plus an audit; no after-target is accepted.

    `after_world` must be the caller's independently synthesized world. Both
    event sequences must be generated by that model, never parsed from targets.
    The measured fixtures produce no extra Mercenary route news; unknown event
    kinds fail closed instead of being silently omitted.
    """
    if any(type(date) is not datetime.date for date in (news_date, score_date)):
        raise ValueError('separate explicit news and scoreboard calendar dates required')
    _matrix_clock(news_clock)
    _matrix_clock(score_clock)
    if not isinstance(events, (list, tuple)) or events:
        raise ValueError('additional Mercenary/general event news is outside this profile')
    losses = _encounter_losses(encounters)
    before, scores, totals = _admit_world(before_files, after_world, losses)
    original = original_literals()
    board, percentages = _npc_scoreboard(original, after_world, score_date, score_clock, scores)
    result = {
        'YTNAME.DAT': before_files['YTNAME.DAT'],
        'YTYNEWS.DAT': before_files['YTNEWS.DAT'],
        'YTRMSG.DAT': b'',
        'YTNEWS.DAT': news(original, before, after_world, news_date, news_clock, encounters=encounters),
        'YTSCORE.ASC': board,
    }
    return result, dict(scores=scores, percentages=percentages,
                        initial_physical_force=totals[0], final_physical_force=totals[1],
                        modeled_casualties=losses, public_encounters=len(encounters), private_bytes=0)
