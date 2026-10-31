"""Independently verify retained DOS plasma launch, routing and disruption evidence."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE = 'plasma-routing-v1'
BASE_SHA = '2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19'
RECIPE_SHA = '77c337b14aad0c9f8db66345870a1149d6383fe6eaed10443c80031a5e4a4108'
BINS = {'BRUN30.EXE': '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
 'KEYFEED.COM': '06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
 'LOCAL.EXE': 'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
 'YT.EXE': 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'}
WITNESSES = {'quiet-origin': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                  'transcript': 'd81dbbc1daff7d891b02089a27386f89b9aed00c155c5c8260e7aa5b2854f46b',
                  'aux': '10b1ec96d212e36fd0577d0a7ce38a6c2f174abcfb2a66d1279986f873959e1c'},
 'empty-adjacent': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
                    'transcript': 'db84f49df04b3f92599cd7ff452197174fb1de7e593aed96cea81ba9b542115f',
                    'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'no-bolts': {'world': '12613698556e40b8d3837938476e683adc6ebc9922ad7e72bcfa3e5af28a92c4',
              'transcript': '82755f76122e707fd8edb08a8fdf749f54a08c086e4457a2fada581630004799',
              'aux': '0432903c36ac0a0871ff866ee66e7da6b2c4300bbff5afe32584c37134d78514'},
 'zero-turns': {'world': '0b3d54c7b6dd286b9530bb425f1fd034a697d8891435d38b2cbf041f681f9d50',
                'transcript': '840d4a80b06e9d072d553e61889851f7ac0c3b37e409366bd594a803312c6b59',
                'aux': '10b1ec96d212e36fd0577d0a7ce38a6c2f174abcfb2a66d1279986f873959e1c'},
 'one-turn': {'world': '72bcf527570fedc5e4df30f75a76f46b02e40f2d7d9f71273c8f90d3102af534',
              'transcript': '74d4aa013eb215ea50698693d96270d517b0886fd03abb2bfe1278534548c6b6',
              'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'zero-sector-reprompt': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                          'transcript': 'af39d86bbb286cf37e4f5fd5fd6c6b72d4449751ebc58eb0259dcefe2ff5d86b',
                          'aux': 'b7a8cf03d4e58054a60e02409a244461cae8022cc0df072cda528c031f030dc6'},
 'blank-sector': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                  'transcript': '5f8967bcbcc55bc8216d761a6742c52227893cfdc567cacbc826a0d1e231dbe2',
                  'aux': '7070051f231bfd292fb014a8d285bb045723e2e52decebc9d1a3b48e16a97281'},
 'cancel-count': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                  'transcript': 'cf4a2b9f2354f8a2281cc3eba8a2d8f19fcfe3a041a39de4ec7e13e41386871f',
                  'aux': '10b1ec96d212e36fd0577d0a7ce38a6c2f174abcfb2a66d1279986f873959e1c'},
 'negative-count': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                    'transcript': 'e4c08a5b89f5055a8d0d855556fb207594b0a0b8d5aba0babe36534dca6ea434',
                    'aux': 'bd86d6201b34ecc438d6ea439c9d3286365a96ee40a959e1da24dee31edd5eb2'},
 'oversized-count': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                     'transcript': 'cd1b6a3c71b6e23c1493140d0d756c2f670b2c613a0a0f72250b74bbed083d65',
                     'aux': 'bd86d6201b34ecc438d6ea439c9d3286365a96ee40a959e1da24dee31edd5eb2'},
 'invalid-sector': {'world': '9ced4a37dbe77184691ad02177cfce552137ecde1d1f8e2f35a84487890110cb',
                    'transcript': '44689796f117433d1e00381869d56123c1010bac908133313b1f3aebfa4a7a55',
                    'aux': '5afbee877c03e1afe40e941bca083667d90ae9ede0f1be6aa70ea95659de2f36'},
 'own-sector': {'world': 'c547709519b224a0b180c04caed74be3112aa4d8da14bcabbb9a9d2e5ab59558',
                'transcript': '445457565e61917e5590cd4eb1f4f9c24ae56c006481f5c32aa3f40fc1a368d5',
                'aux': '927b52c893a63903f4881dab71ac93ddd21fd695cf18a7a74e1480fc1e0aeeaf'},
 'own-sector-cloaked': {'world': '45b664c090d4b66d46a389c0c1fab42bafb391eb3cf185e7e85b181da35cdb61',
                        'transcript': '998dda38296bafd96bccb85ca8d6cdeaf321d938ef799867d28749224a965230',
                        'aux': '927b52c893a63903f4881dab71ac93ddd21fd695cf18a7a74e1480fc1e0aeeaf'},
 'earth-target': {'world': '63ff48ee711da9205ebbdcae7091972947fa1c56eeb63d69e9e5f9de2d598f6a',
                  'transcript': '1828bc4ac34cb03aa3f13c87fba689cfc6e8a3cf730aa790387bfa2748486650',
                  'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'two-hop': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
             'transcript': '1bf818d2c4f6561b97c3cb1060a43120ef163f91e1f855b8e472100dd22c835a',
             'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'three-hop': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
               'transcript': '21352e0abcf64b83d8fa94654ef0b54fc6bb306345eaf22cec7a64c23708fee1',
               'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'route-dead-end': {'world': 'a6e70061e75cea79fca2c75c761450327bce1dbd831dcaaf7ed6e3160d309fca',
                    'transcript': '576c6668eae669f25d824cd29e2ff553672700a61e0a44b50dc776bdc222915a',
                    'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'route-tie': {'world': '44c7c4a81bc210ec75cf3c2eb979b0e09fd09597aa62b877197cda8db93d5e3a',
               'transcript': 'e140e8b0528e288bfced73f20b62d07634507625df88c946f20e12dc8b39aae7',
               'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'repeat-volley': {'world': 'a6c87ccb28730f2f0cb73b65c7e9a6fd664340fe0e8a4198104aa1704100adde',
                   'transcript': '065753e7f99b25a02ba693a8ea21991ec037affd20ffa7c88c09254fce9a0cfd',
                   'aux': '3f67e864a9215cb47c0b1e68e435848f86c39992eb8edd68023af4f8fc04d97f'},
 'fighters-enemy': {'world': 'fe89c35507b48782015e7c889528be4a455a7b6137ad047b24aef77ee5507500',
                    'transcript': '2d26eb2db9d159c1b1f4ef83c59b36c391d0d9f7ecc15f3dadef4ffad9e0636a',
                    'aux': 'f81c6da7ec5ac9a3346439dd049a8221c08c219ad92c738f8e15a2ea22f8000e'},
 'fighters-self': {'world': 'c8a899e23a38c93fa8a0b3ea9b8a75e8640631463156b7c037c780972f0139b0',
                   'transcript': 'b15f90f9069294724d5658b0d394044303103a8a3487480dabe685ebd1ba8fed',
                   'aux': '47b4a255a074cbc72f21f5048ae9a4e6117b0df9993a4c0378b6dddcdd400a85'},
 'fighters-two-bolts': {'world': 'e51cf78a0f104f7ad880999ccf8c59f3762e70c8214f45b861d395699c5c4608',
                        'transcript': 'f3cc6ebc9e3e114696c3f9e7369cf3820e68e61b4a25d71c56b1bb5d622e9fe3',
                        'aux': 'd21477b5a49474ee953ab7e1ba773fcdad8effc5f65da041eb7cf286863fc5d7'},
 'fighter-spill': {'world': '47107e17ce692cad78210e7ca6fce675ca562f2232409e58d8225b0a99ff6990',
                   'transcript': '8a9afd902aac186b80ed62c45097275f6e88ab390e037dcb8e6cb98ab3ef6bc7',
                   'aux': 'abcbdc9d476055e2e259ba9c84ad5c1bfd5007b9d3dae72957e5a08e153f9828'},
 'mines-only': {'world': '6a0d297c1817685b048f07cd52c8a0cbbd604bd659c89de3e58932d8bc99fa8b',
                'transcript': '3a99aad0eaaf4dc00c57a150e720b1022181d3f92b6ded188f154e3419b2a0db',
                'aux': 'd0982c583094c34678f861634f6a7e431198c4b8a392d89abeb7d5ae41d94c6d'},
 'enemy-ship': {'world': '7ad3c3ce58e360413e537760b98f39250f00b9997ef4d2f57ff3fa3c44b32899',
                'transcript': '9bcae7c53e6d271f2db3b5e87bca335de03110a8ceffb8e9c55676a4b476ca5b',
                'aux': 'ff33f9b1605bae453ee3230a3e898d54c1397e01e847099a7f9c0cc8a642fd1b'},
 'cloaked-ship': {'world': '9090e5330091236fb539b3e96948bfbfbca119bafca60e5f2b56fac69c2b4a7b',
                  'transcript': '9bcae7c53e6d271f2db3b5e87bca335de03110a8ceffb8e9c55676a4b476ca5b',
                  'aux': 'ff33f9b1605bae453ee3230a3e898d54c1397e01e847099a7f9c0cc8a642fd1b'},
 'team-ship': {'world': '87f1feacf92f358e1753b1949a08546f6e01aa33f8b49f599f0cc389c35876ab',
               'transcript': '7a4a60277869d2849aaea7ecac8166dd142af710dbd79daeb2fc347936507ab4',
               'aux': '94abea388e4980963b588777557be5d85638dc207023c67bc7aef264bc0cf539'},
 'ship-fighters': {'world': '2f51004f4373b5c507f86932f04753bdb62ca05b86fd1752e800c20529bf622a',
                   'transcript': 'c22045a607e6e14f681d2730c5caf6ba4ae3e1b802d6951213bd48fb7025f339',
                   'aux': 'f0246503b58f703dcfe226286c0b53e95ff0261c9e8f436609cd6c11bfa3a559'},
 'two-ships': {'world': '22cadc4af60080cfd7750441fd9b3f2bdb26377b3ac6242bc3c7d44afe8cffe7',
               'transcript': 'ead0f7f4bb82c3169de7600df309ccfc1e85590c5774c0f142b8135b43de9d17',
               'aux': '0cb606d338585708c5b4d12d7e091cdbb5f6698b8019765f95e2cc42c68de8ad'},
 'lethal-ship': {'world': '5b702c7683ea78cae2f98fe161eed1237393ed280c0159da810817b0a3716960',
                 'transcript': 'd0035b3a7328948a6b208b62523af5c04c1e3a2dc8506252adc8f9d79564d467',
                 'aux': 'bc864cb042ed6ac41664a0067979e6b3462bb0cadeef336b8d92880ef80ad37b'},
 'planet-productive': {'world': 'c915e62540adaf6d214e7a60acec91b7158a7c2f85ea2348982080830a261d32',
                       'transcript': 'e14d4ab14f5adf7811104a8ad1153824ca1deb5987ef5fb4dc3772fa563aa60f',
                       'aux': '2c9822cc71bffcbdf33df55abd23a466d14d42f1da93845644a2297895867a25'},
 'planet-zero-projection': {'world': 'dcc301fc32361d18908f054e3c45dd210e9929f69143accb699e16f0fc6c4332',
                            'transcript': 'bf36446eee719f736adf7217c71938a824d99e08e40b666aa45dfe8d6787ffcc',
                            'aux': '31a0c767cfe14fdbfdcc5f14a8735fae8931401066d0c80ac8f7a373760a8d0a'},
 'planet-small-projection': {'world': '58872005ccaf6ae36cf6283734d922cfe4ea4c5c30f818d0a0f8ea51fc6a6dff',
                             'transcript': 'bf36446eee719f736adf7217c71938a824d99e08e40b666aa45dfe8d6787ffcc',
                             'aux': '31a0c767cfe14fdbfdcc5f14a8735fae8931401066d0c80ac8f7a373760a8d0a'},
 'planet-small': {'world': '7bc39093b4c3da40df56e54edd3fada0a7c2afc0ba3f52620f4a8a2b0109cf79',
                  'transcript': 'a6e77de9afceb138f3b4439f9f39a9d560c9ad4030366bcc42c47e13c3e816d2',
                  'aux': '965005bb28f1647efb42644fc552d574e11492e58aff6e8d6a06699baad1a134'},
 'planet-zero': {'world': 'c5d612f1dc0858d56b41ae0437750675a26f14b2f55f7b1f10d1ec9ac6cd8557',
                 'transcript': 'a18c33557b62ddb1a1b72cef12cda793e78cba3d0705959a6c06c7c655274086',
                 'aux': '0cc54778355e8246a556222c09adbb3043a70c64a2987df9f9e5dd58ef20977b'},
 'planet-organic-small': {'world': '466068e2a1d226fc41fbda838271f358dd57db90b4c23c1881b2354f6442152c',
                          'transcript': 'f03ed642837f33ef810cd3e0ac250183db9575f605c1531a9809394d5de93415',
                          'aux': '0677022e83fba347cd2657668a355c4bd5861326b52ac4294a1a4966cc30e3d0'},
 'planet-no-ore-stock': {'world': 'e8a13fcae4286f4442af9176579352feba16a701e032009035c086ae1aeb3983',
                         'transcript': 'e14d4ab14f5adf7811104a8ad1153824ca1deb5987ef5fb4dc3772fa563aa60f',
                         'aux': '2c9822cc71bffcbdf33df55abd23a466d14d42f1da93845644a2297895867a25'},
 'mixed-defense': {'world': 'cb51cb04b966fa35b9d68c81e489791a2daf6fb2ac0fe2faad711fe41a039b0a',
                   'transcript': '41332d6ff2ca07d5225fdb61361dfd0170a617a2b407a0f2011c8cbf0eef2d10',
                   'aux': '22c2a2ca7c1533ff26f6b3e47ef2acc270ee938101fc749355bff53b86b199d8'},
 'hole-592': {'world': '4cfa561d54e7aa7f20512285ca5e6d2b5b4d284b0e58cc37e6072a583cfc0fb9',
              'transcript': 'b63075cf5244352e860d4615baf411786c385ef0e1538ac7bbdda5de3e7ee461',
              'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'hole-1051': {'world': '6e534ed1d647f7cff32365f42e6a9af608a8ba85135d462460ce12a04d3c20e1',
               'transcript': '43e6019eec3a9b6b6c520b32495a2f82ab3b5134337f0759b6408ddfbd0204a3',
               'aux': 'c24e287433f2b0286c39d93ffe4607b9163ed6841874c3fdb42599e670b9b391'},
 'hole-target-defenses': {'world': '21ee9f4e22841467bef4ee6d2e258a33e862549a48014f1a047334165a0eacfb',
                          'transcript': '127660256e00a5319b639003c29268bc2bf845c7b56a608c6d178be171a14fa3',
                          'aux': 'dc1cd4614e2b7000957fd145c7f12c2e6f8573692038e9ace148081a2ac99ce9'},
 'hole-enroute': {'world': 'e8b7363221e9f0e60d5fc3c3cbfc521025045d66b3cd9b45a96ae1ee57c4f8fd',
                  'transcript': 'f68d48615461aef437790ac89af88fb9dec8beb9816b2ca1df888448cb849bb4',
                  'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'hole-sensors': {'world': '9b85deaa7e1bed4525e2019ba8dee5134961920134d69014b7738737c7a7b9fb',
                  'transcript': 'afd35ef756a495cc4c4af39264a02f52e71dbd62be9f36782c335715c56ad19f',
                  'aux': '10b1ec96d212e36fd0577d0a7ce38a6c2f174abcfb2a66d1279986f873959e1c'},
 'adjacent-clock-01': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
                       'transcript': '65daa00960d54e2da3c7d5e80a7f4d702eb34c315c68bd6e34dda96f92215066',
                       'aux': '22a51ab96a390da28c3dfbb6c240f875697b6e191efd0d95837d0c0c89ec5c33'},
 'fractional-count': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
                      'transcript': '53ff136af22656da824cf576e5f32e2efb08d8d939f466187802929e63328629',
                      'aux': 'c24e287433f2b0286c39d93ffe4607b9163ed6841874c3fdb42599e670b9b391'},
 'avoid-route': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
                 'transcript': '4f68b9a09fc43253f360e666704b952dadfd33a2fbf4d4dd444168f34fff14c5',
                 'aux': 'c24e287433f2b0286c39d93ffe4607b9163ed6841874c3fdb42599e670b9b391'},
 'route-tie-reverse': {'world': '54cc59f90e8e664a26de76986754f254b07e928025203cf1b065b2bed71c5183',
                       'transcript': '072e7922c65445ea5fd978511bdd59052ac353ba6c79db1cfcb22fec35362147',
                       'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'range-exhaustion': {'world': '8d6566e337b7ccbb84a725c1d65a5aa5a67711a09976d98929154857073fe91b',
                      'transcript': 'f2dfeb825bdf27cf54b77133757f789d57da567ac8c9f053188f596e7f2ebcde',
                      'aux': '2dc0d1e55b3d83b845e3a53678aa0948b29264b1e0804c5306738fe84131477b'},
 'empty-two-bolts': {'world': '42157fd904f99e0a580d5d97f69330abcb5a41c7b9b1af23387ca02a86bd627e',
                     'transcript': '434dca48f8189ef82e090d88ab7fd992c34efc318dbc4acbdb96ebdcdf9a0c26',
                     'aux': 'e10e663ae9e383e1f6af5a996a030328493f5d477cc4e709ef95ce2a0b73d016'},
 'self-lethal': {'world': '601e769788bcd798a948ec0b6336da01cb90a35053c6984b6a9cb4d0fad08872',
                 'transcript': 'f0ac808f7cf8e909828788a3fd467673453bc7036823eb105cb8741c5a69e689',
                 'aux': 'aa0dfdfc946bc926e45bf26b044ce319587ce319c3b63d99d68e8968cb1256b8'},
 'friendly-small': {'world': '7739b85d4b071706ce840ce039dcbb7990616ffe0592665fc5ea16b20ad397d5',
                    'transcript': 'b751788aaf98326fb9f660acf1f43874b88477f0e537d18ce5faec242913295b',
                    'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'planet-self': {'world': 'b5addaec7e2c4120eb43b43418ee56ed27e7341236d89866aadf520513daf514',
                 'transcript': 'e14d4ab14f5adf7811104a8ad1153824ca1deb5987ef5fb4dc3772fa563aa60f',
                 'aux': '2c9822cc71bffcbdf33df55abd23a466d14d42f1da93845644a2297895867a25'},
 'planet-team': {'world': 'b35f367f5ae50046a1b688df80e6e9516a0cb83f21fe5131649ed8da8501bcd9',
                 'transcript': '87c673ed224d1edd3b2e708af0609c2b2a2038e4008c457719ea556d9cacbd44',
                 'aux': '2a641394941a52e95c8f244f91ef1b5eec7a6e9bdc3116cfc4b9317366fd18f5'},
 'planet-ore-only-full': {'world': '17c688e01ac759ec06df2a791343e4bfeaf8c1bd93cac073f41a06a0ccce7ad5',
                          'transcript': '7980cebca826a895fb6ffcf51419dce12c60224e4cdcb0e3a0da99e4b08203f6',
                          'aux': '6a96cff8f3bd21405a97fd5f458cb5c81a98f8d2c854cf76507cc40232f0fb85'},
 'planet-ore-only-empty': {'world': '9879e06936bd0ea865a66db70130dd5dbd3a7ca6c7ac49d8f701cfe246f609b0',
                           'transcript': '7980cebca826a895fb6ffcf51419dce12c60224e4cdcb0e3a0da99e4b08203f6',
                           'aux': '6a96cff8f3bd21405a97fd5f458cb5c81a98f8d2c854cf76507cc40232f0fb85'},
 'planet-impact-zero': {'world': 'c5d612f1dc0858d56b41ae0437750675a26f14b2f55f7b1f10d1ec9ac6cd8557',
                        'transcript': '39a2c8d7d154033374487d82540fa97aa085cb087610fcc6160c1c0a689450df',
                        'aux': 'c195b565508752cc771aa1a43dbf0895228a0e7a08d43b9db8c8401927db7b84'},
 'planet-zero-empty': {'world': 'c5d612f1dc0858d56b41ae0437750675a26f14b2f55f7b1f10d1ec9ac6cd8557',
                       'transcript': '09b585a0a76d2659bf1eeacdfcf13b86f1a63a475b716c5d16ab426b167ad4ce',
                       'aux': '7b47cd3731ebd1ef9521d2bf83ea62a9b3af5e17d965676cf126365b2c59871b'},
 'hole-rebuilt-route': {'world': '391c6f4b30f6a4f63ed6ab726c1d76ffb8654b481708770515f91b6e71496cd7',
                        'transcript': '210b1783fd5b44cea73e4012c99287f9dae6ecac48240bf347965f40049baec1',
                        'aux': '47b9be2ef42294c9fc9f4973a00e8be607ead581f7124a6c316f22cfb14ddf14'},
 'hole-back-through-self': {'world': '80381e495677cd7c79714e7c18e80996209bd64d972057827772d6d2e413edcf',
                            'transcript': 'b0115eea69e9b00ec37648c23a97d6c83aeb2ddfd074382a6599c4006b19a555',
                            'aux': 'd352673afd5826c1ce1434da41b3f37ad061050616ad770750870c726fe46769'},
 'hole-two-redirects': {'world': '9801cd150682f326cea4f1eaba9ff3502a55d3495394396bcd94ce762c918309',
                        'transcript': '4540bb945757d0d4da5dd49ef89c00df00fc73f5c85583023b2b0c39659334cb',
                        'aux': '3713a3406591a4083ae1e0ba88801e730a9775fbc8b5e423e0316c52fd42f700'},
 'volley-reload': {'world': 'a6c87ccb28730f2f0cb73b65c7e9a6fd664340fe0e8a4198104aa1704100adde',
                   'transcript': 'd19f3f02f3f46549997981b71e666e1ac17abc2ec77ab95f56613be7eee6cb98',
                   'aux': '14c1ce58fce1d4400cd114de2f669dd8fe6d0a94ca71d8615c3eafe416aa539c'},
 'planet-reload': {'world': '7bc39093b4c3da40df56e54edd3fada0a7c2afc0ba3f52620f4a8a2b0109cf79',
                   'transcript': 'c3ae27a0b5ae5ed1415991c810343c098f1ec8c11aefa1f2b25a562a6d31f205',
                   'aux': '5a1250680f0eaef6672079cac6ad491d96b58c02d6b5f0f99c4bb930c57ea857'}}
FOOTPRINT = {'quiet-origin': [[2, 109], [3, 109]],
 'empty-adjacent': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'no-bolts': [[2, 109], [3, 109]],
 'zero-turns': [[2, 109], [3, 109]],
 'one-turn': [[2, 49], [2, 109], [2, 113], [2, 125], [3, 109]],
 'zero-sector-reprompt': [[2, 109], [3, 109]],
 'blank-sector': [[2, 109], [3, 109]],
 'cancel-count': [[2, 109], [3, 109]],
 'negative-count': [[2, 109], [3, 109]],
 'oversized-count': [[2, 109], [3, 109]],
 'invalid-sector': [[2, 109], [3, 109]],
 'own-sector': [[2, 49], [2, 53], [2, 61], [2, 109], [2, 113], [3, 109]],
 'own-sector-cloaked': [[2, 49], [2, 53], [2, 61], [2, 109], [2, 113], [3, 109]],
 'earth-target': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'two-hop': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'three-hop': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'route-dead-end': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'route-tie': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'repeat-volley': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'fighters-enemy': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 81]],
 'fighters-self': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 81]],
 'fighters-two-bolts': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 81]],
 'fighter-spill': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 81], [152, 85], [152, 129]],
 'mines-only': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 129]],
 'enemy-ship': [[2, 49], [2, 109], [2, 113], [3, 53], [3, 61], [3, 109]],
 'cloaked-ship': [[2, 49], [2, 109], [2, 113], [3, 53], [3, 61], [3, 109]],
 'team-ship': [[2, 49], [2, 109], [2, 113], [3, 53], [3, 61], [3, 109], [58, 77]],
 'ship-fighters': [[2, 49], [2, 109], [2, 113], [3, 61], [3, 109]],
 'two-ships': [[2, 49], [2, 109], [2, 113], [3, 53], [3, 61], [3, 109], [4, 109]],
 'lethal-ship': [[2, 49], [2, 65], [2, 81], [2, 109], [2, 113], [3, 45], [3, 57], [3, 93], [3, 117], [3, 129], [152, 129]],
 'planet-productive': [[2, 49],
                       [2, 109],
                       [2, 113],
                       [3, 109],
                       [4053, 45],
                       [4053, 49],
                       [4053, 53],
                       [4053, 57],
                       [4053, 61],
                       [4053, 65],
                       [4053, 69],
                       [4053, 77],
                       [4053, 89],
                       [4053, 125],
                       [4053, 129]],
 'planet-zero-projection': [[2, 109], [3, 109], [4053, 45], [4053, 49], [4053, 53], [4053, 57], [4053, 61], [4053, 65], [4053, 89], [4053, 129]],
 'planet-small-projection': [[2, 109], [3, 109], [4053, 45], [4053, 49], [4053, 53], [4053, 57], [4053, 61], [4053, 65], [4053, 89], [4053, 129]],
 'planet-small': [[2, 49],
                  [2, 109],
                  [2, 113],
                  [3, 109],
                  [152, 93],
                  [4053, 45],
                  [4053, 49],
                  [4053, 53],
                  [4053, 57],
                  [4053, 61],
                  [4053, 65],
                  [4053, 69],
                  [4053, 73],
                  [4053, 77],
                  [4053, 85],
                  [4053, 89],
                  [4053, 129]],
 'planet-zero': [[2, 49],
                 [2, 109],
                 [2, 113],
                 [3, 109],
                 [152, 93],
                 [4053, 57],
                 [4053, 61],
                 [4053, 65],
                 [4053, 69],
                 [4053, 73],
                 [4053, 77],
                 [4053, 85],
                 [4053, 89],
                 [4053, 129]],
 'planet-organic-small': [[2, 49],
                          [2, 109],
                          [2, 113],
                          [3, 109],
                          [152, 93],
                          [4053, 49],
                          [4053, 53],
                          [4053, 69],
                          [4053, 73],
                          [4053, 77],
                          [4053, 85],
                          [4053, 89],
                          [4053, 129]],
 'planet-no-ore-stock': [[2, 49],
                         [2, 109],
                         [2, 113],
                         [3, 109],
                         [4053, 45],
                         [4053, 49],
                         [4053, 53],
                         [4053, 57],
                         [4053, 61],
                         [4053, 65],
                         [4053, 69],
                         [4053, 77],
                         [4053, 89],
                         [4053, 125],
                         [4053, 129]],
 'mixed-defense': [[2, 49],
                   [2, 65],
                   [2, 81],
                   [2, 109],
                   [2, 113],
                   [3, 45],
                   [3, 57],
                   [3, 93],
                   [3, 117],
                   [3, 129],
                   [152, 81],
                   [152, 85],
                   [152, 129],
                   [4053, 45],
                   [4053, 49],
                   [4053, 53],
                   [4053, 57],
                   [4053, 61],
                   [4053, 65],
                   [4053, 69],
                   [4053, 77],
                   [4053, 89],
                   [4053, 125],
                   [4053, 129]],
 'hole-592': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'hole-1051': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'hole-target-defenses': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'hole-enroute': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'hole-sensors': [[2, 109], [3, 109]],
 'adjacent-clock-01': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'fractional-count': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'avoid-route': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'route-tie-reverse': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'range-exhaustion': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'empty-two-bolts': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'self-lethal': [[2, 45], [2, 49], [2, 57], [2, 113], [2, 117], [2, 129], [3, 109]],
 'friendly-small': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 81], [152, 85]],
 'planet-self': [[2, 49],
                 [2, 109],
                 [2, 113],
                 [3, 109],
                 [4053, 45],
                 [4053, 49],
                 [4053, 53],
                 [4053, 57],
                 [4053, 61],
                 [4053, 65],
                 [4053, 69],
                 [4053, 77],
                 [4053, 89],
                 [4053, 125],
                 [4053, 129]],
 'planet-team': [[2, 49],
                 [2, 109],
                 [2, 113],
                 [3, 109],
                 [58, 77],
                 [4053, 45],
                 [4053, 49],
                 [4053, 53],
                 [4053, 57],
                 [4053, 61],
                 [4053, 65],
                 [4053, 69],
                 [4053, 77],
                 [4053, 89],
                 [4053, 125],
                 [4053, 129]],
 'planet-ore-only-full': [[2, 49], [2, 109], [2, 113], [3, 109], [4053, 45], [4053, 57], [4053, 69], [4053, 77], [4053, 89], [4053, 129]],
 'planet-ore-only-empty': [[2, 49], [2, 109], [2, 113], [3, 109], [4053, 45], [4053, 57], [4053, 69], [4053, 77], [4053, 89], [4053, 129]],
 'planet-impact-zero': [[2, 49], [2, 109], [2, 113], [3, 109], [152, 93], [4053, 69], [4053, 73], [4053, 77], [4053, 85], [4053, 89], [4053, 129]],
 'planet-zero-empty': [[2, 49],
                       [2, 109],
                       [2, 113],
                       [3, 109],
                       [152, 93],
                       [4053, 61],
                       [4053, 65],
                       [4053, 69],
                       [4053, 73],
                       [4053, 77],
                       [4053, 85],
                       [4053, 89],
                       [4053, 129]],
 'hole-rebuilt-route': [[2, 49], [2, 109], [2, 113], [3, 109], [2419, 81]],
 'hole-back-through-self': [[2, 49], [2, 53], [2, 61], [2, 109], [2, 113], [3, 109]],
 'hole-two-redirects': [[2, 49], [2, 109], [2, 113], [3, 109]],
 'volley-reload': [],
 'planet-reload': []}
NATIVE_LEDGER_SHA = '60a52ce52ec3fa777654bea0c3bf981988caa85aa78c50334f719f7dbf66f7b5'
NATIVE_RANGES = {'yt.json': {'0x12079':642,'0x29ddb':4863,'0x20436':1536,'0x388f0':448,'0x122fe':112,'0x365f0':272,'0x36be6':8,'0x38ae2':176,'0x1a89b':55,'0x1a6e3':353,'0x1a41c':176,'0x2b106':214,'0x2f227':325}}
KEEP = {'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}

def sha(value):
    return hashlib.sha256(value).hexdigest()

def read(path):
    if path.exists():return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix+'.gz').read_bytes()))

def zipped(path):return gzip.decompress(path.read_bytes())

def get(data, record, offset):
    raw = data[(record-1)*137+offset:(record-1)*137+offset+4]
    assert len(raw)==4, 'MBF field bounds'
    if not raw[3]:return 0.0
    m=int.from_bytes(raw[:3],'little')
    v=math.ldexp(1+(m&0x7fffff)/(1<<23),raw[3]-129)
    return -v if m&0x800000 else v

def enc(value):
    if not value:return bytes(4)
    f,e=math.frexp(abs(value));m=round((2*f-1)*(1<<23))
    if m==1<<23:m=0;e+=1
    return (m|(0x800000 if value<0 else 0)).to_bytes(3,'little')+bytes([e+128])

def put(data,record,offset,value):
    assert 1<=record<=4151 and offset in range(41,134,4), 'patch bounds'
    at=(record-1)*137+offset;data[at:at+4]=enc(value)

def setup(case,baseline):
    """Independent transcription of controlled full-header table preparation."""
    assert case['sectors']==3000 and case['standard'] is True and case['start']==100, 'full-width fixture geometry'
    b=bytearray(baseline)
    for r in range(4052,4152):b[(r-1)*137:r*137]=bytes(137)
    if case.get('planet'):
        assert case['planet'] is True, 'declared planet setup'
        r=4053;b[(r-1)*137:r*137]=baseline[(r-1)*137:r*137]
        name=b'Target Planet';b[(r-1)*137:(r-1)*137+41]=name.ljust(41,b' ')
        for o,v in {41:297,45:10000,49:10000,53:10000,57:1000,61:2000,65:3000,69:37,73:3,77:5000,81:0,85:13,89:0,113:41,117:1234,125:43,129:47}.items():put(b,r,o,v)
        for o,v in case.get('planet_patches',[]):put(b,r,o,v)
    patches=[]
    for r in range(4,52):
        patches.extend((r,o,0) for o in range(41,137,4));patches.append((r,109,-1))
    patches.extend((51+s,o,0) for s in range(1,3001) for o in range(41,137,4))
    patches.extend((51+s,41,s+1 if s<160 else 100) for s in range(100,161))
    for s,links in case.get('graph',{}).items():
        assert 1<=int(s)<=3000 and len(links)<=6 and all(1<=v<=3000 for v in links), 'declared graph bounds'
        patches.extend((51+int(s),o,links[i] if i<len(links) else 0) for i,o in enumerate(range(41,65,4)))
    for r,values in ((2,{41:297,45:0,49:500,53:1000000,57:100,61:10000,65:100,69:10,73:20,77:30,81:100000,89:0,93:0,97:7,105:0,109:0,113:9,117:0,121:1000,125:1,129:8}),(3,{41:297,45:0,49:500,57:200,61:0,53:0,65:100,69:0,73:0,77:0,85:6,89:0,97:0,109:0,125:1})):
        patches.extend((r,o,v) for o,v in values.items())
    if case.get('planet'):patches.append((152,93,2))
    patches.extend(tuple(p) for p in case['patches'])
    for r,o,v in patches:put(b,r,o,v)
    return bytes(b),[list(p) for p in patches]

def public_score(data,player):
    if get(data,player,45):return 0
    terms=((53,50),(61,100),(65,2500),(69,20),(73,30),(77,40),(81,1),(97,1000),(113,1000000),(117,50000),(121,750),(129,2500))
    total=sum(get(data,player,o)*w for o,w in terms)
    total+=sum(get(data,51+s,81)*100 for s in range(1,3001) if get(data,51+s,85)==player)
    if get(data,player,93):total+=250000
    return total

def witness_aux(files):return sha(b''.join(n.encode()+b'\0'+v+b'\0' for n,v in sorted(files.items())))

def assert_footprint(name,before,after):
    masked=bytearray(after)
    for r,o in FOOTPRINT[name]:
        at=(r-1)*137+o;masked[at:at+4]=before[at:at+4]
    assert bytes(masked)==before, 'unrelated world mutation'

def clock(directory,case):
    date=case['date'];wanted=case['time']
    assert date=='10/24/2026', 'declared DOS date'
    assert re.search(r'Current date: [A-Za-z]{3} '+re.escape(date)+r'(?:\n|$)',(directory/'DOSDATE.LOG').read_text()), 'DOS date'
    match=re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)',(directory/'DOSTIME.LOG').read_text())
    assert match, 'DOS clock'
    h,m,s,f,ampm=match.groups();actual=(int(h)%12+(12 if ampm=='pm' else 0))*3600+int(m)*60+int(s)+int(f)/10**len(f)
    h,m,s=map(int,wanted.split(':'));assert abs(actual-(3600*h+60*m+s))<=.06, 'DOS clock mismatch'

def semantics(case,before,after,text):
    name=case['name']
    # Frozen entire-world witnesses below supplement these causal checks. Clock-
    # sensitive casualty counts are observations, not claims of RNG emulation.
    command_text=text[text.find('Main Command (?=Help)?'):]
    energies=[int(v) for v in re.findall(r'Plasma bolts targeted\.\.\. firing (\d+) megawatts!',text)]
    assert all(v>0 and v%2500000==0 for v in energies), 'launch energy arithmetic'
    quantities=[v//2500000 for v in energies]
    if not get(after,2,45):
        assert get(after,2,113)==get(before,2,113)-sum(quantities), 'saved plasma debit'
        assert get(after,2,49)==get(before,2,49)-len(quantities), 'saved launch turns'
        assert get(after,2,57)==get(before,2,57), 'launcher sector preserved'
    assert text.count('One Turn Deducted,')==len(energies), 'launch turn receipt count'
    for record in (2,3,4):
        if get(after,record,109)>=0:
            expected=public_score(after,record)
            # Native per-operation MBF rounding is a separate parity boundary.
            # The exact persisted cache is additionally pinned by the world hash.
            assert abs(get(after,record,109)-expected)<=max(1,abs(expected)*2**-20), 'saved score arithmetic'
    entries=[(int(s),float(e)) for s,e in re.findall(r'Bolt entering sector (\d+)\. ([0-9.]+) Megawatts remaining\.',text)]
    assert all(1<=s<=3000 and e>0 for s,e in entries), 'tracking bounds'
    assert all(e<=max(energies,default=0) for _,e in entries), 'tracking energy bound'
    if name in ('empty-adjacent','adjacent-clock-01','one-turn'):
        assert entries==[(101,2500000)], 'adjacent route and launch energy'
    if name=='two-hop':assert entries==[(101,2500000),(102,2450000)], 'two-hop fixed attenuation'
    if name=='three-hop':assert entries==[(101,2500000),(102,2450000),(103,2400000)], 'three-hop fixed attenuation'
    if name=='route-tie-reverse':assert entries==[(101,2500000),(104,2450000)], 'route tie reversed link ordering'
    if name=='range-exhaustion':
        assert entries==[(101+i,2500000-i*50000) for i in range(50)], 'finite attenuation range'
    if name=='empty-two-bolts':assert entries==[(101,5000000),(102,4900000),(103,4800000)], 'volley-scaled fixed attenuation'
    if name=='fractional-count':assert energies==[2500000], 'quantity integer conversion'
    if name=='route-tie':assert entries==[(102,2500000),(104,2450000)], 'route tie link ordering'
    if name in ('quiet-origin','no-bolts','zero-turns','zero-sector-reprompt','cancel-count','negative-count','oversized-count','invalid-sector','hole-sensors','volley-reload','planet-reload'):
        assert not energies and not entries, 'non-launch preserves volley'
    if name=='route-dead-end':
        assert energies==[2500000] and not entries and "You can't get there without going someplace you dont want to!" in command_text, 'unreachable route consumes launch'
    if name=='mixed-defense':
        receipts=('destroyed 1 fighters!','destroyed 1 mines in sector 101!','The plasma bolts hit Enemy','destroyed 5 mines in sector 101!','The plasma bolts hit planet')
        positions=[command_text.find(r) for r in receipts]
        assert all(i>=0 for i in positions) and positions==sorted(positions), 'mixed absorption and wreck order'
    if name in ('own-sector','own-sector-cloaked'):
        assert entries==[(100,2500000)] and get(after,2,53)<get(before,2,53) and get(after,2,61)<get(before,2,61), 'self-target damage'
    if name in ('enemy-ship','cloaked-ship','team-ship'):
        assert get(after,3,53)<get(before,3,53), 'indiscriminate ship damage'
    if name=='ship-fighters':
        assert get(after,3,61)<get(before,3,61) and get(after,3,53)==get(before,3,53), 'ship fighters shield absorption order'
    if name in ('fighters-enemy','fighters-self','fighters-two-bolts'):
        destroyed=sum(int(v) for v in re.findall(r'The plasma bolts destroyed (\d+) fighters!',text))
        assert destroyed>0 and get(before,152,81)-get(after,152,81)==destroyed, 'sector fighter casualty receipt'
    if name in ('mines-only','fighter-spill'):
        destroyed=sum(int(v) for v in re.findall(r'The plasma bolts destroyed (\d+) mines in sector 101!',command_text))
        assert destroyed>0 and get(before,152,129)-get(after,152,129)==destroyed, 'sector mine casualty receipt'
    if name in ('enemy-ship','cloaked-ship','team-ship','ship-fighters','two-ships','lethal-ship'):
        receipts=re.findall(r'shields to (\d+) units and destroying (\d+) fighters!',command_text)
        assert len(receipts)==1, 'ship casualty receipt count'
        if get(after,3,45)==0:
            assert get(after,3,53)==int(receipts[0][0]) and get(before,3,61)-get(after,3,61)==int(receipts[0][1]), 'saved ship casualty receipt'
        else:
            # DOS leaves precombat shields in the dead record; the death identity
            # and tracking receipt, not that stale cache, establish destruction.
            assert int(receipts[0][0])==0 and get(after,3,57)==0, 'fatal ship casualty receipt'
    if name.startswith('hole-') and name!='hole-sensors':
        hole=1051 if name=='hole-1051' else 592
        assert entries and entries[0]==(hole,2500000), 'hole encountered on route'
        assert re.search(r'The plasma bolt is deflected by a black hole in sector '+str(hole)+r' to sector [1-9][0-9]*!',text), 'hole deflection receipt'
        if name=='hole-target-defenses':
            assert get(after,643,81)==get(before,643,81) and get(after,643,85)==get(before,643,85), 'hole before defenses'
    if name in ('planet-small','planet-zero','planet-organic-small','planet-zero-empty','planet-impact-zero'):
        assert 'The planet was destroyed!!' in text and get(after,152,93)==0 and get(after,4053,85)==0 and get(after,4053,73)==0, 'planet destruction link cleanup'
        assert all(get(after,4053,o)==0 for o in (45,49,53,57,61,65,77)), 'planet destruction resources'
    if name in ('planet-productive','planet-no-ore-stock','planet-self','planet-team'):
        assert 'The plasma bolts hit planet' in text and 'The planet was destroyed!!' not in text, 'planet hit and survivor receipt'
        assert all(0<get(after,4053,o)<get(before,4053,o) for o in (45,49,53,77)) and get(after,152,93)==2, 'surviving planet damage'
        ground=re.search(r'Ground forces reduced by (\d+) units to (\d+)!',command_text)
        assert ground and get(after,4053,77)==int(ground.group(2)) and get(before,4053,77)-get(after,4053,77)==int(ground.group(1)), 'saved ground casualty receipt'
    if name=='lethal-ship':
        assert get(after,3,45)==2 and get(after,3,57)==0 and 'Enemy  was destroyed!' in text, 'ship death attribution'
        credits=re.search(r'  -  Credits: (\d+)',text);holds=re.search(r'  -  (\d+) empty holds',text)
        assert credits and holds and get(after,2,81)-get(before,2,81)==int(credits.group(1)) and get(after,2,65)-get(before,2,65)==int(holds.group(1)), 'salvage saved receipt'
    if name=='two-ships':
        assert get(after,3,53)<get(before,3,53) and get(after,4,53)==get(before,4,53), 'ordered shared ship energy'
    if name in ('planet-zero-projection','planet-small-projection'):
        assert get(before,151,93)==2 and get(before,152,93)==0 and 'There is no planet in this sector.' not in command_text, 'projection loads intended planet'
        assert 'Target Planet' in command_text and not energies, 'unfired planet projection receipt'
        assert all(get(after,4053,o)>100 for o in (45,49,53)), 'lazy surplus production projection'
        assert get(after,4053,85)>0 and get(after,4053,73)==3, 'projection planet survives decline'
    if name=='planet-impact-zero':
        assert 'Productivity reduced by 0 units to 0 units!' in command_text, 'zero projected production receipt'
    if name=='planet-reload':
        assert get(after,152,93)==0 and get(after,4053,85)==0 and get(after,4053,73)==0, 'planet deletion survives reload'
    assert_footprint(name,before,after)

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
    # Reviewed ranges are independently checked against the immutable MZ image.
    assert NATIVE_RANGES, 'unfrozen native declarations'
    binary=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
    assert sha(binary)==BINS['YT.EXE'], 'native binary identity'
    image=loaded(binary)
    ledger_path=root/'rea/ledger.json'
    assert sha(ledger_path.read_bytes())==NATIVE_LEDGER_SHA, 'native ledger identity'
    ledger=read(ledger_path)
    assert ledger['target']=='archive/dos-original/YT.EXE' and ledger['target_sha256']==sha(binary), 'native ledger target'
    header=struct.unpack_from('<H',binary,8)[0]*16
    assert ledger['header_bytes']==header and ledger['module_bytes']==len(image) and ledger['relocations']==struct.unpack_from('<H',binary,6)[0] and ledger['load_segment']=='0x1000', 'native ledger geometry'
    count=0
    for filename,ranges in NATIVE_RANGES.items():
        records=read(root/'rea'/filename)['records'];seen=set()
        assert len(records)==len(ranges)+1, 'native observation count'
        images=[r for r in records if r['operation']=='inspect_native_load_image']
        assert len(images)==1, 'native load image count'
        verify_load_image(images[0],binary,image)
        assert images[0]['evidence_id']==ledger['load_image_evidence_id'], 'native image evidence identity'
        ledger_reads={r['address']:r for r in ledger['reads']}
        assert set(ledger_reads)==set(ranges) and len(ledger_reads)==len(ledger['reads']), 'native ledger ranges'
        for e in records:
            if e['operation']!='read_bytes':continue
            v=e['normalized_result'];address=v['address']
            assert address in ranges and address not in seen, 'native address set';seen.add(address)
            size=ranges[address];at=int(address,16)-0x10000
            assert e['subject']['digest']['sha256']==sha(binary), 'native target identity'
            assert v['complete'] and v['requested_bytes']==v['returned_bytes']==size, 'incomplete native bytes'
            assert 0<=at<at+size<=len(image) and bytes.fromhex(v['bytes_hex'])==image[at:at+size], 'native bytes'
            r=ledger_reads[address]
            assert r['evidence_id']==e['evidence_id'] and r['length']==size and r['file_offset']==header+at, 'native source mapping'
            assert r['file_bytes_sha256']==sha(binary[header+at:header+at+size]) and r['loaded_bytes_sha256']==sha(bytes(image[at:at+size])), 'native source/loaded digests'
            assert e['analysis_profile']['digest']==ledger['analysis_profile_digest'], 'native analysis profile'
        assert seen==set(ranges), 'native address set';count+=len(seen)
    return count

def verify_control(directory,decl,case,baseline,worlds,auxiliaries):
    name=case['name'];d=directory/name
    assert re.fullmatch(r'[a-z0-9-]+',name), 'scenario path'
    assert case==read(d/'result.json') and all(case[k]==v for k,v in decl.items()), 'manifest/declaration mismatch'
    assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA and case['binaries']==BINS, 'binary/session identity'
    assert case['date']==decl.get('date','10/24/2026') and case['time']==decl.get('time','00:00:00'), 'declared clock identity'
    assert case['timeout_seconds']==decl.get('timeout',120), 'capture timeout declaration'
    assert case['complete'] and case['program_returned'] and not case['timed_out'], 'incomplete DOS control'
    assert set(case['files'])==KEEP and {p.name for p in d.iterdir()}==KEEP|{'result.json.gz'}, 'retained file set'
    for file,digest in case['files'].items():assert sha((d/file).read_bytes())==digest, ('file hash',name,file)
    clock(d,case)
    assert (d/'RETURN.LOG').read_bytes()==b'PLASMA_PROGRAM_RETURNED\r\n', 'DOS return marker'
    before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz');assert len(before)==len(after)==568687, 'world size'
    if case.get('parent'):
        assert case['parent'] in worlds, 'parent ordering'
        expected=bytearray(worlds[case['parent']]);patches=decl['patches']
        for r,o,v in patches:put(expected,r,o,v)
        initial=auxiliaries[case['parent']]
    else:
        expected,patches=setup(decl,baseline)
        initial={p.name:p.read_bytes() for p in SOURCE.iterdir() if p.suffix.upper() in ('.DAT','.ASC','.DEF','.TMP') and p.name!='YTDATA.DAT'}
    assert case['applied_patches']==patches, 'declared patch list'
    assert before==expected, 'undeclared setup or broken world chain'
    assert {n:bytes.fromhex(v) for n,v in read(d/'side-before.json').items()}==initial, 'auxiliary input chain'
    auxiliary=read(d/'sidefiles.json');final={n:bytes.fromhex(v['hex']) for n,v in auxiliary.items()}
    assert all(v['after_sha256']==sha(final[n]) and v['before_sha256']==(sha(initial[n]) if n in initial else None) for n,v in auxiliary.items()), 'auxiliary identity'
    assert (d/'KEYS.TXT').read_bytes()==('\r~~~~~\r~'+decl['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode(), 'exact input stream'
    text=(d/'transcript.txt').read_text()
    assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text, 'raw transcript identity'
    semantics(case,before,after,text)
    assert sha(after)==WITNESSES[name]['world'], 'frozen complete world witness'
    assert sha(text.encode())==WITNESSES[name]['transcript'], 'frozen complete transcript witness'
    assert witness_aux(final)==WITNESSES[name]['aux'], 'frozen complete auxiliary witness'
    return after,final

def verify(root):
    assert RECIPE_SHA and WITNESSES and BINS and FOOTPRINT, 'unfrozen plasma declarations'
    directory=root/'dos';baseline=(SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline)==BASE_SHA and zipped(directory/'baseline.dat.gz')==baseline, 'baseline identity'
    recipe_bytes=(directory/'recipe.json').read_bytes();assert sha(recipe_bytes)==RECIPE_SHA, 'frozen declarations'
    recipe=json.loads(recipe_bytes);manifest=read(directory/'results.json')
    assert recipe['recipe']==manifest['recipe']==RECIPE and recipe['source']==str(SOURCE.relative_to(ROOT)), 'recipe identity'
    declarations={c['name']:c for c in recipe['scenarios']};rows={c['name']:c for c in manifest['scenarios']}
    assert len(rows)==len(manifest['scenarios'])==len(declarations)==len(WITNESSES), 'scenario count'
    assert set(rows)==set(declarations)==set(WITNESSES)==set(FOOTPRINT), 'scenario identity'
    binaries={n:(ROOT/('archive/analysis/yt-combat' if n=='KEYFEED.COM' else 'archive/dos-original')/n).read_bytes() for n in BINS}
    assert {n:sha(b) for n,b in binaries.items()}==BINS, 'archived binary identity'
    worlds={};auxiliaries={}
    for name,decl in declarations.items():
        try:worlds[name],auxiliaries[name]=verify_control(directory,decl,rows[name],baseline,worlds,auxiliaries)
        except AssertionError as error:raise AssertionError(f'{name}: {error}') from error
    reads=verify_native(root)
    chains=sum(bool(c.get('parent')) for c in declarations.values())
    print(f'Verified {len(rows)} returned plasma controls, {chains} exact world/auxiliary reload chains and {reads} native byte observations.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-plasma');verify(p.parse_args().research)
