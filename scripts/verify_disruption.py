"""Independently verify original-DOS disruption and black-hole arrival evidence."""
import argparse
import gzip
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='disruption-arrival-v1'
BASE_SHA='2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19'
# Freeze only after the final returned corpus has been independently inspected.
RECIPE_SHA='4470aad136b6e231e0980b7382dd119e31f17fa5ee53555987081ee629cdc057'
WORLD_SHA={'quiet-origin': '7bbbc818bc61f9efcfbec17c9712e8c4b1ae7e8ddb4f9e8a57f87f84b5d12d47',
 'ordinary-arrival': '4744d89733c15c82452a8f9e5900fb5ad27b33f7cb2131572594581ace46ee9f',
 'startup-arrival': 'e14337b498c5263d4777546a65ffebe73d00c39552c77c929eb6e76e1215cd73',
 'upper-safe': 'a65e317bad0e8b398579882521ef8319216fa709ce71d4a222508ca05f60b724',
 'upper-raw-133': '2175856d5bd94009ab0653a4e2c7bbf03ad344f880cf37aa25e3ebff4cdccd40',
 'scanner-decline': '8e8462ee7c5d64ee5aff230710f547d9aa295f5f9218629a7c487fa956a87b17',
 'scanner-accept': 'cca81bdb97481feee64c09ce5bdf41bd7000b66f363b3b1e7dadf351a5b9bceb',
 'arrival-zero-turns': '6b8e1932e6f7da93ec71432237a5717678f363b0eb618e31c155b65c769c6303',
 'startup-zero-turns': 'b90629bbd3422f4072d6568ec42a01e32202d4fdee096f2e7e44a81366057948',
 'startup-low-turns': '707305b2ba44b987b0cd41f70b3bd0b77bc2c19704105517124c75ec3a551fbc',
 'startup-cloak-zero': '309b366ce2c42f8edbd250d28c9449f04de79653836253617a373758c277981c',
 'startup-cloak-fraction': 'b6d4a200e2edfa40c8cf5c9ca3c918f8f976ec287897fc988a7f97614356b8e5',
 'startup-hole-mines': 'a061b75b663f57b14c08eeeffebd6eb8e440b493fbad1bbca976aa5174b5411e',
 'startup-hole-fighters': '36b222721c5390e98d654738b7b1a7350c8f62af73a83ff7884006dc153545b8',
 'startup-hole-both': '2d9b2290c0bbb0a94b9fcf55a6f4a90ca1440067560666e1e3db1b8ec6da0e94',
 'startup-landing-mines': '0f86a132b450c7076cc85d8cacaad3a90bea69d74a5e649514f45a426851ee7c',
 'startup-landing-fighters': '9332864789a98c85f13dfffc20d07d402659ced729ffeac5ad5b330462e23270',
 'startup-landing-both': '7a0e9616edc3aea7aa5b2d25331476b55b987b76ac8a840873087a8b876cd493',
 'startup-landing-lethal': '8355db322749f4caaf774cb49485ec766fb8bf23a739eae71706b14a7aa1da4f',
 'ordinary-hole-both': 'ed8dd2947424dbe60b1042345dd9573fa5ce6249c916f316833c7c4e79f3c1b3',
 'scanner-combined-decline': 'edb8640cbcda9e91a0db39a8cde288ca90f45cee98e1a3d3eca399d81f3407fd',
 'scanner-combined-accept': '42099971a5dbe404abf8257ac709b1eebc134666248ad027b46d17bddafc83a2',
 'autopilot': '6d5053a26d1b12c9d6d6ff5274220c8e480f6f340cd493485fb2f779fff6c2c0',
 'autopilot-scanner-decline': '8e8462ee7c5d64ee5aff230710f547d9aa295f5f9218629a7c487fa956a87b17',
 'autopilot-scanner-accept': 'b3c5c411f07179bc0e543dd48420239efb42f184f444edeb89655b21802e47b1',
 'manual-warp': 'c06f404d8e442b12a232ad5adf01956108d5dfa3117d00442ba1241fa947a967',
 'thruster-final': '27971a060e9a48cf4005780eb32ce8442bc22ace707c10f5e8462c32abd55d81',
 'thruster-intermediate': 'd743759008ecdc1d625d2fef452a5fd2d9168a99ca30c10069ca01dc4e5fbbd9',
 'thruster-intermediate-mines': '18248123b2cbf194b97fbe41652a70167658ed34c2ae1dc3a725c55af60f9a6a',
 'thruster-intermediate-fighters': '0ae9f391b709ce7f61993c682a6627394dd26588618dcf2f4b875bd4f4f9b299',
 'thruster-final-collision': 'ea4468980ca77056c99f5a50f0c4614a65f48aa8430e2d5e802a95e131737e5f',
 'thruster-ten-turns': 'b37e918085b428d55dcb66444c5882db175a581831cf728bc871f42680d498cb',
 'thruster-cancel': 'a5e822f79a02b23350191d39c334dbd0017d722d844f2ccd634d3be8164bee98',
 'wanderer-final': 'd08ba2831037029bf0ee3c95bdb654f67a204652fe66106320f5fb5540df71d4',
 'wanderer-clock-0001': 'c7debfb406c0f970d22cd234c2babab7378a2205eaca9bad542dcd477e486bc9',
 'wanderer-clock-0100': 'b5d400ed95c5e6834ac3480e7d929970696fd4f039c51ae70fa974037e586302',
 'wanderer-clock-0200': '09d8cc05d634ec164087241a63a43b5d5db2ebaca5df9a8188cda0d5a46c3c22',
 'wanderer-clock-0300': '66458e929517e30fa465545e100d23ee01670004ee8baf7b98801cb828c1278a',
 'two-sector-arrival': 'b88d95c958c8feefa1f8b742d418a0b9d1adb8cf503e76ccef42855a000fd249',
 'startup-clock-01': 'de2c60f1ac559c0a9cda11d4aafff0b072e00dc063ff0bec0752e0e7a08f1385',
 'startup-clock-02': 'f35c66ee16e65b7d572b684b992906aa2f17f260fa96f562ad725a6539ca0d02',
 'startup-clock-03': '84ff5141a116a36375518d7b15df39e88ddfbeec497cf5ad789b06da16933043',
 'eight-sector-sensors': 'f78d65ac1d4e36e58ab7bb89ac4e8d61a649c9fc1acb7ea4758eb10e8c1d9d5d',
 'eight-sector-arrival-3': '8d7470613f1d7e2add52c7e39edc63a05b0f16aeab8cfe36400d64b70a6b361e',
 'eight-sector-arrival-4': '8d7470613f1d7e2add52c7e39edc63a05b0f16aeab8cfe36400d64b70a6b361e',
 'normal-width-origin': '4108c466e4ce891d3892945d705d6afe1e62e68355d85738c33f33027f7cad28',
 'normal-width-adjacent': '16a6a6e5177dd048390de31be87ef8bffafc57209d151eac883f2a25af389c63',
 'normal-width-thruster': 'a831a945636a7c2bd61b9cb67b326e9a46079aabcb96360210758ae1e801e2f1',
 'normal-width-sensors': 'afe860817d6f21f3ef20c7d82519691747fdf5bb7501e308c595307dd89e8aba',
 'normal-width-sensors-repeat': 'afe860817d6f21f3ef20c7d82519691747fdf5bb7501e308c595307dd89e8aba',
 'normal-width-arrival-592': '6442a7c8118cdafbaef23320d5c57f7157c0eedb7fe76a46762d75d1c8de563a',
 'normal-width-arrival-1051': '6442a7c8118cdafbaef23320d5c57f7157c0eedb7fe76a46762d75d1c8de563a',
 'normal-width-thruster-hole': 'fe31d4e2c7b827f0ade86bbba5e59a9b09268b5d9bdda3ed1690fe1efd055bad',
 'normal-width-wanderer-hole': 'f559c97192bba422d1e08d3a29053a303a6a215194a76db30508b54e3f6b8fc5',
 'normal-width-startup-hole': 'c8dbdd20a1b3dcbdaa5725429a72364ff128b120efd974825ee20a20ed02661c',
 'normal-width-upper-safe': '219616564ed8619972cb3a6395a9a441ca6dafa1fa919adda22d8b1645fe4d13',
 'normal-width-earth-safe': 'cb3943caf1233e4a5c36dd3b2580ac8b464d2e7bfd41ea14d36c80a5b1a9ae34',
 'normal-width-reconnect': 'afe860817d6f21f3ef20c7d82519691747fdf5bb7501e308c595307dd89e8aba',
 'ordinary-reconnect': '4744d89733c15c82452a8f9e5900fb5ad27b33f7cb2131572594581ace46ee9f',
 'wanderer-reconnect': 'af9a207b335eb72c91eac44a26d6edeff0f043e7807499dca44ccd1f7f063ab0',
 'eight-sector-reconnect': 'f78d65ac1d4e36e58ab7bb89ac4e8d61a649c9fc1acb7ea4758eb10e8c1d9d5d'}
AUX_SHA={'quiet-origin': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'ordinary-arrival': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'startup-arrival': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'upper-safe': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'upper-raw-133': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'scanner-decline': '3d742df7d5b8bd4213dd63e1b1aa2fc83909c635e2125ee05545f6fa326643e7',
 'scanner-accept': '2ffe830c992f6462e73934b6e0c89dcbba99f8212f1c6ab612ff616fb293bcb6',
 'arrival-zero-turns': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'startup-zero-turns': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'startup-low-turns': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'startup-cloak-zero': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'startup-cloak-fraction': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'startup-hole-mines': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'startup-hole-fighters': '467e51f73718a0a57a9db6f7537ef8125903c3e97a1fff3b31c235bf759a07e6',
 'startup-hole-both': '467e51f73718a0a57a9db6f7537ef8125903c3e97a1fff3b31c235bf759a07e6',
 'startup-landing-mines': 'aecac3fc3546295d5a905f5d59d742ae6f18813dc13239a5e53cf66c0f231339',
 'startup-landing-fighters': '467e51f73718a0a57a9db6f7537ef8125903c3e97a1fff3b31c235bf759a07e6',
 'startup-landing-both': '3161f492ddaeb7315cf01710ea90c3c104612f5395231f489d2dd6faf94f7ae6',
 'startup-landing-lethal': '23cf6938eafba5251ad9ebb615d6b2de7ff113b448781b3a0d8efafa7cc80644',
 'ordinary-hole-both': 'b0c23db10675c4152529e615872f1cd94e8c088897cb463cebd910aa0b45b218',
 'scanner-combined-decline': '3161a2b4cb94b7f8bea48057c624babdc93399ed94825b747dfae91f5325a5e5',
 'scanner-combined-accept': '6b15262d5435ec9946e0b32780876a55a350738492977fa9700193da738e119c',
 'autopilot': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'autopilot-scanner-decline': 'c55f8986de0cf6958990f1a76fb56e18a9c20099f2c51b307f9e8b8dce8a7220',
 'autopilot-scanner-accept': 'c55f8986de0cf6958990f1a76fb56e18a9c20099f2c51b307f9e8b8dce8a7220',
 'manual-warp': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'thruster-final': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'thruster-intermediate': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'thruster-intermediate-mines': '8cceb78f5bfd411ae68de3db39821ead75729bf09e678da1c6ebff7fef0cdaf9',
 'thruster-intermediate-fighters': '8c35acadbfbbd12e9c7f98ff912310e6d9d860422f7133e4906a8846e544691a',
 'thruster-final-collision': '0f67405ce547adbf0f8c339250485da564809128737241603959a326e84bf4df',
 'thruster-ten-turns': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'thruster-cancel': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'wanderer-final': '8cceb78f5bfd411ae68de3db39821ead75729bf09e678da1c6ebff7fef0cdaf9',
 'wanderer-clock-0001': '74367d4d703411db056ec427353538c14ce2926aaba2342d7b658c1f93e6b9f9',
 'wanderer-clock-0100': 'aa5113cba65afa941804dbce5321b6b38160eb9d7f9bc6a6015c6f68631e8b62',
 'wanderer-clock-0200': '0c8ab9521ccc08ee3e3106e320c8c59b81b362e669c32d49089cb824943840d7',
 'wanderer-clock-0300': 'f5740be4a97d26187ea7b09da2251ee1245e6fc54d3570c05022998cb9a51f1e',
 'two-sector-arrival': '5f38318b07261616cc3f045d61de4bdbd047c23cc725257ee45d48c97eff9bc0',
 'startup-clock-01': '035869488d6c9a2fcecd1abfb62778f934973a7f84a27053edb66c74597b5bc5',
 'startup-clock-02': '0f9321fa28a84fea9f98f21afa24d5763defa494c79331cbdbe9af47f2a25c42',
 'startup-clock-03': '81ad9fc06e2702c9d84b2090749719c363448dc16dd1ff3c6c9af91213fdaf46',
 'eight-sector-sensors': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'eight-sector-arrival-3': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'eight-sector-arrival-4': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'normal-width-origin': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-adjacent': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-thruster': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'normal-width-sensors': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-sensors-repeat': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-arrival-592': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'normal-width-arrival-1051': '888bae0372edd1dfdba213a7859170e90ed7f76dca70277d88b02522f3a60fc2',
 'normal-width-thruster-hole': '8cceb78f5bfd411ae68de3db39821ead75729bf09e678da1c6ebff7fef0cdaf9',
 'normal-width-wanderer-hole': '922f3cdc6c8bc1d2ba302a1320a213776e560cb0bb4359cbc930bc9729aa34c5',
 'normal-width-startup-hole': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-upper-safe': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-earth-safe': '0f1fced864db47164c27f8eae820292f6abc965f1124ef196b6c4a3d8d5a5c2a',
 'normal-width-reconnect': '313de7e9076d25413caa357e2cec9e0d66e1fea7f1a8cbca12c63f81d6793b15',
 'ordinary-reconnect': '313de7e9076d25413caa357e2cec9e0d66e1fea7f1a8cbca12c63f81d6793b15',
 'wanderer-reconnect': '313de7e9076d25413caa357e2cec9e0d66e1fea7f1a8cbca12c63f81d6793b15',
 'eight-sector-reconnect': 'd3eaed6843a5bfaf84c912af506cfdac8ca261769a6cc24796a01b9a0ac97b20'}
TRANSCRIPT_SHA={'quiet-origin': '16598eb57aea15dce81561c97d5378a7ab04306fb630e6ea4f461c6cfef99040',
 'ordinary-arrival': '0c78ba65f442edda1be0aeb5331f6002e46cda31d628b63a4214711a915362bb',
 'startup-arrival': '448792ae110cd99a2c3201faf11a6e59ce84e9a003ebdbaf3ee33cedf668c0a9',
 'upper-safe': '4e746ddd8d8c052dceebd9c8077e7042d40d5567a7012f3a4107717513c31d40',
 'upper-raw-133': '4e746ddd8d8c052dceebd9c8077e7042d40d5567a7012f3a4107717513c31d40',
 'scanner-decline': '57f84b1f338a52be8a5bea68afde1873f4778f98d923499724f499daa93e4038',
 'scanner-accept': '87ae26a04cf3e9fba4ca7da8e85f317bf9f9199a167439601d5fd8bb2322f785',
 'arrival-zero-turns': 'c295fc2ddf35a4a7355ad4db0944a92e1bcb2d55b05b4d31c0f2c183b47200f7',
 'startup-zero-turns': '76f01cc8e7e20dbd842870681219c45fc6954349cd01042c083a741326df2189',
 'startup-low-turns': '069a1579e7a8dbc9a38e6c2f4979e0cca66e1136db505b1063776f0ab2c5a9f0',
 'startup-cloak-zero': '4f159cd0fd1a5c8c084eeb3d3d540d0f9ef262b5321353fa37fad2f35c9cc3da',
 'startup-cloak-fraction': 'a87155da704972665fdda0b299d58a140a2c99daa9d68d4b0ae8eab82a097b91',
 'startup-hole-mines': 'aa7ab7216875b831d6ac6f91bb54b17d73f1e3f402d6f647e0e2b499fd1198f2',
 'startup-hole-fighters': '8e846026d6115fbb9e0e175dcdad76454305d6d032180dfd859b9d518696a494',
 'startup-hole-both': '958fb08e1632177dd6aa8a656071a5d0eda5aac5306b999a464fe1604756e4bb',
 'startup-landing-mines': 'e0fe667d6919b0eb36040a3b67c548b73084b95c204d7484a9bdb55933303771',
 'startup-landing-fighters': 'c92b6bed57c4f3094d73d288dd52f57163c9b4306498be7dd4eec7d4373fccca',
 'startup-landing-both': 'f1f3b572959e20a7862d4e6e90391d126444fece2204d6ac125d81a981020768',
 'startup-landing-lethal': 'e3a05cc102925cddf536c3dccdb2a37813f8ea9ccc778a6cb291e22952cb9f95',
 'ordinary-hole-both': '79c857b41ae7dcf7e35c253a3438995723137df5ae1189bc0f0c3b785753984e',
 'scanner-combined-decline': '8051e8adbecd03f102d759b60b666d617ab6bbfd60993aa1615cd4c23d78bece',
 'scanner-combined-accept': '6b4c6d47c8666f8c935d6bab0a2a15250f98d55b445e4122c6c07730ec74b7de',
 'autopilot': '803252c8bc42385a0c6f39fadff53e5f59dca597f7d1fde2f47166023c24db0e',
 'autopilot-scanner-decline': 'b0a2da0ff0dc9811992949abdcead676948122d602977ea61676d7fc6fb96ae3',
 'autopilot-scanner-accept': '242a84d19bb86590effb668d0a4c9659526408289076f7d5180e0ce64924bfcb',
 'manual-warp': 'b1dcc36845401997e330300b50f4003a9e628c7e8b1487b1ff1917ee3bc1564c',
 'thruster-final': '53113950271a261d323a80177c7839e9b7dae415e0f2c9fae33e7c231d67fef8',
 'thruster-intermediate': 'cbd6db5b2520460fa366588a0851f4179d2817049c3b15c1f85181990cc645d0',
 'thruster-intermediate-mines': 'dc2868aee5f6b050b178c25264f42c1d1a58891cd078bca0f078c296a63c5ea2',
 'thruster-intermediate-fighters': '4bd9fc9c2adbeb2e10e39dd687f0bbdfac38d595e00e720fdb9329fce5682587',
 'thruster-final-collision': '907380335c0b991c01d735311408313938ff9a518eb6d9f90ab31a47742e0132',
 'thruster-ten-turns': 'b5ce6145ea4f2f90b5c2556e41c206d8cf7989d182d486214bea98829c4f6292',
 'thruster-cancel': 'fdc543cc45acf94d034442503b84c2ce7f03aad12dbf12c66313f49f377321b9',
 'wanderer-final': 'bb52e4694990f31862367a3ad82a83cbd20620affd359bb5c1e078190d03c9d6',
 'wanderer-clock-0001': 'dccd303aaea8b26a1c2e7cb6b7c0e8c16d6858beb03cf66c185309d665e9bdb9',
 'wanderer-clock-0100': '3605c343c3bd2d6aae9ea4ecb92d207e1511df5cba1297ad5905397ba0955ea6',
 'wanderer-clock-0200': 'a10fd3a2fd32cf669cd6aff11268c177377240b16747b6be4af08188c1eab1fe',
 'wanderer-clock-0300': 'ce19b8a6d6ff67b1e48a8526286c9444a16569d7d5094e45dd485df765197e9d',
 'two-sector-arrival': '9de797c4c4743cd33f3d0d9ec68b3d63e3a86048c3bf26e9ef335e9e42b5902c',
 'startup-clock-01': 'ca5df6cbf5ad47d87a19e593b7d31302d38182a54dcc7090a2b17f38e2dd9a76',
 'startup-clock-02': '087c822cc608cda96c9765dee5cbbbcefd922070c5da0b2e09333d04ea614859',
 'startup-clock-03': 'b012fe32fece5f7ad4160e8e54f944b9cf8a4dd45c9788c1a15f42f79fd63245',
 'eight-sector-sensors': 'a678dff51bb65fd53f4f7737304f3cb0b7be5ca291e4678ed89f9bef547c55bc',
 'eight-sector-arrival-3': '615ad1a7a21161956bcfd532ec7f19a120629a39905f56dc1e0be1bd9cdf09bf',
 'eight-sector-arrival-4': '93db6dc577920fca714fc3e7ae9b60193a41f0508eada0b72855787704016b1a',
 'normal-width-origin': '5eaa3f9f4deafe37cb6fec7691a62fbe7edd6df94aefc54be74ea56801fee02e',
 'normal-width-adjacent': '5e9e97c6db4edbfed6babd383bfed3dac4af8d18fc8a9d0d192f143b2cb89b1e',
 'normal-width-thruster': 'fedd0459b7617b2de6d2754bd8f3358f2a63c31dbd3d89ea8e217703571cc316',
 'normal-width-sensors': '73e2813bc215f7a6158ef9ae934464aea077167276e5e84b358415223162836e',
 'normal-width-sensors-repeat': 'cf0795183b238c29cbbf0c3ed6f2303c9569cd2977267d393447e2be3fb25c7e',
 'normal-width-arrival-592': '67bc216a542b9c65097bd9c83cea6b0b63cfdaa0b490d94afd6f9248bf0a2fcf',
 'normal-width-arrival-1051': '14a8e7d712cf07b3273ae5b319b779f4da53e3e9f2c660a9b492b99ff966d20e',
 'normal-width-thruster-hole': 'fa246d04cb9d8751c679d878a1bf0e219cf7486bba30ee8c61f2997e69d53e10',
 'normal-width-wanderer-hole': '81e4546fa04b8e63f403513aab3f9de9c031cf6dff248c8d402ebb866410d7e3',
 'normal-width-startup-hole': '054476c9299895cf9fad362aae768f3b2f50e3eb01000676f7a16996446fcbda',
 'normal-width-upper-safe': '51ab16d253ac3e07d3f28e9a1ab73911429e3d51176e07d433c149c07b91745b',
 'normal-width-earth-safe': '16598eb57aea15dce81561c97d5378a7ab04306fb630e6ea4f461c6cfef99040',
 'normal-width-reconnect': 'cb652549079b9f0ec3dc004c021744791337bfa6e42550c96c3bd1636561e70f',
 'ordinary-reconnect': 'b823fc544dd354857b0043b7811f2e8ec098fce3c09e6e5208179890a2c4f071',
 'wanderer-reconnect': 'f41b4108b3f1075ba668a1d401d2ef67cb4170b93ee6bbf56610ae6247a23dcd',
 'eight-sector-reconnect': '705281c2f5956734be4f56c71e78203806f83eabcbde129ddc73131a202fe9af'}
FOOTPRINT={'quiet-origin': [0, 0, 1, 500, []],
 'ordinary-arrival': [2, 2, 3, 373, []],
 'startup-arrival': [1, 1, 3, 442, []],
 'upper-safe': [0, 0, 3, 500, []],
 'upper-raw-133': [0, 0, 3, 500, []],
 'scanner-decline': [0, 0, 1, 500, []],
 'scanner-accept': [2, 2, 3, 373, []],
 'arrival-zero-turns': [2, 2, 3, 0, []],
 'startup-zero-turns': [1, 1, 3, 0, []],
 'startup-low-turns': [1, 1, 3, 0, []],
 'startup-cloak-zero': [1, 1, 3, 442, []],
 'startup-cloak-fraction': [1, 1, 3, 442, []],
 'startup-hole-mines': [1, 1, 3, 442, []],
 'startup-hole-fighters': [1, 1, 3, 442, []],
 'startup-hole-both': [1, 1, 3, 442, []],
 'startup-landing-mines': [1, 1, 3, 442, []],
 'startup-landing-fighters': [1, 1, 3, 442, []],
 'startup-landing-both': [1, 1, 3, 442, []],
 'startup-landing-lethal': [1, 2, 0, 386, []],
 'ordinary-hole-both': [2, 2, 3, 373, []],
 'scanner-combined-decline': [0, 0, 1, 500, []],
 'scanner-combined-accept': [2, 2, 3, 373, []],
 'autopilot': [1, 1, 1, 444, []],
 'autopilot-scanner-decline': [0, 0, 1, 500, []],
 'autopilot-scanner-accept': [1, 1, 1, 444, []],
 'manual-warp': [1, 2, 3, 375, []],
 'thruster-final': [1, 1, 1, 435, [2]],
 'thruster-intermediate': [0, 0, 3, 480, [3]],
 'thruster-intermediate-mines': [1, 1, 1, 435, [2]],
 'thruster-intermediate-fighters': [1, 1, 1, 435, [2]],
 'thruster-final-collision': [0, 0, 1, 500, []],
 'thruster-ten-turns': [1, 1, 1, 0, [2]],
 'thruster-cancel': [0, 0, 1, 500, [1]],
 'wanderer-final': [1, 1, 1, 400, [1]],
 'wanderer-clock-0001': [1, 1, 3, 385, [1]],
 'wanderer-clock-0100': [1, 1, 1, 431, [1]],
 'wanderer-clock-0200': [1, 1, 1, 0, [3]],
 'wanderer-clock-0300': [1, 1, 3, 413, [1]],
 'two-sector-arrival': [3, 3, 1, 262, []],
 'startup-clock-01': [1, 1, 1, 497, []],
 'startup-clock-02': [2, 2, 3, 298, []],
 'startup-clock-03': [1, 1, 1, 440, []],
 'eight-sector-sensors': [0, 0, 8, 500, []],
 'eight-sector-arrival-3': [1, 1, 6, 407, []],
 'eight-sector-arrival-4': [1, 1, 6, 407, []],
 'normal-width-origin': [0, 0, 100, 500, []],
 'normal-width-adjacent': [0, 0, 101, 499, []],
 'normal-width-thruster': [0, 0, 101, 490, [101]],
 'normal-width-sensors': [0, 0, 3000, 500, []],
 'normal-width-sensors-repeat': [0, 0, 3000, 500, []],
 'normal-width-arrival-592': [1, 1, 1981, 407, []],
 'normal-width-arrival-1051': [1, 1, 1981, 407, []],
 'normal-width-thruster-hole': [1, 1, 1981, 398, [592]],
 'normal-width-wanderer-hole': [1, 1, 1810, 435, [2368]],
 'normal-width-startup-hole': [1, 1, 2665, 442, []],
 'normal-width-upper-safe': [0, 0, 3000, 500, []],
 'normal-width-earth-safe': [0, 0, 1, 500, []],
 'normal-width-reconnect': [0, 0, 3000, 500, []],
 'ordinary-reconnect': [0, 0, 3, 373, []],
 'wanderer-reconnect': [0, 0, 1, 400, []],
 'eight-sector-reconnect': [0, 0, 8, 500, []]}
DIAGNOSTIC_SHA={'recipe': '1b435dd3974e10b24be33541e229563489cf09e3446b97f5b928576f62ef5a86',
 'world': '7f4aebd14fcce6684e13db1acb5ebf81086a338f261f2a17facd59f64564d789',
 'aux': '86c21365b94f2ab3268663edd46780ea3cc1fcc36233d7873d9e4566a398a0da',
 'transcript': '4950ef36195b393534c7dee7409dd7b5a9a579d489b22e04dd4660c9eb12a71c'}
NATIVE_RANGES={'yt.json':('YT.EXE',{
 '0x2b49a':98,'0x24fbc':78,'0x38686':18,'0x3667a':4,
 '0x1081f':486,'0x300de':998,'0x369c4':4,'0x293e4':1084,
 '0x20ef9':34,'0x36622':8,'0x11594':134,'0x2b1e7':69,
 '0x24fbe':88,'0x36c1a':4,'0x2b4a3':88,
})}
KEEP={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
BINS={
 'YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037',
 'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
 'LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
 'KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()

def read(path):
    if path.exists():return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix+'.gz').read_bytes()))

def zipped(path):
    return gzip.decompress(path.read_bytes())

def side(path):
    return json.loads(zipped(path))

def rawfield(data, record, offset):
    at = (record-1)*137+offset
    return data[at:at+4]

def get(data, record, offset):
    raw = rawfield(data, record, offset)
    mantissa = int.from_bytes(raw[:3], 'little')
    if raw[3] == 0:
        return 0.0
    value = math.ldexp(1+(mantissa & 0x7fffff)/(1 << 23), raw[3]-129)
    return -value if mantissa & 0x800000 else value

def enc(value):
    if value == 0:
        return bytes(4)
    fraction, exponent = math.frexp(abs(value))
    mantissa = round((2*fraction-1)*(1 << 23))
    if mantissa == 1 << 23:
        mantissa = 0
        exponent += 1
    return (mantissa | (0x800000 if value < 0 else 0)).to_bytes(3, 'little')+bytes([exponent+128])

def put(data, record, offset, value):
    assert 1 <= record <= len(data)//137 and offset in range(41, 134, 4), 'patch bounds'
    at = (record-1)*137+offset
    data[at:at+4] = enc(value)

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

def public_score(data, player):
    """Public native ship score; planetary bank/production are not ship assets."""
    terms=((53,50),(61,100),(65,2500),(69,20),(73,30),(77,40),(81,1),
           (97,1000),(113,1000000),(117,50000),(121,750),(129,2500))
    if get(data,player,45)!=0:
        return 0
    total=sum(get(data,player,offset)*weight for offset,weight in terms)
    total+=sum(get(data,51+sector,81)*100 for sector in range(1,int(get(data,1,57)-get(data,1,53))+1) if get(data,51+sector,85)==player)
    # Native scanner flags are nonzero booleans; installed is canonical -1.
    if get(data,player,93)!=0:
        total+=250000
    return total

def assert_unchanged_except(before,after,fields=(),names=()):
    masked=bytearray(after)
    for record,offset in fields:
        at=(record-1)*137+offset;masked[at:at+4]=before[at:at+4]
    for record in names:
        at=(record-1)*137;masked[at:at+41]=before[at:at+41]
    assert masked==before, 'unrelated world mutation'

def auxiliary_witness(files):
    return sha(b''.join(name.encode()+b'\0'+data+b'\0' for name,data in sorted(files.items())))

def verify_native(root):
    assert NATIVE_RANGES, 'unfrozen native declarations'
    reads=0
    for filename,(executable,ranges)in NATIVE_RANGES.items():
        binary=(ROOT/'archive/dos-original'/executable).read_bytes()
        assert sha(binary)==BINS[executable], 'native binary identity'
        image=loaded(binary)
        records=read(root/'rea'/filename)['records']
        assert len(records)==len(ranges)+1, 'native observation count'
        images=[r for r in records if r['operation']=='inspect_native_load_image']
        assert len(images)==1, 'native load image count'
        verify_load_image(images[0],binary,image)
        seen=set()
        for record in records:
            if record['operation']=='inspect_native_load_image':continue
            assert record['operation']=='read_bytes', 'native operation'
            value=record['normalized_result'];address=value['address']
            assert address in ranges and address not in seen, 'native address set'
            seen.add(address);count=ranges[address]
            assert record['subject']['digest']['sha256']==sha(binary), 'native target identity'
            assert value['complete']and value['requested_bytes']==value['returned_bytes']==count, 'incomplete native bytes'
            at=int(address,16)-0x10000
            assert 0<=at<at+count<=len(image), 'native read bounds'
            assert bytes.fromhex(value['bytes_hex'])==image[at:at+count], 'native bytes'
        assert seen==set(ranges), 'native address set'
        reads+=len(seen)
    return reads

def verify_clock(directory,case):
    date=case['date'];clock=case['time']
    assert re.fullmatch(r'10/2[3-9]/2026',date), 'declared DOS date'
    line=(directory/'DOSDATE.LOG').read_text()
    assert re.search(r'Current date: [A-Za-z]{3} '+re.escape(date)+r'(?:\n|$)',line), 'DOS date'
    match=re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)',(directory/'DOSTIME.LOG').read_text())
    assert match, 'DOS clock'
    h,m,s,f,ampm=match.groups()
    actual=(int(h)%12+(12 if ampm=='pm'else 0))*3600+int(m)*60+int(s)+int(f)/10**len(f)
    h,m,s=map(int,clock.split(':'));expected=3600*h+60*m+s
    assert abs(actual-expected)<=.06, 'DOS clock mismatch'


def common_patches(case):
    """Independent transcription of the declared synthetic table geometry."""
    n=case['sectors'];assert isinstance(n,int) and 1<=n<=3000 and (n>1 or case.get('diagnostic')=='bounded-native-reentry-loop'), 'declared sector count'
    patches=[]
    for record in range(4,52):
        patches +=[(record,o,0) for o in range(41,137,4)]
        patches +=[(record,109,-1),(record,85,0)]
    # Only declared sectors are cleared: remapped planet rows are NOT sectors.
    for sector in range(1,n+1):
        patches +=[(51+sector,o,0) for o in (81,85,93,105,129,133)]
    if not case.get('standard'):patches +=[(1,57,51+n),(1,61,51+n),(1,93,54+n)]
    for sector in range(1,n+1):
        warps=[sector+1] if sector<n else [1]
        if 1<sector<n:warps +=[1]
        patches +=[(51+sector,o,warps[i] if i<len(warps) else 0) for i,o in enumerate(range(41,65,4))]
        patches +=[(51+sector,o,0) for o in (65,69,73,77)]
    for sector,warps in case.get('graph',{}).items():
        assert 1<=int(sector)<=n and len(warps)<=6 and all(1<=v<=n for v in warps), 'declared graph bounds'
        patches +=[(51+int(sector),o,warps[i] if i<len(warps) else 0) for i,o in enumerate(range(41,65,4))]
    patches +=[(2,o,v) for o,v in {41:297,45:0,49:500,53:10000,57:case['start'],61:10000,65:100,69:10,73:20,77:30,81:100000,89:0,93:0,97:7,105:0,109:0,113:9,117:0,121:1000,125:1,129:8}.items()]
    patches +=[(3,o,v) for o,v in {41:297,45:0,49:500,57:1,61:0,53:0,89:0,109:0,125:1}.items()]
    if case.get('planet'):patches +=[(51+case['start'],93,case['planet'])]
    return patches


def construct_before(case,baseline):
    n=case['sectors'];expected=bytearray(baseline);base=4051 if case.get('standard') else 51+n
    for record in range(base+1,base+(101 if case.get('standard') else 4)):expected[(record-1)*137:record*137]=bytes(137)
    slot=case.get('planet')
    if slot:
        assert slot in (1,2), 'declared mobile planet slot'
        record=base+slot
        expected[(record-1)*137:record*137]=baseline[(4053-1)*137:4053*137]
        name='The Wanderer' if slot==1 else 'Test Planet'
        expected[(record-1)*137:(record-1)*137+41]=name.encode().ljust(41,b' ')
        for o,v in {41:297,45:10,49:20,53:30,57:100,61:200,65:300,69:37,73:2,77:23,81:0,85:len(name),89:0,113:41,117:1234,125:43,129:47}.items():put(expected,record,o,v)
        if case.get('collision'):
            other=base+3;expected[(other-1)*137:other*137]=expected[(record-1)*137:record*137]
            expected[(other-1)*137:(other-1)*137+41]=b'Stationary'.ljust(41,b' ');put(expected,other,85,10)
    patches=common_patches(case)+[tuple(p) for p in case['patches']]
    if case.get('collision'):patches +=[(53,93,3)]
    for record,offset,value in patches:put(expected,record,offset,value)
    return bytes(expected),[list(p) for p in patches]


def planet_base(case):
    return 4051 if case.get('standard') else 51+case['sectors']


def planet_links(data,case,slot):
    return {sector for sector in range(1,case['sectors']+1) if get(data,51+sector,93)==slot}


def path_between(data,start,destination,n):
    queue=[(start,[start])];seen={start}
    for sector,path in queue:
        if sector==destination:return path
        for offset in range(41,65,4):
            to=int(get(data,51+sector,offset))
            if to and to not in seen:
                assert 1<=to<=n, 'route range'
                queue.append((to,path+[to]));seen.add(to)
    return None


def warp_trace(text,n,turns):
    """Check each returned warp receipt, including zero-turn forced calls."""
    charges=[];destinations=[];heats=[]
    chunks=text.split('* EMERGENCY WARP ENGAGED! *')[1:]
    for part in chunks:
        gauge=re.search(r'={32}\n\[([*]*)',part)
        assert gauge, 'warp heat gauge'
        heat=len(gauge[1]);heats.append(heat)
        assert 0<=heat<=31, 'warp heat bound'
        if 'MELT DOWN!' in part:
            assert heat==31 and 'Your engines are disabled!' in part and 'It will take a solar day to repair them.' in part, 'meltdown receipt'
            match=re.search(r'You are stranded in sector (\d+)\.',part)
            assert match, 'meltdown destination receipt'
            destination=int(match[1]);cost=turns
        else:
            match=re.search(r'sector (\d+)\. However, it takes you (\d+) turns to recharge your engines!',part)
            assert match, 'warp recharge receipt'
            destination,cost=map(int,match.groups())
            assert min(turns,4*heat)<=cost<=min(turns,4*heat+3), 'heat/recharge relationship'
        assert 1<=destination<=n, 'warp destination range'
        assert 0<=cost<=turns, 'warp turn capacity'
        turns-=cost;charges.append(cost);destinations.append(destination)
    return charges,destinations,heats,turns


def before_transport(case,before,text):
    """Price only verified movement preceding the common arrival shell."""
    command=case['command'];start=int(get(before,2,57));n=case['sectors']
    if command.startswith('M;'):
        if '\r~~N' in command:return 0,start,None
        destination=int(command.split(';',1)[1].split('\r',1)[0])
        assert destination in [get(before,51+start,o) for o in range(41,65,4)], 'ordinary adjacency'
        return 1,destination,None
    if command.startswith('C;3;'):
        if '\r~~N' in command:return 0,start,None
        target=int(command.split(';')[2]);path=path_between(before,start,target,n)
        assert path and len(path)>1, 'autopilot route'
        # These controls encounter a disruption on the very first planned edge.
        return 1,path[1],None
    if command.startswith('L;!;'):
        slot=case['planet'];destination=int(command.split(';')[2].split('\r')[0]);path=path_between(before,start,destination,n)
        assert path and len(path)>1, 'thruster route'
        assert f'Distance is {len(path)-1} and will take {10*(len(path)-1)} turns.' in text, 'thruster quote'
        assert 'Moving planets costs 10 turns per sector.' in text, 'thruster price notice'
        if '\r~~~~N' in command:
            assert 'Planet thrusters engaged.' not in text, 'cancelled transport engaged'
            return 0,start,start
        assert get(before,2,49)>=10*(len(path)-1) and 'Planet thrusters engaged.' in text, 'thruster admission'
        if case.get('collision'):
            assert 'There is already a planet in that sector!' in text and 'EXPLODED!' in text, 'thruster collision notices'
            return 0,start,None
        if slot==1:
            assert 'The Wanderer vanishes from your sensors!' in text, 'hidden Wanderer transport receipt'
            return 10,path[1],None
        stop=destination
        for sector in path[1:]:
            if get(before,51+sector,129)>0 or get(before,51+sector,81)>0 and get(before,51+sector,85)!=2:
                stop=sector;break
        assert ('Test Planet moved! (Xannoron Movers, we move anyTHING, anyWHERE!)' in text)==(stop==destination), 'ordinary transport completion receipt'
        return 10*path.index(stop),stop,stop
    return 0,start,None


def verify_semantics(case,before,after,text):
    name=case['name'];n=case['sectors'];slot=case.get('planet')
    holes=text.count('A *-BLACK HOLE-* grabs you!')
    fee,arrival,planet=before_transport(case,before,text)
    charges,destinations,heats,turns=warp_trace(text,n,int(get(before,2,49))-fee)
    assert get(after,2,49)==turns, 'saved turns disagree with paid movement and warp receipts'
    expected=FOOTPRINT[name]
    assert (holes,len(charges),int(get(after,2,57)),int(get(after,2,49)))==tuple(expected[:4]), 'arrival/warp footprint'
    assert len(charges)==holes+int(case['command']=='W;Y')+int(name=='startup-landing-lethal'), 'forced/manual/mine warp distinction'
    dead=name=='startup-landing-lethal'
    assert get(after,2,45)==(2 if dead else 0), 'death attribution'
    assert get(after,2,57)==(0 if dead else destinations[-1] if destinations else arrival), 'saved warp destination'
    assert get(after,2,81)==get(before,2,81), 'transport credits preserved'
    if get(before,2,93):
        if case['command'].startswith(('M;','C;3;')):
            assert '*** WARNING! *** Danger Scanner has detected the following in sector 2!' in text, 'scanner warning'
            assert 'Space-time disruption' in text, 'scanner disruption warning'
    if name.endswith('decline'):
        assert fee==0 and not charges and get(after,2,57)==get(before,2,57), 'declined warning has no travel effect'
    # Ordinary movement with a final zero balance drains .01 cloak; forced calls do not.
    cloak=get(before,2,125)
    if name=='arrival-zero-turns':cloak=.9900000095367432
    assert get(after,2,125)==cloak, 'forced warp cloak preservation'
    names=[]
    changed={(2,o) for o in (49,57,109)}|{(3,109)}
    if name=='arrival-zero-turns':changed.add((2,125))
    for player in (2,3):
        expected_score=enc(public_score(after,player))
        assert rawfield(after,player,109)==expected_score, 'saved score arithmetic'
    # A disruption wins over physical hazards at the same landing coordinate.
    for sector in range(1,n+1):
        row=51+sector
        for o in (81,85,129):
            if name in ('startup-landing-mines','startup-landing-both','startup-landing-lethal') and sector==3 and o==129:continue
            assert rawfield(after,row,o)==rawfield(before,row,o), 'disruption bypass preserves physical hazards'
    if name in ('startup-landing-mines','startup-landing-both'):
        assert 'There are 3 mines here! 1 EXPLODE!' in text and get(after,54,129)==0 and get(after,2,53)==8419, 'safe landing mine damage'
        assert text.index('A *-BLACK HOLE-*')<text.index('There are 3 mines here! 1 EXPLODE!'), 'arrival hazard ordering'
        changed|={(2,53),(54,129)}
    if name=='startup-landing-both':
        assert text.index('There are 3 mines here! 1 EXPLODE!')<text.rindex('Fighters in sector: 100 (Belong to Enemy'), 'mines precede fighter encounter'
    if dead:
        assert 'Your ship has been destroyed!' in text and get(after,54,129)==27, 'lethal mine aftermath'
        assert all(get(after,2,o)==0 for o in (57,65,97,117,129)), 'death cleared ship equipment'
        changed|={(2,o) for o in (45,65,97,117,129)}|{(54,129)}
    if slot:
        record=planet_base(case)+slot;actual=planet_links(after,case,slot)
        assert actual==set(expected[4]), 'saved planetary destination/link identity'
        if case.get('collision'):
            assert get(after,record,85)==0 and planet_links(after,case,3)=={2}, 'collision removes mover and preserves stationary planet'
            stationary=planet_base(case)+3
            assert after[(stationary-1)*137:stationary*137]==before[(stationary-1)*137:stationary*137], 'collision preserves stationary planet'
            assert get(after,2,61)<get(before,2,61) and get(after,2,49)==get(before,2,49), 'collision fighter loss without failed-edge charge'
            assert after[(record-1)*137:(record-1)*137+41]==bytes(4)+b' '*37, 'collision clears planet name'
            names.append(record)
            changed|={(record,85),(2,61)}
        else:
            assert get(after,record,85)==get(before,record,85), 'planet identity survives transport'
            if slot==2:assert actual=={planet}, 'ordinary planet follows charged prefix'
        if slot==1:
            assert 'The Wanderer vanishes from your sensors!' in text, 'Wanderer private departure receipt'
            assert 'successfully warped' not in text, 'Wanderer destination privacy'
        # Access/transport performs bounded lazy growth, not a new maintenance tick.
        for o in (45,49,53,57,61,65,69,113,125,129):
            assert get(before,record,o)<=get(after,record,o)<=get(before,record,o)*1.2+.01, 'bounded lazy planetary growth'
        assert 0<=get(after,record,89)-get(before,record,89)<181, 'planet access clock bound'
        assert get(after,record,117) in (get(before,record,117),get(before,record,117)+1), 'planet lazy integer clock'
        changed|={(record,o) for o in (45,49,53,57,61,65,69,89,113,117,125,129)}
        changed|={(51+s,93) for s in range(1,n+1)}
    elif name=='wanderer-reconnect':
        record=planet_base(case)+1
        assert planet_links(after,case,1)==planet_links(before,case,1), 'reconnect preserves hidden planetary location'
        assert get(after,record,89)>get(before,record,89), 'reconnect lazy access clock'
        changed|={(record,o) for o in (45,49,53,57,61,65,69,89,113,117,125,129)}
    if case['command'].startswith('S'):
        scans=text.split('Sensors Activated ]')[1:]
        expected_holes=({3,4} if n==8 and not case.get('parent') else {592,1051} if n==3000 and not case.get('parent') else {3,5} if n==8 else set())
        assert len(scans)==(2 if case['command']=='S;S' else 1), 'sensor scan count'
        for scan in scans:
            scan=scan.split('[ End Sensor Scan ]')[0]
            labels={int(m[1]) for m in re.finditer(r'Sector: (\d+)\n\*\* Space-time disruption detected!',scan)}
            assert labels==expected_holes, 'session-local sensor hazard candidates'
    assert_unchanged_except(before,after,changed,names)


def verify_aux(case,before,after,text,initial,final):
    assert set(initial)==set(final), 'auxiliary file set'
    for name,data in initial.items():
        if name not in {'YTNEWS.DAT','YTSCORE.ASC'}:assert final[name]==data, 'unrelated auxiliary mutation'
    prefix=initial['YTNEWS.DAT'].rstrip(b'\x1a');news=final['YTNEWS.DAT']
    assert news.startswith(prefix), 'public news prefix preservation'
    tail=news[len(prefix):].decode('cp437')
    match=re.match(r'-=\*=- (\d{2}:\d{2}:\d{2}) Q  Logged on -=\*=-\r\n',tail)
    assert match, 'public login news'
    h,m,s=map(int,match[1].split(':'));h0,m0,s0=map(int,case['time'].split(':'))
    assert 0<=3600*(h-h0)+60*(m-m0)+s-s0<=30, 'public login clock'
    extra='';name=case['name']
    if name in ('startup-landing-mines','startup-landing-both'):
        extra='Q  hit sector mines in sector 3!\r\nShields reduced to 8419 units!\r\n'
    if name=='startup-landing-lethal':extra='Q  hit sector mines in sector 3!\r\n  -  Q  was killed!\r\n'
    if case.get('collision'):
        extra=' *** Planet Test Planet EXPLODED while being moved by Q !!!\r\n'+f'Q  lost {int(get(before,2,61)-get(after,2,61))} fighters in the explosion!\r\n'
    assert tail[match.end():]==extra+'\x1a', 'exact public event settlement and transport privacy'
    score=final['YTSCORE.ASC'].decode('cp437')
    for player,alias in ((2,'Q'),(3,'Enemy')):
        match=re.search(r'^ *\d+ +[0-9.]+% +([0-9,]+) +(None|1) +(\d+) +'+alias+r' *\r?$',score,re.M)
        assert match and int(match[1].replace(',',''))==int(public_score(after,player)), 'public scoreboard points'
        assert int(match[3])==get(after,player,117), 'public scoreboard ports'
    assert auxiliary_witness(final)==AUX_SHA[name], 'frozen complete auxiliary witness'


def verify_control(directory,decl,case,baseline,worlds,auxiliaries,diagnostic=False):
    name=case['name'];d=directory/name
    assert re.fullmatch(r'[a-z0-9-]+',name), 'scenario path'
    assert case==read(d/'result.json') and all(case[k]==v for k,v in decl.items()), 'manifest/declaration mismatch'
    assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA, 'session identity'
    assert case['date']==decl.get('date','10/24/2026') and case['time']==decl.get('time','00:00:00'), 'declared date/time identity'
    assert case['binaries']==BINS, 'binary identity'
    assert case['timeout_seconds']==case.get('timeout',120), 'capture timeout declaration'
    if diagnostic:
        assert not case['complete'] and not case['program_returned'] and case['timed_out'] and case['timeout_seconds']==40, 'diagnostic classification'
    else:assert case['complete'] and case['program_returned'] and not case['timed_out'], 'incomplete DOS control'
    assert set(case['files'])==KEEP and {p.name for p in d.iterdir()}==KEEP|{'result.json.gz'}, 'retained file set'
    for file,digest in case['files'].items():assert sha((d/file).read_bytes())==digest, ('file hash',name,file)
    verify_clock(d,case)
    assert (d/'RETURN.LOG').read_bytes()==(b'' if diagnostic else b'DISRUPTION_PROGRAM_RETURNED\r\n'), 'DOS return marker'
    before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz')
    assert len(before)==len(after)==568687, 'world size'
    if case.get('parent'):
        assert case['parent'] in worlds, 'parent ordering'
        expected=bytearray(worlds[case['parent']]);patches=decl['patches']
        for record,offset,value in patches:put(expected,record,offset,value)
        initial=auxiliaries[case['parent']]
    else:
        expected,patches=construct_before(decl,baseline)
        initial={p.name:p.read_bytes() for p in SOURCE.iterdir() if p.suffix.upper() in ('.DAT','.ASC','.DEF','.TMP') and p.name!='YTDATA.DAT'}
    assert case['applied_patches']==patches, 'declared patch list'
    assert before==expected, 'undeclared setup or broken world chain'
    assert {n:bytes.fromhex(v) for n,v in side(d/'side-before.json.gz').items()}==initial, 'auxiliary input chain'
    auxiliary=side(d/'sidefiles.json.gz');final={n:bytes.fromhex(v['hex']) for n,v in auxiliary.items()}
    assert all(v['after_sha256']==sha(final[n]) and v['before_sha256']==(sha(initial[n]) if n in initial else None) for n,v in auxiliary.items()), 'auxiliary identity'
    keys=('\r~~~~~\r~'+decl['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode()
    assert (d/'KEYS.TXT').read_bytes()==keys, 'exact input stream'
    text=(d/'transcript.txt').read_text()
    assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text, 'raw transcript identity'
    if diagnostic:
        assert case['diagnostic']=='bounded-native-reentry-loop' and case['sectors']==1, 'unsupported diagnostic geometry'
        assert text.count('A *-BLACK HOLE-* grabs you!')>=2 and text.count('* EMERGENCY WARP ENGAGED! *')>=2, 'diagnostic repeated native arrival'
        assert get(after,2,49)==0 and get(after,2,57)==1 and 'Generating ScoreBoard' not in text, 'diagnostic does not claim a completed login'
        assert sha(after)==DIAGNOSTIC_SHA['world'] and auxiliary_witness(final)==DIAGNOSTIC_SHA['aux'] and sha(text.encode())==DIAGNOSTIC_SHA['transcript'], 'frozen incomplete diagnostic witness'
    else:
        verify_semantics(case,before,after,text);verify_aux(case,before,after,text,initial,final)
        assert sha(after)==WORLD_SHA[name], 'frozen complete world witness'
        assert sha(text.encode())==TRANSCRIPT_SHA[name], 'frozen complete transcript witness'
    return after,final


def verify(root):
    assert RECIPE_SHA and WORLD_SHA and AUX_SHA and TRANSCRIPT_SHA, 'unfrozen disruption declarations'
    directory=root/'dos';baseline=(SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline)==BASE_SHA and zipped(directory/'baseline.dat.gz')==baseline, 'baseline identity'
    recipe_bytes=(directory/'recipe.json').read_bytes();assert sha(recipe_bytes)==RECIPE_SHA, 'frozen declarations'
    recipe=json.loads(recipe_bytes);manifest=read(directory/'results.json')
    assert recipe['recipe']==manifest['recipe']==RECIPE and recipe['source']==str(SOURCE.relative_to(ROOT)), 'recipe identity'
    declarations={c['name']:c for c in recipe['scenarios']};rows={c['name']:c for c in manifest['scenarios']}
    assert len(rows)==len(manifest['scenarios'])==len(declarations)==len(WORLD_SHA)==61, 'scenario count'
    assert set(rows)==set(declarations)==set(WORLD_SHA)==set(AUX_SHA)==set(TRANSCRIPT_SHA)==set(FOOTPRINT), 'scenario identity'
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes() for n in BINS if n!='KEYFEED.COM'}
    binaries['KEYFEED.COM']=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
    assert {n:sha(b) for n,b in binaries.items()}==BINS, 'archived binary identity'
    worlds={};auxiliaries={}
    for name,decl in declarations.items():
        try:worlds[name],auxiliaries[name]=verify_control(directory,decl,rows[name],baseline,worlds,auxiliaries)
        except AssertionError as error:raise AssertionError(f'{name}: {error}') from error
    d=root/'diagnostics'/'one-sector-loop';recipe_bytes=(d.parent/'recipe.json').read_bytes()
    assert sha(recipe_bytes)==DIAGNOSTIC_SHA['recipe'], 'diagnostic frozen declarations'
    diagnostic_recipe=json.loads(recipe_bytes);diagnostic_rows=read(d.parent/'results.json')['scenarios']
    assert len(diagnostic_recipe['scenarios'])==len(diagnostic_rows)==1, 'diagnostic scenario count'
    assert zipped(d.parent/'baseline.dat.gz')==baseline, 'diagnostic baseline identity'
    verify_control(d.parent,diagnostic_recipe['scenarios'][0],diagnostic_rows[0],baseline,{}, {},True)
    reads=verify_native(root)
    print(f'Verified {len(rows)} returned disruption controls, four exact world/auxiliary reload chains, one separate incomplete synthetic diagnostic and {reads} native byte observations.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research',type=Path,default=ROOT/'research/yt-disruption')
    verify(parser.parse_args().research)
