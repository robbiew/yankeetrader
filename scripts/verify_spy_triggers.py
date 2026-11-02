"""Independently verify retained spy-trigger controls and their provenance."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'archive/analysis/yt-combat/experiments/fixture-team-captain'
RECIPE = 'spy-triggers-v1'
BASE_SHA = '04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec'
BINS = {
    'BRUN30.EXE': '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
    'KEYFEED.COM': '06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
    'LOCAL.EXE': 'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
    'YT.EXE': 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037',
}
KEEP = {'before.dat.gz', 'after.dat.gz', 'side-before.json.gz', 'sidefiles.json.gz',
        'transcript.txt', 'game.log.gz', 'DOSDATE.LOG', 'DOSTIME.LOG', 'RETURN.LOG',
        'KEYS.TXT', 'dosbox.log'}
# Filled from the reviewed, retained controls, never imported from the writer.
GRAPH = {1:[100,2],2:[3],3:[2],100:[1,101],101:[102],102:[103],103:[101],200:[201],201:[200]}
DECLARATIONS = {'list-only': {'name': 'list-only',
               'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;C;15;1;C;15;1',
               'patches': [[2, 81, 2000000],
                           [2, 61, 1000],
                           [2, 53, 10000],
                           [3, 57, 200],
                           [3, 125, 1],
                           [152, 129, 7],
                           [153, 93, 0],
                           [152, 65, 0]]},
 'ship-info': {'name': 'ship-info',
               'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;I;C;15;1',
               'patches': [[2, 81, 2000000],
                           [2, 61, 1000],
                           [2, 53, 10000],
                           [3, 57, 200],
                           [3, 125, 1],
                           [152, 129, 7],
                           [153, 93, 0],
                           [152, 65, 0]]},
 'sensors': {'name': 'sensors',
             'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;S;C;15;1',
             'patches': [[2, 81, 2000000],
                         [2, 61, 1000],
                         [2, 53, 10000],
                         [3, 57, 200],
                         [3, 125, 1],
                         [152, 129, 7],
                         [153, 93, 0],
                         [152, 65, 0]]},
 'help': {'name': 'help',
          'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;?;C;15;1',
          'patches': [[2, 81, 2000000],
                      [2, 61, 1000],
                      [2, 53, 10000],
                      [3, 57, 200],
                      [3, 125, 1],
                      [152, 129, 7],
                      [153, 93, 0],
                      [152, 65, 0]]},
 'port-report': {'name': 'port-report',
                 'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;C;2;1;1;C;15;1',
                 'patches': [[2, 81, 2000000],
                             [2, 61, 1000],
                             [2, 53, 10000],
                             [3, 57, 200],
                             [3, 125, 1],
                             [152, 129, 7],
                             [153, 93, 0],
                             [152, 65, 0]]},
 'planet-report-foreign': {'name': 'planet-report-foreign',
                           'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;C;9;101;1;C;15;1',
                           'patches': [[2, 81, 2000000],
                                       [2, 61, 1000],
                                       [2, 53, 10000],
                                       [3, 57, 200],
                                       [3, 125, 1],
                                       [152, 129, 7],
                                       [153, 93, 0],
                                       [152, 65, 0],
                                       [152, 93, 2],
                                       [4053, 73, 3],
                                       [4053, 77, 12]]},
 'planet-report-own': {'name': 'planet-report-own',
                       'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;C;9;101;1;C;15;1',
                       'patches': [[2, 81, 2000000],
                                   [2, 61, 1000],
                                   [2, 53, 10000],
                                   [3, 57, 200],
                                   [3, 125, 1],
                                   [152, 129, 7],
                                   [153, 93, 0],
                                   [152, 65, 0],
                                   [152, 93, 2],
                                   [4053, 73, 2],
                                   [4053, 77, 12]]},
 'move': {'name': 'move',
          'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1',
          'patches': [[2, 81, 2000000],
                      [2, 61, 1000],
                      [2, 53, 10000],
                      [3, 57, 200],
                      [3, 125, 1],
                      [152, 129, 7],
                      [153, 93, 0],
                      [152, 65, 0]]},
 'dock': {'name': 'dock',
          'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;P;0;C;15;1',
          'patches': [[2, 81, 2000000],
                      [2, 61, 1000],
                      [2, 53, 10000],
                      [3, 57, 200],
                      [3, 125, 1],
                      [152, 129, 7],
                      [153, 93, 0],
                      [152, 65, 0]]},
 'no-port-dock': {'name': 'no-port-dock',
                  'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;P;0;C;15;1',
                  'patches': [[2, 81, 2000000],
                              [2, 61, 1000],
                              [2, 53, 10000],
                              [3, 57, 200],
                              [3, 125, 1],
                              [152, 129, 7],
                              [153, 93, 0],
                              [152, 65, 0]]},
 'fighters-zero': {'name': 'fighters-zero',
                   'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;F;0;C;15;1',
                   'patches': [[2, 81, 2000000],
                               [2, 61, 1000],
                               [2, 53, 10000],
                               [3, 57, 200],
                               [3, 125, 1],
                               [152, 129, 7],
                               [153, 93, 0],
                               [152, 65, 0]]},
 'fighters-five': {'name': 'fighters-five',
                   'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;F;5;C;15;1',
                   'patches': [[2, 81, 2000000],
                               [2, 61, 1000],
                               [2, 53, 10000],
                               [3, 57, 200],
                               [3, 125, 1],
                               [152, 129, 7],
                               [153, 93, 0],
                               [152, 65, 0]]},
 'fighters-over-stock': {'name': 'fighters-over-stock',
                         'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;F;1001;C;15;1',
                         'patches': [[2, 81, 2000000],
                                     [2, 61, 1000],
                                     [2, 53, 10000],
                                     [3, 57, 200],
                                     [3, 125, 1],
                                     [152, 129, 7],
                                     [153, 93, 0],
                                     [152, 65, 0]]},
 'missile-zero': {'name': 'missile-zero',
                  'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;!;100;0;C;15;1',
                  'patches': [[2, 81, 2000000],
                              [2, 61, 1000],
                              [2, 53, 10000],
                              [3, 57, 200],
                              [3, 125, 1],
                              [152, 129, 7],
                              [153, 93, 0],
                              [152, 65, 0]]},
 'missile-one': {'name': 'missile-one',
                 'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;!;100;1;C;15;1',
                 'patches': [[2, 81, 2000000],
                             [2, 61, 1000],
                             [2, 53, 10000],
                             [3, 57, 200],
                             [3, 125, 1],
                             [152, 129, 7],
                             [153, 93, 0],
                             [152, 65, 0]]},
 'plasma-zero': {'name': 'plasma-zero',
                 'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;+;100;0;C;15;1',
                 'patches': [[2, 81, 2000000],
                             [2, 61, 1000],
                             [2, 53, 10000],
                             [3, 57, 200],
                             [3, 125, 1],
                             [152, 129, 7],
                             [153, 93, 0],
                             [152, 65, 0]]},
 'planet-report-protected': {'name': 'planet-report-protected',
                             'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;C;9;101;1;C;15;1',
                             'patches': [[2, 81, 2000000],
                                         [2, 61, 1000],
                                         [2, 53, 10000],
                                         [3, 57, 200],
                                         [3, 125, 1],
                                         [152, 129, 7],
                                         [153, 93, 0],
                                         [152, 65, 0],
                                         [152, 93, 2],
                                         [4053, 73, 3],
                                         [4053, 77, 12],
                                         [152, 81, 42],
                                         [152, 85, 3]]},
 'planet-report-empty': {'name': 'planet-report-empty',
                         'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;C;9;100;1;C;15;1',
                         'patches': [[2, 81, 2000000],
                                     [2, 61, 1000],
                                     [2, 53, 10000],
                                     [3, 57, 200],
                                     [3, 125, 1],
                                     [152, 129, 7],
                                     [153, 93, 0],
                                     [152, 65, 0]]},
 'alternating-findings': {'name': 'alternating-findings',
                          'command': 'P;9;1;101\r'
                                     '~~~~\r'
                                     '~~0;C;15;1;M;100;C;15;1;M;1;C;15;1;M;100;C;15;1;M;1;C;15;1',
                          'patches': [[2, 81, 2000000],
                                      [2, 61, 1000],
                                      [2, 53, 10000],
                                      [3, 57, 200],
                                      [3, 125, 1],
                                      [152, 129, 7],
                                      [153, 93, 0],
                                      [152, 65, 0],
                                      [153, 129, 8]]},
 'plasma-one': {'name': 'plasma-one',
                'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;+;2;1;C;15;1',
                'patches': [[2, 81, 2000000],
                            [2, 61, 1000],
                            [2, 53, 10000],
                            [3, 57, 200],
                            [3, 125, 1],
                            [152, 129, 7],
                            [153, 93, 0],
                            [152, 65, 0],
                            [4, 57, 2],
                            [4, 53, 3000000],
                            [4, 61, 0],
                            [4, 125, 0]]},
 'plasma-unreachable': {'name': 'plasma-unreachable',
                        'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;+;200;1;C;15;1',
                        'patches': [[2, 81, 2000000],
                                    [2, 61, 1000],
                                    [2, 53, 10000],
                                    [3, 57, 200],
                                    [3, 125, 1],
                                    [152, 129, 7],
                                    [153, 93, 0],
                                    [152, 65, 0]]},
 'missile-over-stock': {'name': 'missile-over-stock',
                        'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;!;100;8;C;15;1',
                        'patches': [[2, 81, 2000000],
                                    [2, 61, 1000],
                                    [2, 53, 10000],
                                    [3, 57, 200],
                                    [3, 125, 1],
                                    [152, 129, 7],
                                    [153, 93, 0],
                                    [152, 65, 0]]},
 'missile-negative': {'name': 'missile-negative',
                      'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;!;100;-1;C;15;1',
                      'patches': [[2, 81, 2000000],
                                  [2, 61, 1000],
                                  [2, 53, 10000],
                                  [3, 57, 200],
                                  [3, 125, 1],
                                  [152, 129, 7],
                                  [153, 93, 0],
                                  [152, 65, 0]]},
 'mine-drop': {'name': 'mine-drop',
               'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;D;1;C;15;1',
               'patches': [[2, 81, 2000000],
                           [2, 61, 1000],
                           [2, 53, 10000],
                           [3, 57, 200],
                           [3, 125, 1],
                           [152, 129, 7],
                           [153, 93, 0],
                           [152, 65, 0]]},
 'repeat-last-report': {'name': 'repeat-last-report',
                        'command': 'P;9;1;101\r'
                                   '~~~~\r'
                                   '~~0;C;15;1;M;100;C;15;1;M;1;C;15;1;M;100;C;15;1;M;1;C;15;1',
                        'patches': [[2, 81, 2000000],
                                    [2, 61, 1000],
                                    [2, 53, 10000],
                                    [3, 57, 200],
                                    [3, 125, 1],
                                    [152, 129, 7],
                                    [153, 93, 0],
                                    [152, 65, 0]]},
 'three-spies': {'name': 'three-spies',
                 'command': 'P;9;3;101;101;101\r~~~~\r~~0;C;15;1;M;100;C;15;1',
                 'patches': [[2, 81, 2000000],
                             [2, 61, 1000],
                             [2, 53, 10000],
                             [3, 57, 200],
                             [3, 125, 1],
                             [152, 129, 7],
                             [153, 93, 0],
                             [152, 65, 0]]},
 'partial-reveal': {'name': 'partial-reveal',
                    'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;S;C;15;1',
                    'patches': [[2, 81, 2000000],
                                [2, 61, 1000],
                                [2, 53, 10000],
                                [3, 57, 200],
                                [3, 125, 1],
                                [152, 129, 7],
                                [153, 93, 0],
                                [152, 65, 0],
                                [3, 57, 101],
                                [3, 125, 0.5],
                                [152, 129, 0]]},
 'partial-reveal-target': {'name': 'partial-reveal-target',
                           'command': '\r~~~~C;6;1;I',
                           'patches': [],
                           'parent': 'partial-reveal',
                           'actor': 'ENEMY'},
 'full-hidden': {'name': 'full-hidden',
                 'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;S;C;15;1',
                 'patches': [[2, 81, 2000000],
                             [2, 61, 1000],
                             [2, 53, 10000],
                             [3, 57, 200],
                             [3, 125, 1],
                             [152, 129, 7],
                             [153, 93, 0],
                             [152, 65, 0],
                             [3, 57, 101],
                             [3, 125, 1],
                             [152, 129, 0]]},
 'full-hidden-target': {'name': 'full-hidden-target',
                        'command': '\r~~~~C;6;1;I',
                        'patches': [],
                        'parent': 'full-hidden',
                        'actor': 'ENEMY'},
 'uncloaked': {'name': 'uncloaked',
               'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;S;C;15;1',
               'patches': [[2, 81, 2000000],
                           [2, 61, 1000],
                           [2, 53, 10000],
                           [3, 57, 200],
                           [3, 125, 1],
                           [152, 129, 7],
                           [153, 93, 0],
                           [152, 65, 0],
                           [3, 57, 101],
                           [3, 125, 0],
                           [152, 129, 0]]},
 'uncloaked-target': {'name': 'uncloaked-target',
                      'command': '\r~~~~C;6;1;I',
                      'patches': [],
                      'parent': 'uncloaked',
                      'actor': 'ENEMY'},
 'partial-spy-attack': {'name': 'partial-spy-attack',
                        'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;M;101;A;N;C;15;1',
                        'patches': [[2, 81, 2000000],
                                    [2, 61, 1000],
                                    [2, 53, 10000],
                                    [3, 57, 200],
                                    [3, 125, 1],
                                    [152, 129, 7],
                                    [153, 93, 0],
                                    [152, 65, 0],
                                    [3, 57, 101],
                                    [3, 125, 0.5],
                                    [152, 129, 0]]},
 'partial-no-spy-attack': {'name': 'partial-no-spy-attack',
                           'command': 'M;100;M;101;A;N;C;15;1',
                           'patches': [[2, 81, 2000000],
                                       [2, 61, 1000],
                                       [2, 53, 10000],
                                       [3, 57, 200],
                                       [3, 125, 1],
                                       [152, 129, 7],
                                       [153, 93, 0],
                                       [152, 65, 0],
                                       [3, 57, 101],
                                       [3, 125, 0.5],
                                       [152, 129, 0]]},
 'full-hidden-attack': {'name': 'full-hidden-attack',
                        'command': 'P;9;1;101\r~~~~\r~~0;C;15;1;M;100;C;15;1;M;101;A;N;C;15;1',
                        'patches': [[2, 81, 2000000],
                                    [2, 61, 1000],
                                    [2, 53, 10000],
                                    [3, 57, 200],
                                    [3, 125, 1],
                                    [152, 129, 7],
                                    [153, 93, 0],
                                    [152, 65, 0],
                                    [3, 57, 101],
                                    [3, 125, 1],
                                    [152, 129, 0]]},
 'sensor-only-partial': {'name': 'sensor-only-partial',
                         'command': 'M;100;S;C;15;1',
                         'patches': [[2, 81, 2000000],
                                     [2, 61, 1000],
                                     [2, 53, 10000],
                                     [3, 57, 200],
                                     [3, 125, 1],
                                     [152, 129, 7],
                                     [153, 93, 0],
                                     [152, 65, 0],
                                     [3, 57, 101],
                                     [3, 125, 0.5],
                                     [152, 129, 0]]}}
EXPECTED = {'list-only': {'changes': [[2, 49, 499], [2, 81, 1667000]],
               'headers': [],
               'all_locations': [[1, 101], [1, 101], [1, 101], [1, 101]],
               'ship_records': [],
               'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                          'You detect the shimmering of a cloaking device!': 0,
                          'Attack Enemy  (Y/N)[Y]?': 0,
                          '[ Info ]': 2,
                          '[ Sensors Activated ]': 0,
                          '[ End Sensor Scan ]': 0},
               'required': []},
 'ship-info': {'changes': [[2, 49, 499], [2, 81, 1667000]],
               'headers': [],
               'all_locations': [[1, 101], [1, 101], [1, 101]],
               'ship_records': [],
               'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                          'You detect the shimmering of a cloaking device!': 0,
                          'Attack Enemy  (Y/N)[Y]?': 0,
                          '[ Info ]': 3,
                          '[ Sensors Activated ]': 0,
                          '[ End Sensor Scan ]': 0},
               'required': []},
 'sensors': {'changes': [[2, 49, 499], [2, 81, 1667000]],
             'headers': [],
             'all_locations': [[1, 101], [1, 101], [1, 101]],
             'ship_records': [],
             'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                        'You detect the shimmering of a cloaking device!': 0,
                        'Attack Enemy  (Y/N)[Y]?': 0,
                        '[ Info ]': 2,
                        '[ Sensors Activated ]': 1,
                        '[ End Sensor Scan ]': 1},
             'required': []},
 'help': {'changes': [[2, 49, 499], [2, 81, 1667000]],
          'headers': [],
          'all_locations': [[1, 101], [1, 101], [1, 101]],
          'ship_records': [],
          'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                     'You detect the shimmering of a cloaking device!': 0,
                     'Attack Enemy  (Y/N)[Y]?': 0,
                     '[ Info ]': 2,
                     '[ Sensors Activated ]': 0,
                     '[ End Sensor Scan ]': 0},
          'required': ['<Help>', 'D - <D>rop a Sector mine']},
 'port-report': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                 'headers': [],
                 'all_locations': [[1, 101], [1, 101], [1, 101]],
                 'ship_records': [],
                 'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                            'You detect the shimmering of a cloaking device!': 0,
                            'Attack Enemy  (Y/N)[Y]?': 0,
                            '[ Info ]': 2,
                            '[ Sensors Activated ]': 0,
                            '[ End Sensor Scan ]': 0},
                 'required': ['Enter sector number port is in -=> 1']},
 'planet-report-foreign': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                           'headers': [],
                           'all_locations': [[1, 101], [1, 101], [1, 101]],
                           'ship_records': [],
                           'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                      'You detect the shimmering of a cloaking device!': 0,
                                      'Attack Enemy  (Y/N)[Y]?': 0,
                                      '[ Info ]': 2,
                                      '[ Sensors Activated ]': 0,
                                      '[ End Sensor Scan ]': 0},
                           'required': ['Planet: Test Planet -*- Ground Forces: 12']},
 'planet-report-own': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                       'headers': [],
                       'all_locations': [[1, 101], [1, 101], [1, 101]],
                       'ship_records': [],
                       'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                  'You detect the shimmering of a cloaking device!': 0,
                                  'Attack Enemy  (Y/N)[Y]?': 0,
                                  '[ Info ]': 2,
                                  '[ Sensors Activated ]': 0,
                                  '[ End Sensor Scan ]': 0},
                       'lazy_fields': [[4053, 45],
                                       [4053, 49],
                                       [4053, 53],
                                       [4053, 57],
                                       [4053, 61],
                                       [4053, 65],
                                       [4053, 69],
                                       [4053, 89],
                                       [4053, 125],
                                       [4053, 129]],
                       'required': [' Item           Production     Amount    In Holds']},
 'move': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
          'headers': [[1, 101]],
          'all_locations': [[1, 101], [1, 101], [1, 102]],
          'ship_records': [],
          'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                     'You detect the shimmering of a cloaking device!': 0,
                     'Attack Enemy  (Y/N)[Y]?': 0,
                     '[ Info ]': 2,
                     '[ Sensors Activated ]': 0,
                     '[ End Sensor Scan ]': 0},
          'required': []},
 'dock': {'changes': [[2, 49, 498], [2, 81, 1667000]],
          'headers': [[1, 101]],
          'all_locations': [[1, 101], [1, 101], [1, 102]],
          'ship_records': [],
          'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                     'You detect the shimmering of a cloaking device!': 0,
                     'Attack Enemy  (Y/N)[Y]?': 0,
                     '[ Info ]': 2,
                     '[ Sensors Activated ]': 0,
                     '[ End Sensor Scan ]': 0},
          'required': []},
 'no-port-dock': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
                  'headers': [[1, 101]],
                  'all_locations': [[1, 101], [1, 101], [1, 102]],
                  'ship_records': [],
                  'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                             'You detect the shimmering of a cloaking device!': 0,
                             'Attack Enemy  (Y/N)[Y]?': 0,
                             '[ Info ]': 2,
                             '[ Sensors Activated ]': 0,
                             '[ End Sensor Scan ]': 0},
                  'required': ['No port here!']},
 'fighters-zero': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
                   'headers': [[1, 101]],
                   'all_locations': [[1, 101], [1, 101], [1, 102], [1, 102]],
                   'ship_records': [],
                   'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                              'You detect the shimmering of a cloaking device!': 0,
                              'Attack Enemy  (Y/N)[Y]?': 0,
                              '[ Info ]': 2,
                              '[ Sensors Activated ]': 0,
                              '[ End Sensor Scan ]': 0},
                   'world_values': [[151, 85, 2]],
                   'required': ['Done.  You have 1000 fighters left.']},
 'fighters-five': {'changes': [[2, 49, 498], [2, 57, 100], [2, 61, 995], [2, 81, 1667000]],
                   'headers': [[1, 101]],
                   'all_locations': [[1, 101], [1, 101], [1, 102], [1, 102]],
                   'ship_records': [],
                   'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                              'You detect the shimmering of a cloaking device!': 0,
                              'Attack Enemy  (Y/N)[Y]?': 0,
                              '[ Info ]': 2,
                              '[ Sensors Activated ]': 0,
                              '[ End Sensor Scan ]': 0},
                   'world_values': [[151, 81, 5], [151, 85, 2]],
                   'required': ['Done.  You have 995 fighters left.']},
 'fighters-over-stock': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
                         'headers': [[1, 101]],
                         'all_locations': [[1, 101], [1, 101], [1, 102]],
                         'ship_records': [],
                         'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                    'You detect the shimmering of a cloaking device!': 0,
                                    'Attack Enemy  (Y/N)[Y]?': 0,
                                    '[ Info ]': 2,
                                    '[ Sensors Activated ]': 0,
                                    '[ End Sensor Scan ]': 0},
                         'required': ["You don't have that many!"]},
 'missile-zero': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                  'headers': [],
                  'all_locations': [[1, 101], [1, 101], [1, 101]],
                  'ship_records': [],
                  'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                             'You detect the shimmering of a cloaking device!': 0,
                             'Attack Enemy  (Y/N)[Y]?': 0,
                             '[ Info ]': 2,
                             '[ Sensors Activated ]': 0,
                             '[ End Sensor Scan ]': 0},
                  'required': ['You have 7. Send your cruise missile', 'Send how many? [0] ?0']},
 'missile-one': {'changes': [[2, 49, 498], [2, 81, 1667000], [2, 97, 6]],
                 'headers': [[1, 101]],
                 'all_locations': [[1, 101], [1, 101], [1, 102]],
                 'ship_records': [],
                 'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                            'You detect the shimmering of a cloaking device!': 0,
                            'Attack Enemy  (Y/N)[Y]?': 0,
                            '[ Info ]': 2,
                            '[ Sensors Activated ]': 0,
                            '[ End Sensor Scan ]': 0},
                 'required': ['Loading course into misile targeting computer.', '*** End of Report ***']},
 'plasma-zero': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                 'headers': [],
                 'all_locations': [[1, 101], [1, 101], [1, 101]],
                 'ship_records': [],
                 'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                            'You detect the shimmering of a cloaking device!': 0,
                            'Attack Enemy  (Y/N)[Y]?': 0,
                            '[ Info ]': 2,
                            '[ Sensors Activated ]': 0,
                            '[ End Sensor Scan ]': 0},
                 'required': ['You have 9. Send your plasma bolt', 'Send how many? [0] ?0']},
 'planet-report-protected': {'changes': [[2, 49, 498], [2, 81, 1667000]],
                             'headers': [[1, 101]],
                             'all_locations': [[1, 101], [1, 101], [1, 102]],
                             'ship_records': [],
                             'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                        'You detect the shimmering of a cloaking device!': 0,
                                        'Attack Enemy  (Y/N)[Y]?': 0,
                                        '[ Info ]': 2,
                                        '[ Sensors Activated ]': 0,
                                        '[ End Sensor Scan ]': 0},
                             'required': ['No information available.'],
                             'lazy_fields': [[4053, 45],
                                             [4053, 49],
                                             [4053, 53],
                                             [4053, 57],
                                             [4053, 61],
                                             [4053, 65],
                                             [4053, 69],
                                             [4053, 89],
                                             [4053, 125],
                                             [4053, 129]]},
 'planet-report-empty': {'changes': [[2, 49, 498], [2, 81, 1667000]],
                         'headers': [[1, 101]],
                         'all_locations': [[1, 101], [1, 101], [1, 102]],
                         'ship_records': [],
                         'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                    'You detect the shimmering of a cloaking device!': 0,
                                    'Attack Enemy  (Y/N)[Y]?': 0,
                                    '[ Info ]': 2,
                                    '[ Sensors Activated ]': 0,
                                    '[ End Sensor Scan ]': 0},
                         'required': ['No information available.']},
 'alternating-findings': {'changes': [[2, 49, 495], [2, 81, 1667000]],
                          'headers': [[1, 101], [1, 102], [1, 101]],
                          'all_locations': [[1, 101], [1, 101], [1, 102], [1, 103], [1, 101], [1, 102]],
                          'ship_records': [],
                          'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                     'You detect the shimmering of a cloaking device!': 0,
                                     'Attack Enemy  (Y/N)[Y]?': 0,
                                     '[ Info ]': 2,
                                     '[ Sensors Activated ]': 0,
                                     '[ End Sensor Scan ]': 0},
                          'required': []},
 'plasma-one': {'changes': [[2, 49, 498], [2, 81, 1667000], [2, 113, 8]],
                'headers': [[1, 101]],
                'all_locations': [[1, 101], [1, 101], [1, 102]],
                'ship_records': [],
                'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                           'You detect the shimmering of a cloaking device!': 0,
                           'Attack Enemy  (Y/N)[Y]?': 0,
                           '[ Info ]': 2,
                           '[ Sensors Activated ]': 0,
                           '[ End Sensor Scan ]': 0},
                'plasma_target': True,
                'required': ['Plasma bolts targeted... firing 2500000 megawatts!',
                             'Plasma bolts dissipated.']},
 'plasma-unreachable': {'changes': [[2, 49, 498], [2, 81, 1667000], [2, 113, 8]],
                        'headers': [[1, 101]],
                        'all_locations': [[1, 101], [1, 101], [1, 102]],
                        'ship_records': [],
                        'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                   'You detect the shimmering of a cloaking device!': 0,
                                   'Attack Enemy  (Y/N)[Y]?': 0,
                                   '[ Info ]': 2,
                                   '[ Sensors Activated ]': 0,
                                   '[ End Sensor Scan ]': 0},
                        'required': ["*** You can't get there without going someplace you dont want to!",
                                     'Plasma bolts dissipated.',
                                     'Plasma bolts targeted... firing 2500000 megawatts!']},
 'missile-over-stock': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                        'headers': [],
                        'all_locations': [[1, 101], [1, 101], [1, 101]],
                        'ship_records': [],
                        'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                   'You detect the shimmering of a cloaking device!': 0,
                                   'Attack Enemy  (Y/N)[Y]?': 0,
                                   '[ Info ]': 2,
                                   '[ Sensors Activated ]': 0,
                                   '[ End Sensor Scan ]': 0},
                        'required': ['You have 7. Send your cruise missile',
                                     'Send how many? [0] ?8',
                                     'You dont have that many!']},
 'missile-negative': {'changes': [[2, 49, 499], [2, 81, 1667000]],
                      'headers': [],
                      'all_locations': [[1, 101], [1, 101], [1, 101]],
                      'ship_records': [],
                      'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                 'You detect the shimmering of a cloaking device!': 0,
                                 'Attack Enemy  (Y/N)[Y]?': 0,
                                 '[ Info ]': 2,
                                 '[ Sensors Activated ]': 0,
                                 '[ End Sensor Scan ]': 0},
                      'required': ['You have 7. Send your cruise missile', 'Send how many? [0] ?-1']},
 'mine-drop': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000], [2, 129, 7]],
               'headers': [[1, 101]],
               'all_locations': [[1, 101], [1, 101], [1, 102], [1, 102]],
               'ship_records': [],
               'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                          'You detect the shimmering of a cloaking device!': 0,
                          'Attack Enemy  (Y/N)[Y]?': 0,
                          '[ Info ]': 2,
                          '[ Sensors Activated ]': 0,
                          '[ End Sensor Scan ]': 0},
               'world_values': [[151, 129, 1]],
               'required': ['Sector 100 is now mined!']},
 'repeat-last-report': {'changes': [[2, 49, 495], [2, 81, 1667000]],
                        'headers': [[1, 101]],
                        'all_locations': [[1, 101], [1, 101], [1, 102], [1, 103], [1, 101], [1, 102]],
                        'ship_records': [],
                        'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                   'You detect the shimmering of a cloaking device!': 0,
                                   'Attack Enemy  (Y/N)[Y]?': 0,
                                   '[ Info ]': 2,
                                   '[ Sensors Activated ]': 0,
                                   '[ End Sensor Scan ]': 0},
                        'required': []},
 'three-spies': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1001000]],
                 'headers': [[1, 101], [2, 101], [3, 101]],
                 'all_locations': [[1, 101],
                                   [2, 101],
                                   [3, 101],
                                   [1, 101],
                                   [2, 101],
                                   [3, 101],
                                   [1, 102],
                                   [2, 102],
                                   [3, 102]],
                 'ship_records': [],
                 'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                            'You detect the shimmering of a cloaking device!': 0,
                            'Attack Enemy  (Y/N)[Y]?': 0,
                            '[ Info ]': 2,
                            '[ Sensors Activated ]': 0,
                            '[ End Sensor Scan ]': 0},
                 'required': []},
 'partial-reveal': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
                    'headers': [[1, 101]],
                    'all_locations': [[1, 101], [1, 101], [1, 102], [1, 102]],
                    'ship_records': ['    Enemy  - Fighters: 42 - Shields: 7',
                                     '    Enemy  - Fighters: 42 - Shields: 7'],
                    'counts': {'The spy detected the shimmering of a cloaking device!': 1,
                               'You detect the shimmering of a cloaking device!': 0,
                               'Attack Enemy  (Y/N)[Y]?': 0,
                               '[ Info ]': 2,
                               '[ Sensors Activated ]': 1,
                               '[ End Sensor Scan ]': 1},
                    'required': []},
 'partial-reveal-target': {'changes': [],
                           'headers': [],
                           'all_locations': [],
                           'ship_records': [],
                           'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                      'You detect the shimmering of a cloaking device!': 0,
                                      'Attack Enemy  (Y/N)[Y]?': 0,
                                      '[ Info ]': 3,
                                      '[ Sensors Activated ]': 0,
                                      '[ End Sensor Scan ]': 0},
                           'required': ['Checking for Radio Messages.\nNone Found.',
                                        'Log of messages sent/recieved.\nNone Found.']},
 'full-hidden': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
                 'headers': [],
                 'all_locations': [[1, 101], [1, 101], [1, 102], [1, 102]],
                 'ship_records': [],
                 'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                            'You detect the shimmering of a cloaking device!': 0,
                            'Attack Enemy  (Y/N)[Y]?': 0,
                            '[ Info ]': 2,
                            '[ Sensors Activated ]': 1,
                            '[ End Sensor Scan ]': 1},
                 'required': []},
 'full-hidden-target': {'changes': [],
                        'headers': [],
                        'all_locations': [],
                        'ship_records': [],
                        'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                   'You detect the shimmering of a cloaking device!': 0,
                                   'Attack Enemy  (Y/N)[Y]?': 0,
                                   '[ Info ]': 3,
                                   '[ Sensors Activated ]': 0,
                                   '[ End Sensor Scan ]': 0},
                        'required': ['Checking for Radio Messages.\nNone Found.',
                                     'Log of messages sent/recieved.\nNone Found.']},
 'uncloaked': {'changes': [[2, 49, 498], [2, 57, 100], [2, 81, 1667000]],
               'headers': [[1, 101]],
               'all_locations': [[1, 101], [1, 101], [1, 102], [1, 102]],
               'ship_records': ['    Enemy  - Fighters: 42 - Shields: 7',
                                '    Enemy  - Fighters: 42 - Shields: 7'],
               'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                          'You detect the shimmering of a cloaking device!': 0,
                          'Attack Enemy  (Y/N)[Y]?': 0,
                          '[ Info ]': 2,
                          '[ Sensors Activated ]': 1,
                          '[ End Sensor Scan ]': 1},
               'required': []},
 'uncloaked-target': {'changes': [],
                      'headers': [],
                      'all_locations': [],
                      'ship_records': [],
                      'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                 'You detect the shimmering of a cloaking device!': 0,
                                 'Attack Enemy  (Y/N)[Y]?': 0,
                                 '[ Info ]': 3,
                                 '[ Sensors Activated ]': 0,
                                 '[ End Sensor Scan ]': 0},
                      'required': ['Checking for Radio Messages.\nNone Found.',
                                   'Log of messages sent/recieved.\nNone Found.']},
 'partial-spy-attack': {'changes': [[2, 49, 497], [2, 57, 101], [2, 81, 1667000]],
                        'headers': [[1, 101]],
                        'all_locations': [[1, 101], [1, 101], [1, 102], [1, 103]],
                        'ship_records': ['    Enemy  - Fighters: 42 - Shields: 7',
                                         '    Enemy  - Fighters: 42 - Shields: 7',
                                         '    Enemy  - Fighters: 42 - Shields: 7',
                                         '    Enemy  - Fighters: 42 - Shields: 7'],
                        'counts': {'The spy detected the shimmering of a cloaking device!': 1,
                                   'You detect the shimmering of a cloaking device!': 0,
                                   'Attack Enemy  (Y/N)[Y]?': 1,
                                   '[ Info ]': 2,
                                   '[ Sensors Activated ]': 0,
                                   '[ End Sensor Scan ]': 0},
                        'required': ['Attack Enemy  (Y/N)[Y]? N']},
 'partial-no-spy-attack': {'changes': [[2, 49, 498], [2, 57, 101]],
                           'headers': [],
                           'all_locations': [],
                           'ship_records': ['    Enemy  - Fighters: 42 - Shields: 7',
                                            '    Enemy  - Fighters: 42 - Shields: 7'],
                           'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                      'You detect the shimmering of a cloaking device!': 1,
                                      'Attack Enemy  (Y/N)[Y]?': 1,
                                      '[ Info ]': 2,
                                      '[ Sensors Activated ]': 0,
                                      '[ End Sensor Scan ]': 0},
                           'required': ['Attack Enemy  (Y/N)[Y]? N']},
 'full-hidden-attack': {'changes': [[2, 49, 497], [2, 57, 101], [2, 81, 1667000]],
                        'headers': [],
                        'all_locations': [[1, 101], [1, 101], [1, 102]],
                        'ship_records': [],
                        'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                   'You detect the shimmering of a cloaking device!': 0,
                                   'Attack Enemy  (Y/N)[Y]?': 0,
                                   '[ Info ]': 2,
                                   '[ Sensors Activated ]': 0,
                                   '[ End Sensor Scan ]': 0},
                        'required': ["There's no one here!"]},
 'sensor-only-partial': {'changes': [[2, 49, 499], [2, 57, 100]],
                         'headers': [],
                         'all_locations': [],
                         'ship_records': ['    Enemy  - Fighters: 42 - Shields: 7'],
                         'counts': {'The spy detected the shimmering of a cloaking device!': 0,
                                    'You detect the shimmering of a cloaking device!': 1,
                                    'Attack Enemy  (Y/N)[Y]?': 0,
                                    '[ Info ]': 2,
                                    '[ Sensors Activated ]': 1,
                                    '[ End Sensor Scan ]': 1},
                         'required': []}}
FOOTPRINT = {'list-only': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'ship-info': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'sensors': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'help': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'port-report': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'planet-report-foreign': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'planet-report-own': [[2, 109],
                       [3, 109],
                       [4, 109],
                       [5, 109],
                       [6, 109],
                       [2, 49],
                       [2, 81],
                       [4053, 45],
                       [4053, 49],
                       [4053, 53],
                       [4053, 57],
                       [4053, 61],
                       [4053, 65],
                       [4053, 69],
                       [4053, 89],
                       [4053, 125],
                       [4053, 129]],
 'move': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'dock': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'no-port-dock': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'fighters-zero': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81], [151, 85]],
 'fighters-five': [[2, 109],
                   [3, 109],
                   [4, 109],
                   [5, 109],
                   [6, 109],
                   [2, 49],
                   [2, 57],
                   [2, 61],
                   [2, 81],
                   [151, 81],
                   [151, 85]],
 'fighters-over-stock': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'missile-zero': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'missile-one': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81], [2, 97]],
 'plasma-zero': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'planet-report-protected': [[2, 109],
                             [3, 109],
                             [4, 109],
                             [5, 109],
                             [6, 109],
                             [2, 49],
                             [2, 81],
                             [4053, 45],
                             [4053, 49],
                             [4053, 53],
                             [4053, 57],
                             [4053, 61],
                             [4053, 65],
                             [4053, 69],
                             [4053, 89],
                             [4053, 125],
                             [4053, 129]],
 'planet-report-empty': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'alternating-findings': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'plasma-one': [[2, 109],
                [3, 109],
                [4, 109],
                [5, 109],
                [6, 109],
                [2, 49],
                [2, 81],
                [2, 113],
                [4, 53],
                [4, 61]],
 'plasma-unreachable': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81], [2, 113]],
 'missile-over-stock': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'missile-negative': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'mine-drop': [[2, 109],
               [3, 109],
               [4, 109],
               [5, 109],
               [6, 109],
               [2, 49],
               [2, 57],
               [2, 81],
               [2, 129],
               [151, 129]],
 'repeat-last-report': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 81]],
 'three-spies': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'partial-reveal': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'partial-reveal-target': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'full-hidden': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'full-hidden-target': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'uncloaked': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'uncloaked-target': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'partial-spy-attack': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'partial-no-spy-attack': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57]],
 'full-hidden-attack': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57], [2, 81]],
 'sensor-only-partial': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109], [2, 49], [2, 57]]}
RECIPE_SHA = '8dea0a7a91e56a811d7fcaf242d6724694e2ff84eaf89b53dc7c1bf4b500cda8'
NATIVE_RANGES = {'wrapper': ('0x1a6e4', 20),
 'move-gate': ('0x11bf4', 265),
 'launch-gate': ('0x1205a', 512),
 'dock-gate': ('0x1660e', 175),
 'planet-report-gate': ('0x19f80', 632),
 'spy-routine': ('0x304ca', 2115),
 'sensors-shared-cache': ('0x2525d', 493),
 'attack-shared-cache': ('0x1292b', 373),
 'cache-initialization': ('0x2b3c3', 224),
 'self-cache-refresh': ('0x1a545', 40),
 'cloak-decay-cache': ('0x1a764', 37),
 'sound-helper': ('0x20262', 465),
 'console-helper': ('0x20f98', 139),
 'warning-helper': ('0x29826', 99),
 'spy-drain-input': ('0x30d10', 82),
 'spy-pause-input': ('0x30d65', 187),
 'shared-constants': ('0x3661a', 16),
 'spy-constants': ('0x38c0c', 108),
 'caller-field-refresh': ('0x1a41d', 296),
 'owner-team-access': ('0x28b6f', 194)}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    path = Path(path)
    if path.exists():
        return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix + '.gz').read_bytes()))


def zipped(path):
    return gzip.decompress(Path(path).read_bytes())


def get(data, record, offset):
    raw = data[(record-1)*137+offset:(record-1)*137+offset+4]
    assert len(raw) == 4, 'MBF field bounds'
    if not raw[3]:
        return 0.0
    mantissa = int.from_bytes(raw[:3], 'little')
    value = math.ldexp(1 + (mantissa & 0x7fffff)/(1 << 23), raw[3]-129)
    return -value if mantissa & 0x800000 else value


def put(data, record, offset, value):
    if not value:
        raw = bytes(4)
    else:
        fraction, exponent = math.frexp(abs(value))
        mantissa = round((2*fraction-1)*(1 << 23))
        if mantissa == 1 << 23:
            mantissa = 0
            exponent += 1
        raw = (mantissa | (0x800000 if value < 0 else 0)).to_bytes(3, 'little') + bytes([exponent+128])
    at = (record-1)*137+offset
    assert 0 <= at < at+4 <= len(data), 'MBF patch bounds'
    data[at:at+4] = raw


def setup(declaration, baseline):
    world = bytearray(baseline)
    for sector, warps in GRAPH.items():
        at = (51+sector-1)*137
        world[at:at+137] = bytes(137)
        for offset, value in zip(range(41, 65, 4), warps):
            put(world, 51+sector, offset, value)
    patches = [[2, o, v] for o, v in {45: 0, 49: 500, 57: 1, 89: 0, 93: 0, 105: 0, 125: 0}.items()]
    patches += [[3, o, v] for o, v in {45: 0, 57: 2, 61: 42, 53: 7, 89: 0, 125: 1}.items()]
    patches += [[52, 65, 1], [152, 65, 2], [3053, 93, 101], [153, 93, 2], [4053, 73, 0], [4053, 77, 12]]
    patches += declaration['patches']
    for record, offset, value in patches:
        put(world, record, offset, value)
    return bytes(world), patches


def clock(directory, case):
    assert case['date'] == '10/24/2026', 'declared DOS date'
    assert re.search(r'Current date: [A-Za-z]{3} 10/24/2026(?:\n|$)', (directory/'DOSDATE.LOG').read_text()), 'DOS date'
    match = re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)', (directory/'DOSTIME.LOG').read_text())
    assert match, 'DOS clock'
    h, m, s, f, period = match.groups()
    actual = (int(h) % 12 + (12 if period == 'pm' else 0))*3600 + int(m)*60 + int(s) + int(f)/10**len(f)
    h, m, s = map(int, case['time'].split(':'))
    assert abs(actual-(h*3600+m*60+s)) <= .06, 'DOS clock mismatch'


def semantics(declaration, before, after, initial, final, text):
    name = declaration['name']
    expected = EXPECTED[name]
    actor = 3 if declaration.get('actor') == 'ENEMY' else 2
    identity = 'Enemy' if actor == 3 else 'Tester'
    assert re.findall(r'^Welcome ([^\r\n]+)!$', text, re.MULTILINE) == [identity], 'login identity'
    alias = before[(actor-1)*137:(actor-1)*137+41].decode('cp437').rstrip()
    aliases = [a.rstrip() for a in re.findall(r'^Name[ \t]+:[ \t]+([^\r\n]+)$', text, re.MULTILINE)]
    assert aliases and set(aliases) == {alias}, 'login alias'
    assert 'Entering a new player' not in text and 'Entering a new ship' not in text, 'unexpected registration/replacement'
    for phrase in expected.get('required', []):
        assert phrase in text, 'required spy observation: '+phrase
    for phrase in expected.get('forbidden', []):
        assert phrase not in text, 'forbidden spy observation: '+phrase
    for phrase, count in expected.get('counts', {}).items():
        assert text.count(phrase) == count, 'spy observation count: '+phrase
    if 'locations' in expected:
        assert [int(n) for n in re.findall(r'Spy # 1 will hunt in sector (\d+)', text)] == expected['locations'], 'spy locations'
    if 'all_locations' in expected:
        actual = [[int(a), int(b)] for a, b in re.findall(r'^Spy # (\d+) will hunt in sector (\d+)\.$', text, re.MULTILINE)]
        assert actual == expected['all_locations'], 'complete ordered spy locations'
    if 'headers' in expected:
        actual = [[int(a), int(b)] for a, b in re.findall(r'^\*\*\* RADIO MESSAGE FROM SPY #(\d+)! The following was found in sector (\d+):$', text, re.MULTILINE)]
        assert actual == expected['headers'], 'complete ordered spy report headers'
    if 'ship_records' in expected:
        assert re.findall(r'^    .* - Fighters: .*$', text, re.MULTILINE) == expected['ship_records'], 'complete ordered ship records'
    resource_changes = {(r,o): value for r,o,value in expected.get('changes',[])}
    if expected.get('plasma_target'):
        hits = re.findall(r'^The plasma bolts hit Third  in 2 reducing\nshields to ([0-9]+(?:\.[0-9]+)?(?:[Ee][+-]?[0-9]+)?) units and destroying 0 fighters!$', text, re.MULTILINE)
        assert len(hits)==1, 'single isolated plasma hit'
        printed = float(hits[0]); actual = get(after,4,53)
        assert math.isfinite(printed) and 0<actual<get(before,4,53)==3000000, 'bounded ordinary plasma damage'
        # DOS output rounds native single precision to its printed significant digits.
        assert math.isclose(actual,printed,rel_tol=5e-7,abs_tol=.5), 'plasma shield receipt'
        resource_changes[(4,53)] = actual
        assert get(after,4,45)==get(before,4,45)==0, 'isolated plasma target remains alive'
    for record in range(2,7):
        for offset in (49,53,57,61,65,69,73,77,81,89,93,97,105,113,121,125,129):
            value = resource_changes.get((record,offset),get(before,record,offset))
            assert get(after,record,offset) == value, ('account resources',record,offset)
    for record, offset, value in expected.get('resources', []):
        assert get(after, record, offset) == value, ('resource outcome', record, offset)
    for record in expected.get('conserved_players', []):
        for offset in (49, 53, 57, 61, 65, 69, 73, 77, 81, 89, 93, 97, 105, 113, 121, 125, 129):
            assert get(before, record, offset) == get(after, record, offset), ('conserved resources', record, offset)
    assert final.get('YTRMSG.DAT', b'') == b'', 'no deferred radio notification'
    news_before = initial['YTNEWS.DAT']
    assert news_before.endswith(b'\x1a'), 'source newspaper EOF'
    assert final['YTNEWS.DAT'].startswith(news_before[:-1]), 'existing newspaper preservation'
    suffix = final['YTNEWS.DAT'][len(news_before)-1:]
    news_pattern = rb'-=\*=- \d{2}:\d{2}:\d{2} '+re.escape(alias.encode('cp437'))+rb'  Logged on -=\*=-\r\n'
    if expected.get('plasma_target'):
        ordinary_hit = (alias+" 's plasma bolts hit Third  in 2 reducing\r\nshields to "+hits[0]+" units and destroying 0 fighters!\r\n").encode('cp437')
        news_pattern += re.escape(ordinary_hit)
    assert re.fullmatch(news_pattern+rb'\x1a', suffix), 'only declared ordinary newspaper append'
    assert set(final) == set(initial), 'unexpected auxiliary file'
    for filename in set(initial)-{'YTNEWS.DAT', 'YTSCORE.ASC', 'DORINFO1.DEF'}:
        assert final[filename] == initial[filename], 'unrelated auxiliary mutation: '+filename
    door_lines = initial['DORINFO1.DEF'].split(b'\r\n')
    assert len(door_lines)>6, 'source door identity'
    door_lines[6] = declaration.get('actor','TESTER').encode()
    assert final['DORINFO1.DEF'] == b'\r\n'.join(door_lines), 'actor door identity'
    for record in range(2,7):
        assert math.isfinite(get(after,record,109)) and get(after,record,109)>=0, 'finite nonnegative score cache'
    for record,offset,value in expected.get('world_values',[]):
        assert get(after,record,offset)==value, ('ordinary action world outcome',record,offset)
    for record,offset in expected.get('lazy_fields',[]):
        value=get(after,record,offset)
        assert math.isfinite(value) and value>=get(before,record,offset), 'nondecreasing ordinary planet projection'
    masked = bytearray(after)
    for record, offset in FOOTPRINT[name]:
        at = (record-1)*137+offset
        masked[at:at+4] = before[at:at+4]
    assert bytes(masked) == before, 'unrelated world mutation'


def verify_control(directory, declaration, case, baseline, worlds, auxiliaries):
    name = declaration['name']
    assert re.fullmatch(r'[a-z0-9-]+', name), 'scenario path'
    directory = Path(directory)
    d = directory/name
    assert case == read(d/'result.json'), 'manifest/result mismatch'
    assert all(case[k] == value for k, value in declaration.items()), 'manifest/declaration mismatch'
    assert case['recipe'] == RECIPE and case['baseline_sha256'] == BASE_SHA and case['binaries'] == BINS, 'binary/session identity'
    assert case['date'] == declaration.get('date', '10/24/2026') and case['time'] == declaration.get('time', '00:00:00'), 'declared clock identity'
    assert case['timeout_seconds'] == 150, 'capture timeout declaration'
    assert case['complete'] and case['program_returned'] and not case['timed_out'], 'incomplete DOS control'
    assert set(case['files']) == KEEP and {p.name for p in d.iterdir()} == KEEP | {'result.json'}, 'retained file set'
    for filename, digest in case['files'].items():
        assert sha((d/filename).read_bytes()) == digest, ('file hash', name, filename)
    clock(d, case)
    # The hardened shared capture helper uses this existing normal-return marker.
    assert (d/'RETURN.LOG').read_bytes() == b'BROADCAST_PROGRAM_RETURNED\r\n', 'DOS return marker'
    before, after = zipped(d/'before.dat.gz'), zipped(d/'after.dat.gz')
    assert len(before) == len(after) == 568687, 'world size'
    if declaration.get('parent'):
        assert declaration['parent'] in worlds, 'parent ordering'
        expected = bytearray(worlds[declaration['parent']])
        patches = declaration['patches']
        for record, offset, value in patches:
            put(expected, record, offset, value)
        initial = auxiliaries[declaration['parent']]
    else:
        expected, patches = setup(declaration, baseline)
        initial = {p.name: p.read_bytes() for p in SOURCE.iterdir() if p.suffix.upper() in ('.DAT', '.ASC', '.DEF', '.TMP') and p.name != 'YTDATA.DAT'}
    assert case['applied_patches'] == patches, 'declared patch list'
    assert before == expected, 'undeclared setup or broken world chain'
    assert {n: bytes.fromhex(v) for n, v in read(d/'side-before.json').items()} == initial, 'auxiliary input chain'
    auxiliary = read(d/'sidefiles.json')
    final = {n: bytes.fromhex(v['hex']) for n, v in auxiliary.items()}
    assert all(v['after_sha256'] == sha(final[n]) and v['before_sha256'] == (sha(initial[n]) if n in initial else None) for n, v in auxiliary.items()), 'auxiliary identity'
    tail = '\r0\r~Q;Y\r~~' if declaration.get('port_rescue') else '\rQ;Y\r~~'
    assert (d/'KEYS.TXT').read_bytes() == ('\r~~~~~\r~'+declaration['command']+'\r~~~~'+tail*24).encode(), 'exact input stream'
    text = (d/'transcript.txt').read_text()
    assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n', '\n') == text, 'raw transcript identity'
    assert 'Returning to Yankee Trader Local Logon Program...' in text, 'normal program return'
    semantics(declaration, before, after, initial, final, text)
    return after, final


def loaded(data):
    """Reconstruct the exact observed MZ load image including segment fixups."""
    assert data[:2] == b'MZ', 'native MZ identity'
    image = bytearray(data[struct.unpack_from('<H', data, 8)[0]*16:])
    table = struct.unpack_from('<H', data, 24)[0]
    for i in range(struct.unpack_from('<H', data, 6)[0]):
        offset, segment = struct.unpack_from('<HH', data, table+4*i)
        at = segment*16+offset
        value = struct.unpack_from('<H', image, at)[0]
        struct.pack_into('<H', image, at, (value+0x1000) & 0xffff)
    return image

def verify_load_image(e,binary,image):
    value=e['normalized_result'];observed=value['observations']
    assert e['subject']['digest']['sha256']==sha(binary), 'native image target'
    header=struct.unpack_from('<H',binary,8)[0]*16
    assert value['status']=='verified' and value['format']=='dos-mz' and value['target_sha256']==sha(binary), 'native image verification'
    assert value['header_bytes']==header and value['module_bytes']==len(binary)-header and value['overlay_bytes']==0 and value['load_segment']==0x1000, 'native image bounds'
    ip,cs=struct.unpack_from('<HH',binary,20)
    assert value['entry']==dict(linear_address=hex(0x10000+cs*16+ip),offset=ip,relative_segment=cs), 'native entry mapping'
    assert observed['entry_points']==[value['entry']['linear_address']] and observed['language_id']=='x86:LE:16:Real Mode', 'native entry observations'
    assert len(observed['source_files'])==1, 'native source count'
    source=observed['source_files'][0]
    assert source['size']==len(binary) and source['original_sha256']==sha(binary) and source['modified_sha256']==sha(binary[:header]+image), 'native source digests'
    records=observed['relocations'];count=struct.unpack_from('<H',binary,6)[0];table=struct.unpack_from('<H',binary,24)[0]
    assert len(records)==count, 'native relocation count'
    for i,r in enumerate(records):
        offset,segment=struct.unpack_from('<HH',binary,table+4*i);at=segment*16+offset
        old=binary[header+at:header+at+2];new=bytes(image[at:at+2])
        assert r['address']==hex(0x10000+at) and r['segment']==segment+0x1000 and r['offset']==offset, 'native relocation address'
        assert r['original_bytes_hex']==old.hex() and r['memory_bytes_hex']==new.hex() and r['values']==[segment,offset,int.from_bytes(new,'little')] and r['status']=='APPLIED', 'native relocation bytes'
    coverage=[]
    for m in observed['mappings']:
        if not m['initialized']:
            assert m['file_offset'] is None and m['source_file_index'] is None and m['sha256'] is None, 'native uninitialized mapping'
            continue
        offset=m['file_offset'];size=m['length'];coverage.append((offset,offset+size))
        assert m['source_file_index']==0 and 0<=offset<offset+size<=len(binary), 'native file mapping'
        if m['address_space']=='HEADER':
            assert m['start']=='HEADER:0x0' and m['end']=='HEADER:'+hex(header-1) and offset==0 and size==header and not m['loaded'] and m['overlay'], 'native header mapping'
            raw=binary[:header]
        else:
            start=int(m['start'],16);end=int(m['end'],16)
            assert m['address_space']=='ram' and start==0x10000+offset-header and end==start+size-1 and m['loaded'] and not m['overlay'], 'native module mapping'
            raw=bytes(image[start-0x10000:end-0x10000+1])
        assert sha(raw)==m['sha256'], 'native mapped bytes'
    coverage.sort();assert coverage[0][0]==0 and coverage[-1][1]==len(binary) and all(coverage[i][1]==coverage[i+1][0] for i in range(len(coverage)-1)), 'native mapping coverage'
    assert value['checks'] and all(c['matched'] and c['expected']==c['observed'] for c in value['checks']), 'native self-check consistency'


def verify_native(root):
    dossier = read(Path(root)/'rea.json')
    binary = (ROOT/'archive/dos-original/YT.EXE').read_bytes()
    assert sha(binary) == BINS['YT.EXE'], 'native binary identity'
    image = loaded(binary)
    profile = '92fec87c3e8c374652fd603898f727129f4c0cecccf8cee1c17c98a90aced029'
    reads = dossier['byte_evidence']
    assert len(reads) == len(NATIVE_RANGES), 'native observation count'
    assert {e['label'] for e in reads} == set(NATIVE_RANGES), 'native label set'
    records = reads + dossier['search_evidence'] + [dossier['load_image_evidence']]
    for e in records:
        assert e['subject']['digest']['sha256'] == sha(binary), 'native target identity'
        assert e['analysis_profile']['digest'] == profile, 'native analysis profile'
        assert e['provider']['id'] == 'ghidra' and e['provider']['version'] == '12.1.4', 'native provider identity'
    for e in reads:
        address, length = NATIVE_RANGES[e['label']]
        v = e['normalized_result']
        assert e['operation'] == 'read_bytes' and e['parameters'] == dict(address=address, length=length), 'native read parameters'
        assert v['address'] == address and v['complete'] and v['requested_bytes'] == v['returned_bytes'] == length, 'incomplete native bytes'
        at = int(address,16)-0x10000
        assert 0 <= at < at+length <= len(image) and bytes.fromhex(v['bytes_hex']) == image[at:at+length], 'native bytes'
    assert dossier['load_image_evidence']['operation'] == 'inspect_native_load_image', 'native load-image operation'
    verify_load_image(dossier['load_image_evidence'],binary,image)
    assert len(dossier['search_evidence']) == 1, 'native search count'
    search = dossier['search_evidence'][0]
    assert search['operation'] == 'search_bytes' and search['parameters'] == dict(pattern='cd 3f 58 e3 a6',start='0x10000',end='0x1f41f',limit=100), 'native search parameters'
    result = search['normalized_result']
    assert result['complete'] and result['next_cursor'] is None, 'incomplete native search'
    assert result['searched'] == dict(blocks=[dict(segment='CODE_0',start='0x10000',end='0x1f41f',bytes=62496)],bytes=62496,skipped_uninitialized=[],skipped_not_loaded=[]), 'native search boundary'
    needle = bytes.fromhex('cd3f58e3a6')
    positions = [i for i in range(62496-len(needle)+1) if image[i:i+len(needle)] == needle]
    assert positions == [0x1cae,0x2253,0x6693,0xa1da], 'native trigger search matches'
    header = struct.unpack_from('<H',binary,8)[0]*16
    assert result['matches'] == [dict(address=hex(0x10000+i),segment='CODE_0',file_offset=header+i,procedure=None) for i in positions], 'native trigger search evidence'
    return len(reads)



def verify(root=ROOT/'research/yt-spies/triggers', dos=None):
    root = Path(root)
    assert GRAPH and DECLARATIONS and EXPECTED and FOOTPRINT and RECIPE_SHA, 'unfrozen spy declarations'
    directory = Path(dos) if dos is not None else root/'dos'
    baseline = (SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline) == BASE_SHA and zipped(directory/'baseline.dat.gz') == baseline, 'baseline identity'
    recipe_bytes = (directory/'recipe.json').read_bytes()
    assert sha(recipe_bytes) == RECIPE_SHA, 'frozen declarations'
    recipe, manifest = json.loads(recipe_bytes), read(directory/'results.json')
    assert recipe['recipe'] == manifest['recipe'] == RECIPE, 'recipe identity'
    declarations = {c['name']: c for c in recipe['scenarios']}
    rows = {c['name']: c for c in manifest['scenarios']}
    assert declarations == DECLARATIONS, 'frozen scenario declarations'
    assert len(rows) == len(manifest['scenarios']) == len(declarations), 'scenario count'
    assert set(rows) == set(declarations) == set(EXPECTED) == set(FOOTPRINT), 'scenario identity'
    binaries = {n: (ROOT/('archive/analysis/yt-combat' if n == 'KEYFEED.COM' else 'archive/dos-original')/n).read_bytes() for n in BINS}
    assert {n: sha(value) for n, value in binaries.items()} == BINS, 'archived binary identity'
    worlds, auxiliaries = {}, {}
    for name, declaration in DECLARATIONS.items():
        try:
            worlds[name], auxiliaries[name] = verify_control(directory, declaration, rows[name], baseline, worlds, auxiliaries)
        except AssertionError as error:
            raise AssertionError(f'{name}: {error}') from error
    native = verify_native(root)
    print(f'Verified {len(rows)} returned spy controls, {sum(bool(c.get("parent")) for c in declarations.values())} world/auxiliary chains and {native} native observations.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research', type=Path, default=ROOT/'research/yt-spies/triggers')
    p.add_argument('--dos', type=Path, help='Fresh complete DOS capture directory; use the selected research root for native evidence')
    args=p.parse_args()
    verify(args.research,args.dos)
