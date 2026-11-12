"""Independent DOUBLE multiplication entry-state, prior-FAC and provenance audit."""
import hashlib, json, shlex, struct
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-multiply-double/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_multiply_double.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='d6c501a5abbbcd06a739083c2cc0169e792058868af206135ae3c7fb5f18c186'
SOURCE_PACKETS=[('entries.json', 44859, 78, '96545a5cc1d0c565ecc36cb31ea044a325d0afea47c4de0326a9f67c28bd7a00'), ('partial-products.json', 45196, 322, 'bb44f645357e36f1cc32d1f8596b75a8f4b304fa0fe183084f536fe548f82530')]
INVENTORY_SHA='b91461f8a17d424ca1986f888b765d63a3d33dea4a4cc193931c9cffb497365d'
MATRIX={'op92-both-zero': {'op': 146,
                    'left': '0000000000000000',
                    'right': '0000000000000000',
                    'initial': 5,
                    'fac': '0000000000000000'},
 'op92-aliases': {'op': 146,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 5,
                  'fac': '123456789abcde00'},
 'op92-left-zero': {'op': 146,
                    'left': '123456789abcde00',
                    'right': '0000000000008081',
                    'initial': 5,
                    'fac': '123456789abcde00'},
 'op92-right-zero': {'op': 146,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 5,
                     'fac': '0000000000000081'},
 'op92-max-zero': {'op': 146,
                   'left': 'ffffffffffff7fff',
                   'right': '123456789abcde00',
                   'initial': 5,
                   'fac': 'ffffffffffff7fff'},
 'op92-one': {'op': 146,
              'left': '0000000000000081',
              'right': '0000000000000081',
              'initial': 5,
              'fac': '0000000000000081'},
 'op92-one-negative': {'op': 146,
                       'left': '0000000000008081',
                       'right': '0000000000000081',
                       'initial': 5,
                       'fac': '0000000000008081'},
 'op92-both-negative': {'op': 146,
                        'left': '0000000000008081',
                        'right': '0000000000008081',
                        'initial': 5,
                        'fac': '0000000000008081'},
 'op92-fraction': {'op': 146,
                   'left': '0000000000004081',
                   'right': '0000000000004081',
                   'initial': 5,
                   'fac': '0000000000004081'},
 'op92-fraction-negative': {'op': 146,
                            'left': '000000000000c081',
                            'right': '0000000000004081',
                            'initial': 5,
                            'fac': '000000000000c081'},
 'op92-raw-align': {'op': 146,
                    'left': 'cdab896745230181',
                    'right': '23f1debc9a780681',
                    'initial': 5,
                    'fac': 'cdab896745230181'},
 'op92-raw-reversed': {'op': 146,
                       'left': '23f1debc9a780681',
                       'right': 'cdab896745230181',
                       'initial': 5,
                       'fac': '23f1debc9a780681'},
 'op92-min-half': {'op': 146,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 5,
                   'fac': '0000000000000001'},
 'op92-flush-before-round': {'op': 146,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 5,
                             'fac': '0100000000000040'},
 'op92-negative-flush': {'op': 146,
                         'left': '0100000000008040',
                         'right': 'feffffffffff7f41',
                         'initial': 5,
                         'fac': '0100000000008040'},
 'op92-round-overflow': {'op': 146,
                         'left': '01000000000000c0',
                         'right': 'feffffffffff7fc0',
                         'initial': 5,
                         'fac': '01000000000000c0'},
 'op92-max-two': {'op': 146,
                  'left': 'ffffffffffff7fff',
                  'right': '0000000000000082',
                  'initial': 5,
                  'fac': 'ffffffffffff7fff'},
 'op92-max-one': {'op': 146,
                  'left': 'ffffffffffff7fff',
                  'right': '0000000000000081',
                  'initial': 5,
                  'fac': 'ffffffffffff7fff'},
 'op92-min-one': {'op': 146,
                  'left': '0000000000000001',
                  'right': '0000000000000081',
                  'initial': 5,
                  'fac': '0000000000000001'},
 'op92-tie111-1': {'op': 146,
                   'left': '0000000000004081',
                   'right': '0100000000000081',
                   'initial': 5,
                   'fac': '0000000000004081'},
 'op92-tie111-1-negative': {'op': 146,
                            'left': '000000000000c081',
                            'right': '0100000000000081',
                            'initial': 5,
                            'fac': '000000000000c081'},
 'op92-tie111-3': {'op': 146,
                   'left': '0000000000004081',
                   'right': '0300000000000081',
                   'initial': 5,
                   'fac': '0000000000004081'},
 'op92-tie111-3-negative': {'op': 146,
                            'left': '000000000000c081',
                            'right': '0300000000000081',
                            'initial': 5,
                            'fac': '000000000000c081'},
 'op92-tie112-2': {'op': 146,
                   'left': '0000000000004081',
                   'right': '0200000000004081',
                   'initial': 5,
                   'fac': '0000000000004081'},
 'op92-tie112-2-negative': {'op': 146,
                            'left': '000000000000c081',
                            'right': '0200000000004081',
                            'initial': 5,
                            'fac': '000000000000c081'},
 'op92-tie112-6': {'op': 146,
                   'left': '0000000000004081',
                   'right': '0600000000004081',
                   'initial': 5,
                   'fac': '0000000000004081'},
 'op92-tie112-6-negative': {'op': 146,
                            'left': '000000000000c081',
                            'right': '0600000000004081',
                            'initial': 5,
                            'fac': '000000000000c081'},
 'op92-partial-word-bit0': {'op': 146,
                            'left': '0100000000000081',
                            'right': '23f1debc9a780681',
                            'initial': 16777215,
                            'fac': '0100000000000081'},
 'op92-partial-word-bit1': {'op': 146,
                            'left': '0200000000000081',
                            'right': '23f1debc9a780681',
                            'initial': 16777215,
                            'fac': '0200000000000081'},
 'op92-partial-word-bit7': {'op': 146,
                            'left': '8000000000000081',
                            'right': '23f1debc9a780681',
                            'initial': 16777215,
                            'fac': '8000000000000081'},
 'op92-partial-word-bit8': {'op': 146,
                            'left': '0001000000000081',
                            'right': '23f1debc9a780681',
                            'initial': 16777215,
                            'fac': '0001000000000081'},
 'op92-partial-word-bit15': {'op': 146,
                             'left': '0080000000000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0080000000000081'},
 'op92-partial-word-bit16': {'op': 146,
                             'left': '0000010000000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000010000000081'},
 'op92-partial-word-bit23': {'op': 146,
                             'left': '0000800000000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000800000000081'},
 'op92-partial-word-bit24': {'op': 146,
                             'left': '0000000100000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000100000081'},
 'op92-partial-word-bit31': {'op': 146,
                             'left': '0000008000000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000008000000081'},
 'op92-partial-word-bit32': {'op': 146,
                             'left': '0000000001000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000001000081'},
 'op92-partial-word-bit39': {'op': 146,
                             'left': '0000000080000081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000080000081'},
 'op92-partial-word-bit40': {'op': 146,
                             'left': '0000000000010081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000000010081'},
 'op92-partial-word-bit47': {'op': 146,
                             'left': '0000000000800081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000000800081'},
 'op92-partial-word-bit48': {'op': 146,
                             'left': '0000000000000181',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000000000181'},
 'op92-partial-word-bit54': {'op': 146,
                             'left': '0000000000004081',
                             'right': '23f1debc9a780681',
                             'initial': 16777215,
                             'fac': '0000000000004081'},
 'op92-exp-sum128-80000000000000': {'op': 146,
                                    'left': '0000000000000040',
                                    'right': '0000000000000040',
                                    'initial': 5,
                                    'fac': '0000000000000040'},
 'op92-exp-sum128-c0000000000000': {'op': 146,
                                    'left': '0000000000004040',
                                    'right': '0000000000004040',
                                    'initial': 5,
                                    'fac': '0000000000004040'},
 'op92-exp-sum129-80000000000000': {'op': 146,
                                    'left': '0000000000000040',
                                    'right': '0000000000000041',
                                    'initial': 5,
                                    'fac': '0000000000000040'},
 'op92-exp-sum129-c0000000000000': {'op': 146,
                                    'left': '0000000000004040',
                                    'right': '0000000000004041',
                                    'initial': 5,
                                    'fac': '0000000000004040'},
 'op92-exp-sum130-80000000000000': {'op': 146,
                                    'left': '0000000000000041',
                                    'right': '0000000000000041',
                                    'initial': 5,
                                    'fac': '0000000000000041'},
 'op92-exp-sum130-c0000000000000': {'op': 146,
                                    'left': '0000000000004041',
                                    'right': '0000000000004041',
                                    'initial': 5,
                                    'fac': '0000000000004041'},
 'op92-exp-sum255-80000000000000': {'op': 146,
                                    'left': '000000000000007f',
                                    'right': '0000000000000080',
                                    'initial': 5,
                                    'fac': '000000000000007f'},
 'op92-exp-sum255-c0000000000000': {'op': 146,
                                    'left': '000000000000407f',
                                    'right': '0000000000004080',
                                    'initial': 5,
                                    'fac': '000000000000407f'},
 'op92-exp-sum256-80000000000000': {'op': 146,
                                    'left': '0000000000000080',
                                    'right': '0000000000000080',
                                    'initial': 5,
                                    'fac': '0000000000000080'},
 'op92-exp-sum256-c0000000000000': {'op': 146,
                                    'left': '0000000000004080',
                                    'right': '0000000000004080',
                                    'initial': 5,
                                    'fac': '0000000000004080'},
 'op92-exp-sum257-80000000000000': {'op': 146,
                                    'left': '0000000000000080',
                                    'right': '0000000000000081',
                                    'initial': 5,
                                    'fac': '0000000000000080'},
 'op92-exp-sum257-c0000000000000': {'op': 146,
                                    'left': '0000000000004080',
                                    'right': '0000000000004081',
                                    'initial': 5,
                                    'fac': '0000000000004080'},
 'op92-exp-sum383-80000000000000': {'op': 146,
                                    'left': '00000000000000bf',
                                    'right': '00000000000000c0',
                                    'initial': 5,
                                    'fac': '00000000000000bf'},
 'op92-exp-sum383-c0000000000000': {'op': 146,
                                    'left': '00000000000040bf',
                                    'right': '00000000000040c0',
                                    'initial': 5,
                                    'fac': '00000000000040bf'},
 'op92-exp-sum384-80000000000000': {'op': 146,
                                    'left': '00000000000000c0',
                                    'right': '00000000000000c0',
                                    'initial': 5,
                                    'fac': '00000000000000c0'},
 'op92-exp-sum384-c0000000000000': {'op': 146,
                                    'left': '00000000000040c0',
                                    'right': '00000000000040c0',
                                    'initial': 5,
                                    'fac': '00000000000040c0'},
 'op92-sticky111--1': {'op': 146,
                       'left': '0100000000000081',
                       'right': 'ffffffffffff3f81',
                       'initial': 16777215,
                       'fac': '0100000000000081'},
 'op92-sticky111--1-negative': {'op': 146,
                                'left': '0100000000008081',
                                'right': 'ffffffffffff3f81',
                                'initial': 16777215,
                                'fac': '0100000000008081'},
 'op92-sticky111-1': {'op': 146,
                      'left': '0100000000000081',
                      'right': '0100000000004081',
                      'initial': 16777215,
                      'fac': '0100000000000081'},
 'op92-sticky111-1-negative': {'op': 146,
                               'left': '0100000000008081',
                               'right': '0100000000004081',
                               'initial': 16777215,
                               'fac': '0100000000008081'},
 'op92-sticky112--1': {'op': 146,
                       'left': '0b00000000004081',
                       'right': '5d74d145175d3481',
                       'initial': 16777215,
                       'fac': '0b00000000004081'},
 'op92-sticky112--1-negative': {'op': 146,
                                'left': '0b0000000000c081',
                                'right': '5d74d145175d3481',
                                'initial': 16777215,
                                'fac': '0b0000000000c081'},
 'op92-sticky112-1': {'op': 146,
                      'left': '0100000000004081',
                      'right': '0100000000004081',
                      'initial': 16777215,
                      'fac': '0100000000004081'},
 'op92-sticky112-1-negative': {'op': 146,
                               'left': '010000000000c081',
                               'right': '0100000000004081',
                               'initial': 16777215,
                               'fac': '010000000000c081'},
 'op90-both-zero': {'op': 144,
                    'left': '0000000000000000',
                    'right': '0000000000000000',
                    'initial': 5,
                    'fac': '5aa5d5c33c918092'},
 'op90-aliases': {'op': 144,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 5,
                  'fac': '5aa5d5c33c918092'},
 'op90-left-zero': {'op': 144,
                    'left': '123456789abcde00',
                    'right': '0000000000008081',
                    'initial': 5,
                    'fac': '5aa5d5c33c918092'},
 'op90-right-zero': {'op': 144,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 5,
                     'fac': '5aa5d5c33c918092'},
 'op90-max-zero': {'op': 144,
                   'left': 'ffffffffffff7fff',
                   'right': '123456789abcde00',
                   'initial': 5,
                   'fac': '5aa5d5c33c918092'},
 'op90-min-half': {'op': 144,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 5,
                   'fac': '5aa5d5c33c918092'},
 'op90-flush-before-round': {'op': 144,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 5,
                             'fac': '5aa5d5c33c918092'},
 'op90-negative-flush': {'op': 144,
                         'left': '0100000000008040',
                         'right': 'feffffffffff7f41',
                         'initial': 5,
                         'fac': '5aa5d5c33c918092'},
 'op90-fraction': {'op': 144,
                   'left': '0000000000004081',
                   'right': '0000000000004081',
                   'initial': 5,
                   'fac': '5aa5d5c33c918092'},
 'op90-tie111-1': {'op': 144,
                   'left': '0000000000004081',
                   'right': '0100000000000081',
                   'initial': 5,
                   'fac': '5aa5d5c33c918092'},
 'op90-tie112-6': {'op': 144,
                   'left': '0000000000004081',
                   'right': '0600000000004081',
                   'initial': 5,
                   'fac': '5aa5d5c33c918092'},
 'op90-round-overflow': {'op': 144,
                         'left': '01000000000000c0',
                         'right': 'feffffffffff7fc0',
                         'initial': 5,
                         'fac': '5aa5d5c33c918092'},
 'op90-max-two': {'op': 144,
                  'left': 'ffffffffffff7fff',
                  'right': '0000000000000082',
                  'initial': 5,
                  'fac': '5aa5d5c33c918092'},
 'op90-both-negative': {'op': 144,
                        'left': '0000000000008081',
                        'right': '0000000000008081',
                        'initial': 5,
                        'fac': '5aa5d5c33c918092'},
 'op90-raw-align': {'op': 144,
                    'left': 'cdab896745230181',
                    'right': '23f1debc9a780681',
                    'initial': 5,
                    'fac': '5aa5d5c33c918092'},
 'op90-raw-reversed': {'op': 144,
                       'left': '23f1debc9a780681',
                       'right': 'cdab896745230181',
                       'initial': 5,
                       'fac': '5aa5d5c33c918092'},
 'op90-sticky111--1': {'op': 144,
                       'left': '0100000000000081',
                       'right': 'ffffffffffff3f81',
                       'initial': 16777215,
                       'fac': '5aa5d5c33c918092'},
 'op90-sticky112-1': {'op': 144,
                      'left': '0100000000004081',
                      'right': '0100000000004081',
                      'initial': 16777215,
                      'fac': '5aa5d5c33c918092'},
 'op94-both-zero': {'op': 148,
                    'left': '0000000000000000',
                    'right': '0000000000000000',
                    'initial': 5,
                    'fac': '0000000000000000'},
 'op94-aliases': {'op': 148,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 5,
                  'fac': 'ffffffffffffff00'},
 'op94-left-zero': {'op': 148,
                    'left': '123456789abcde00',
                    'right': '0000000000008081',
                    'initial': 5,
                    'fac': '0000000000008081'},
 'op94-right-zero': {'op': 148,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 5,
                     'fac': '123456789abcde00'},
 'op94-max-zero': {'op': 148,
                   'left': 'ffffffffffff7fff',
                   'right': '123456789abcde00',
                   'initial': 5,
                   'fac': '123456789abcde00'},
 'op94-min-half': {'op': 148,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 5,
                   'fac': '0000000000000080'},
 'op94-flush-before-round': {'op': 148,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 5,
                             'fac': 'feffffffffff7f41'},
 'op94-negative-flush': {'op': 148,
                         'left': '0100000000008040',
                         'right': 'feffffffffff7f41',
                         'initial': 5,
                         'fac': 'feffffffffff7f41'},
 'op94-fraction': {'op': 148,
                   'left': '0000000000004081',
                   'right': '0000000000004081',
                   'initial': 5,
                   'fac': '0000000000004081'},
 'op94-tie111-1': {'op': 148,
                   'left': '0000000000004081',
                   'right': '0100000000000081',
                   'initial': 5,
                   'fac': '0100000000000081'},
 'op94-tie112-6': {'op': 148,
                   'left': '0000000000004081',
                   'right': '0600000000004081',
                   'initial': 5,
                   'fac': '0600000000004081'},
 'op94-round-overflow': {'op': 148,
                         'left': '01000000000000c0',
                         'right': 'feffffffffff7fc0',
                         'initial': 5,
                         'fac': 'feffffffffff7fc0'},
 'op94-max-two': {'op': 148,
                  'left': 'ffffffffffff7fff',
                  'right': '0000000000000082',
                  'initial': 5,
                  'fac': '0000000000000082'},
 'op94-both-negative': {'op': 148,
                        'left': '0000000000008081',
                        'right': '0000000000008081',
                        'initial': 5,
                        'fac': '0000000000008081'},
 'op94-raw-align': {'op': 148,
                    'left': 'cdab896745230181',
                    'right': '23f1debc9a780681',
                    'initial': 5,
                    'fac': '23f1debc9a780681'},
 'op94-raw-reversed': {'op': 148,
                       'left': '23f1debc9a780681',
                       'right': 'cdab896745230181',
                       'initial': 5,
                       'fac': 'cdab896745230181'},
 'op94-sticky111--1': {'op': 148,
                       'left': '0100000000000081',
                       'right': 'ffffffffffff3f81',
                       'initial': 16777215,
                       'fac': 'ffffffffffff3f81'},
 'op94-sticky112-1': {'op': 148,
                      'left': '0100000000004081',
                      'right': '0100000000004081',
                      'initial': 16777215,
                      'fac': '0100000000004081'},
 'fac0-aliases': {'op': 144,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 16777215,
                  'fac': '0000000000000000'},
 'fac0-right-zero': {'op': 144,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 16777215,
                     'fac': '0000000000000000'},
 'fac0-flush-before-round': {'op': 144,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 16777215,
                             'fac': '0000000000000000'},
 'fac0-min-half': {'op': 144,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 16777215,
                   'fac': '0000000000000000'},
 'fac1-aliases': {'op': 144,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 16777215,
                  'fac': '123456789abcde00'},
 'fac1-right-zero': {'op': 144,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 16777215,
                     'fac': '123456789abcde00'},
 'fac1-flush-before-round': {'op': 144,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 16777215,
                             'fac': '123456789abcde00'},
 'fac1-min-half': {'op': 144,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 16777215,
                   'fac': '123456789abcde00'},
 'fac2-aliases': {'op': 144,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 16777215,
                  'fac': '0100000000008001'},
 'fac2-right-zero': {'op': 144,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 16777215,
                     'fac': '0100000000008001'},
 'fac2-flush-before-round': {'op': 144,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 16777215,
                             'fac': '0100000000008001'},
 'fac2-min-half': {'op': 144,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 16777215,
                   'fac': '0100000000008001'},
 'fac3-aliases': {'op': 144,
                  'left': '123456789abcde00',
                  'right': 'ffffffffffffff00',
                  'initial': 16777215,
                  'fac': 'ffffffffffffffff'},
 'fac3-right-zero': {'op': 144,
                     'left': '0000000000000081',
                     'right': '123456789abcde00',
                     'initial': 16777215,
                     'fac': 'ffffffffffffffff'},
 'fac3-flush-before-round': {'op': 144,
                             'left': '0100000000000040',
                             'right': 'feffffffffff7f41',
                             'initial': 16777215,
                             'fac': 'ffffffffffffffff'},
 'fac3-min-half': {'op': 144,
                   'left': '0000000000000001',
                   'right': '0000000000000080',
                   'initial': 16777215,
                   'fac': 'ffffffffffffffff'}}

CASES={n:dict(c) for n,c in MATRIX.items()}
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(case):
    assert case['op'] in (0x90,0x92,0x94)
    def assign(at,raw):return b''.join(bytes.fromhex('c706')+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<'+'H'*(len(raw)//2),raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'DMP1')+output(0x1856,4)+output(0x234,4)
    inputs=assign(0x16,bytes.fromhex(case['fac']))+output(0x16,8)+assign(0x1860,bytes.fromhex(case['left']))+output(0x1860,8)+assign(0x1868,bytes.fromhex(case['right']))+output(0x1868,8)+output(0x1f,1)
    call=bytes.fromhex('be6018')+(bytes.fromhex('bf6818') if case['op'] in (0x90,0x92) else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=output(0x16,8)+output(0x1860,8)+output(0x1868,8)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+inputs+call+suffix


def decode(raw):
    from fractions import Fraction
    if not raw[7]:return Fraction(0)
    value=((int.from_bytes(raw[:7],'little')&((1<<55)-1))|(1<<55))*Fraction(2)**(raw[7]-184)
    return -value if raw[6]&128 else value


def expected_entry(left,right,fac):
    from fractions import Fraction
    if not left[7] or not right[7]:return fac[:7]+b'\x00'
    value=decode(left)*decode(right)
    if abs(value)<Fraction(2)**-128:return fac[:7]+b'\x00' # native pre-round underflow
    negative=value<0;value=abs(value)
    power=value.numerator.bit_length()-value.denominator.bit_length()
    if value<Fraction(2)**power:power-=1
    exponent=power+129
    if exponent>255:return None
    scaled=value*Fraction(2)**(55-power);mantissa,rest=divmod(scaled.numerator,scaled.denominator)
    if rest*2>scaled.denominator or(rest*2==scaled.denominator and mantissa%2):mantissa+=1
    if mantissa==1<<56:mantissa>>=1;exponent+=1
    if exponent>255:return None
    bits=(mantissa&((1<<55)-1))|((1<<55) if negative else 0)
    return bits.to_bytes(7,'little')+bytes([exponent])


def error_address(case):
    p=expected_payload(case);call=bytes([0xcd,0x3f,case['op'],0x90,0x90]);assert p.count(call)==1
    return f'{0x6d+p.index(call)+5:04X}'


def verify_trace(trace,case):
    left=bytes.fromhex(case['left']);right=bytes.fromhex(case['right']);fac=bytes.fromhex(case['fac'])
    assert case['op'] in (0x90,0x92,0x94),'only qualified direct entry forms'
    if case['op']==0x94:assert fac==right,'entry94 right operand is the initial FAC, not the memory shadow'
    if case['op']==0x92:assert fac==left,'entry92 left operand is the initial FAC, not the memory shadow'
    prefix=b'DMP1'+struct.pack('<I',case['initial'])+fac+left+right+b'\x00'
    assert trace[:33]==prefix,'exact initial FAC, ordered operands, RNG and mode'
    want=expected_entry(left,right,fac)
    if want is None:
        address=error_address(case)
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'exact entry-specific native overflow without fabricated state'
    else:
        assert len(trace)==66 and trace[-4:]==b'END!','complete entry-state return frame'
        assert trace[33:41]==want,'exact result and prior-FAC residue'
        assert trace[41:49]==left and trace[49:57]==right,'both memory blocks preserved (left/right shadows for entry92/94 respectively)'
        assert trace[57:61]==struct.pack('<I',case['initial']) and trace[61]==0,'unrelated RNG and mode preserved'
    return want


def verify_static(runtime):
    import verify_add_double as addition
    from verify_rng_native import image
    addition.verify_static(runtime) # retained ABI, normalizer, zero and error source
    code=image(runtime)
    for name,at,length,digest in SOURCE_PACKETS:
        raw=(ROOT/'research/yt-mbf-multiply-double/rea'/name).read_bytes();assert SHA(raw)==digest,'fixed source packet'
        p=json.loads(raw);assert p['ok'] is True;e=p['data'];n=e['normalized_result']
        assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA
        assert e['parameters']==dict(address=hex(0x10000+at),length=length)
        assert n['address']==hex(0x10000+at) and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==length
        assert bytes.fromhex(n['bytes_hex'])==code[at:at+length],'complete original mapped source'
    assert [struct.unpack_from('<H',runtime,0x58d+2*op)[0]for op in (0x90,0x92,0x94)]==[0xaf46,0xaf3b,0xaf43]
    assert code[0xaf3b:0xaf49]==bytes.fromhex('be1600eb06e8806fbf1600e82270'),'direct FAC/ABI mappings'
    assert code[0xaf67:0xaf6f]==bytes.fromhex('e82201740380ca01'),'full helper call and sticky result'
    assert code[0xb1c9:0xb1ce]==bytes.fromhex('5a5e0bf6c3'),'complete helper return and lower-product residue'
    return verify_inventory()

def verify_inventory():
    import re
    raw=(ROOT/'research/yt-mbf-multiply-double/maintenance-calls.json').read_bytes();assert SHA(raw)==INVENTORY_SHA
    d=json.loads(raw);r=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert d['format']=='maintenance-direct-double-multiply-callers-v1'
    assert d['authority']=='Static annotated call-site inventory matched to archived bytes; not observed execution or exhaustive indirect coverage.'
    assert SHA(r)==d['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
    assert SHA(listing)==d['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    calls=[]
    for address,op in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_(90|92|94)\s*\n',listing.decode()):
        off=int(address,16);v=int(op,16);assert r[512+off:512+off+5]==bytes([0xcd,0x3f,v,0x90,0x90]);calls.append(dict(op=v,code_offset=off,file_offset=512+off))
    assert calls==d['direct_calls'] and len(calls)==5 and all(c['op']==0x92 for c in calls)
    assert not re.search(r'QB_3f_96\b',listing.decode()) and d['excluded_inline_calls']==[]
    return calls,[]


def verify_corpus(directory,cases,pins_sha,recipe_id,source_name):
    root=Path(directory); manifest=(root/'pins.json').read_bytes(); assert SHA(manifest)==pins_sha,'fixed native manifest'
    pins=json.loads(manifest)['files']
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete artifact inventory'
    for name,digest in pins.items(): assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert (SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original executable identity'
    verify_static(runtime)
    source=root/'sources'/source_name; recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe=recipe_id,cases=cases,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'frozen prelaunch acquisition source and recipe'
    assert {p.name for p in root.iterdir()}==set(cases)|{'pins.json','recipe.json','sources'} and {p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,case in cases.items():
        folder=root/name; meta=json.loads((folder/'result.json').read_text()); stub=expected_payload(case)
        patched=bytearray(original); assert patched[0x23a:0x23f]==bytes.fromhex('cd3d439090'); patched[0x23a:0x23f]=bytes.fromhex('e930009090'); patched[0x26d:0x26d+len(stub)]=stub
        table=struct.unpack_from('<H',original,24)[0]
        for index in range(struct.unpack_from('<H',original,6)[0]):
            offset,segment=struct.unpack_from('<HH',original,table+4*index);at=16*segment+offset
            assert all(not(at<end and at+2>start) for start,end in ((0x3a,0x3f),(0x6d,0x6d+len(stub)))),'no loader relocation overlaps the diagnostic'
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        assert set(meta)=={'recipe','case','op','left','right','initial','fac','exit_code','timeout','missing','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'fixed result schema'
        assert {k:meta[k] for k in case}==case and meta['recipe']==recipe['recipe'] and meta['case']==name,'declared actual case'
        assert meta['exit_code']==0 and meta['timeout'] is False and meta['missing']==[],'normal emulator completion with all outcomes retained'
        assert meta['payload_hex']==stub.hex() and meta['copied_initializer_sha256']==SHA(patched) and meta['copied_runtime_sha256']==SHA(copied),'full copied image reconstruction'
        assert set(meta['files'])==FILES and {p.name for p in folder.iterdir()}==FILES|{'result.json'},'exact case inventory'
        for file,digest in meta['files'].items(): assert SHA((folder/file).read_bytes())==digest,'captured case digest'
        commands=(folder/'COMMANDS.TXT').read_text().splitlines()
        assert len(commands)==11 and commands[0].startswith(('mount c /tmp/','mount c /private/tmp/')) and Path(commands[0][8:]).name==name,'disposable case mount'
        assert commands[1:]==['c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit'],'complete actual commands'
        argv=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)]
        assert json.loads((folder/'launch.json').read_text())==argv,'pinned actual launch'
        messages=[line.split(' | ',1)[1] for line in (folder/'dosbox.stderr').read_text().splitlines() if ' | ' in line]
        assert [shlex.split(m[11:]) for m in messages if m.startswith('arguments: ')]==[argv] and messages.count('dosbox-staging version 0.83.0 ()')==1,'actual host/version'
        assert 'SDL: dummy video initialised' in messages and "MIXER: Sound output disabled ('nosound' mode)" in messages and any(m.startswith('CPU: Setting fixed 200000 cycles.') for m in messages),'fixed headless host controls'
        assert (folder/'dosbox.stdout').read_bytes()==b'' and (folder/'ERROR.LOG').read_bytes()==b'' and (folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n' and (folder/'RETURN.LOG').read_bytes()==b'PROBE_RETURNED\r\n','native shell return; ERRORLEVEL alone does not prove conversion success'
        assert read_date((folder/'DOSDATE.LOG').read_bytes()).isoformat()=='2026-11-02' and abs(read_time((folder/'DOSTIME.LOG').read_bytes()))<=.1,'raw date/time controls'
        trace=(folder/'TRACE.BIN').read_bytes(); want=verify_trace(trace,case)
        portable.append(dict(name=name,**case,output=want.hex() if want is not None else None,trace_hex=trace.hex(),source_trace_sha256=SHA(trace)))
    return portable


def verify(directory=DEFAULT,fixture=FIXTURE):
    rows=verify_corpus(directory,CASES,PINS_SHA,'brun30-multiply-double-entry-state-v1','recover_multiply_double.py')
    doc=dict(format='qb-native-multiply-double-v1',cases=rows)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals complete native corpus'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['cases']),'DOUBLE multiplication controls;',sum(c['output'] is None for c in d['cases']),'exact native Overflows')
