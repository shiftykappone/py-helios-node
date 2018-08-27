import time
import random
import logging
import json

from evm import MainnetChain
from evm.chains.mainnet import (
    MAINNET_GENESIS_PARAMS,
    MAINNET_GENESIS_STATE,
    GENESIS_PRIVATE_KEY,
)

from evm.db.backends.level import LevelDB
from evm.db.chain import ChainDB
from evm.rlp.transactions import BaseTransaction

from eth_utils import (
    encode_hex,
    decode_hex,        
)

from p2p.kademlia import Address, Node

from p2p.constants import LOCAL_PEER_POOL_PATH

from eth_hash.auto import keccak

from eth_keys import keys
from sys import exit

from trie import (
    HexaryTrie,
)

from evm.db.hash_trie import HashTrie

from evm.db.chain_head import ChainHeadDB

from evm.constants import random_private_keys

logger = logging.getLogger("dev_tools_testing")

#random_private_keys = [b'\xd3.MQ\x1f\xb2SMN\x9c\xea\xc5\x05t#\xca! Da\xd3"\x0f[\x00xr\xf4Z>ui', b'Y\xd8\x16TO\x11\x18\x10~$\x13\xf9\xb4 W\xaa\xd6y\xeb\x1b\x1a\xd3\x8aRd\xbc6\xbeG\xecNi', b']\xaal\x02d\x12\x86\xe9Yg\x84]\x0fD]6\xa7\t\xe7\xf9\xa0\x13X\x94\xc2\x82q\xdd\xae\x9a\x9a\xa9', b']\xa9V??=\xc7*\\x\xbbaS\x9c\x89\xc9\t\x98\x16X\x8a>\x1a\xb9"\xfb\xec\xa0%\x12\xa3Z', b'\x94;\x18\xe4\xa8\xc2,\xc7\xfe\xec:\x82\x8f\x08\xec\xdf7\xb6\xcff\xd7\x04\xf4\xbaF>\xf4\xaf\xbd\x96\xeb\x95', b"\x83YXg\xbf\x95\xb5\x1c\xd7\x96&w;\xe8L\x0cw\xe1,b7\x92!f\xe8\xa6'\x11_n\xa6/", b'\x9f\x99\x01T\xd9\xbb\xb0\xdby}\xeeR\x8d[\xb5wm\xa4k+\x9bi\x8a\x11\xec\xc3Y\xb6\xdf\xc9\xe5\x1e', b'y\xd0\x98:\x0c\xb9\xe5`\xf93.?],\xd3[\x08\xca\xd5\xc9$\xda\xa3\x89\xbf\xebj\x8b\xcc\xff\xd2\x04', b'\xea7\xc9\xb3\x95\xfdP#R\xab\xa6\x18$\xab\xabsN\xe0\x97\xd2ka\xa4\xa9@\xb1\xbd\xd5\xeb\xd4\xfa\x94', b'\x8ck?\xba>\xae\xbf\xd6\xf2\xecKe\x81${>\xd2\x90P\x1b\xd8\x9a\x95\x1e\xcf\x1f\r\x1c x\x86\xa5']
#random_private_keys = [b'n\xdb\xbd\xf4\xe1\xa6\xe4\x15\xb2\x94D\xd3\x86u6Og\xae\x9cZa\x92\xd3\xd7U\x04?Ka\xe7<\xbb', b'\xbda\x0f\x8d=vQ\x92\x19:\x8bTn\x05\xf1\xfe\xc5\xc3\x9d\x9c\x80{<a\xc4\x01\xcf\xa3\x99\xbf\x98g', b"!K\xf9\xd9\xea\x1d\x11\xe4\xe4jB#c\xcd;P^\xf0&N\x0f\xa9\xb8'K\xd4\xa0\xff\x81\xfc\xa2p", b'V\xe1\x95\xe6\x18f\x04e4\tSzr\x13\x03O\xe5\xfa\xb1\xa5\x0e\x1b\xe6\x8e\x16\xae\xa9[\x8d\x8e\xe1!', b"3l\x10\x810s\x1f\xebKs}\xbc\xeb\xd6\nPV\xcf;\xc3^\x94m\x01m\xc3\xfd\x17'\xb0\x9bx", b'B\x85\xd4\x9f\xff\x08\xf3<$\xd3oY f\x1f~\x00\xb3\x1b\x0e\xac(\xc7\xcakc\xfeB&g\x95;', b'\xe6\xfb\x04\xcf\xf8\x8f\x8a@\xa9\xe4_\xfa\x8c9b$@\xf1\xfft\xbe\x8d\xdd\xa6\xbcb\x1a\xc7\xfc\xcd\x88\xe8', b'1\x9a\xab\x92\xcfQ\x10uO\xac\xd2\xf9\xd0_a\x12\xae\x9aF\xe9\xdb\x881$\xca^\xfe%[?J\xe4', b"b~\xd9`\xe3J\x87\xd3E\x893\xfbO\x97\x1a\x9c\xd2\xc7\xb6\xe5\xd4\xcc\x82\xb6\xb2'#\xfc\x8d\x86M\x84", b'\xd4\x8b\x9b\x05\x8c\xe5\xbbO\x93\xddp\x86\xf9&\x16%\xc7&\xe1\xe14\xfc\xb8N\x8b\xcd\xe23G#H\xdb', b'\xdf,\xc6\xcaE\x84\x01\xfa\xbf#\x10\x86\x03\xccU\x8c\xd87\xe6\xf7\x7fK\x94\xef\xe6\x17;q\x1eb\x02\n', b'+Rf\xce_\xb5\xfa\x98%?B\x03\x90\x10\xce\xf8\x08\x83J+x\x0c r.\xe2\x9c\xe7\x892\xc2\xfd', b'U\xafe\x95\x9c_+&p\xf6\xd2\xb0W\t\x8f\xeb\x06c\x88z\x9f\xe7\xfc\xf7\xf6\xa7;\x96Y\x06\xddH', b'\xf7\x0fh\xff\xb3\x049}\xc7*bn\x9e\xf2\xe6C\xb1A\xb4q/0\xfd\xa0r\x01E\x7f-\xfc|\xfc', b'\xa0\xa5\xb4u\xba\x13c\xf5\x04\xdcSP;\x1br=\xa1\t\xc2\xd2f0\xe7\xb3\x08\xfc\x11\xd6\xe3\xf6\xc8\xd7', b'\x1b7\xb6\x08#o\xc1\xb5/:-\x95\x19<\xff\xdeE\x06\xce\xbd7\xa4\xf4\x1dm\xb7\xa72b\xf2\xe94', b"\xb1J\xaf\xac\xfeX\x90j\xbb\x15;\x93\xdc\xfe\x0cn[ ;\x0c\xdbL!'\xa0\xae\xe2\xbe\xb6?\xb6\xfd", b'R\x82\xc9\xef\xbc\tS\x95[\xd7\xa0q\xe57\xb3<\x0b\x94\xc1A\x8d\x0b\xa5-\x90\x02\xcd\xa91|)\xf4', b"\xe6'\xd6C\xd2\xdc3\xb9\xb5\xf0\xeaQ\xd3\xb8\xa3Bj\xc6X\xff\xfe\xa6\xbc\x89p\xde&\xd0\x9d\x81\xf1(", b'}\xc9p\xd9\xa2\x10{\x93R\x8a\x94\xe9R\xe6\xc0\x0b4\xd1\xad\x9e\x81}g\xeeY\xb8)\xdf\x8c.\x88\x99', b'\xe6\x10\x9f\x9a\x9f\x99\xb0+V\xb7#\xf0N\xe7\x99D\xfa\xb1\x1c\xabL\x12kP\x8fB\xf2\xd4\xd5\xfb#\xa1', b'\xb8\x12\x15p\x9dD$e\xbb\x1a\x7f\xbc\x97/\xaey0~\xdd\xa1]r\x90o\xfe(\xb1\xe6?\xa0\xb7\x03', b"\xe9\xa4'\xf6y$\x94\xc6\xe3b\x82v\x1a\x1c@\x18\x03\x98\xc6\x89\x8e\xf5\xc5\xe4\x02\xa7,!Li0\xe3", b'\xacb\xb5\xa8\xcc\xacP\x99\xf5b<MT4\xc3\x8f\x82\xae<\xcd_\x08\x80d\xb6\xf0\xd8\x92\x11\x18\x96s', b'Rn\xa7\x07O\xd2\xc0\xec\x95[\xd6$\xac\xe1\xc1\xb0\xe8\x85\x8ev\xb6"\x1b\xca\x92\xcd\x06\xefFb\x9b}', b"5cZ\xde\x80A\x0b4\xa7\x9c\xff'\x17\xde\xd3\x1c\x0f@}\x173\xa2x\xf4\xb7W\xd0\xef#Jo\x02", b'\xbe\xb9\x00f\x97\x0e\xdfn.\xddC\xa5,\x1e\x98\xa3$\xec\xfe\x04\xb96C1g\x9f\rY:1\xa4\x88', b'm:5i+\x0c\xb1z\xbf\xa4\xbc^\x10\x01\x8c\xcd\xcc)\x1b\xaa\xc2_\xb83%\xb69\xbab\xab\xdb\xad', b'\x08\xdcl\xaf\xdd\xc0y7~\x89\xbd\x19\x94\x1f6\xf6\x9e\x03\xa1\xcf\x04hi\xac\xc3\xb6\xe4\x8cr\xc2\x83@', b"'T\xd1\xf4\xfcSw\xaf\x8a\xf7R\x86\x9fDY\x14\xfa\xd8[J\xe1\xf3\xe6<=\x17n\xa2o\xa0\x91\x85", b"\xb4\xd6\xac\xb0+\x18J\xe9\x82\xcb\xc0\xe7f\x87\x8e\nh<\x11\xe1S\xc9So\xf4\xabl\xb1\xec\xb2\x9c'", b'1\xeb\xbf\x9b\xde\xf8d-\xdbw\x0f\xbe<\x08\xe83\xc4\x8a\x8f\x0c`\xf6\xcd\xb3\x91\xa2\xc7\xe2\xa4j\r\xd6', b'?hT\x8e7}\xee0\xe4<\xa4F\xcc\xf7x\xc9\x9e<x\x1c;\x0bJs\x12\xa3\xf9c\xbb\x1f\xcc\x1c', b'\x13\xa0\x03\xec\xe31\xdb\xf0W\xfe\xbc\xa8\xfb\x89\x81X\xdc>\xcd}@\xf9\x13\xb90\xfd\x93\xb0\xf1\xdf\x0b\xd6', b'_)\xbd\x02e\x823\xd47A\xd0\x8e\x9fm.\x19\xabT\xe9\xafdF\xdb\xa8\x13\x0b\x0f\xf6\xba\xa3\xc6I', b'\xfc\xf2\x88\x9e\xd6\xc2\n\x12\x03\xc9\xb9b@\x82\xde\xe2\xd1\xf26\xfb\xfa\x9e\xa0\xdf\xd4I3S\xb2,\x81\x87', b'\xfc\xa0\x84\x8b\'h\xc6\xad\x15]N\x19"\x0c\xd5\xc5\xfa\xe40K\x95C\xb2\x99\x9a\x83h\xe9\x0e\xdc4\xee', b'\xc1\xe2\x80}k\x8bHO\xa1O\xeb\x9d\xe9\xac\xc9\xf9,\xe4K\xb8\x0f\x86\x8f\xf8\xfc)\xae\xb5\xf8n+\xb9', b'\xae+\x00\xf0\xd7\x89Q\x0e<\xbc\x88X\xa6\xa6\xd7\xeb\x16\xdcR\xc5wn\x88!\x91\xd8\x11ojD\x8b"', b'\x882\xb2\xcf\xc7L\xdb\xaff\xd1\xc9\n\x01\x90\xc6C\xc8\x81\xd3\xac\x1d\xc9*g\xc8\xf2;\xa5\x88\xae\x06\xc1', b'\xb4\xec\x07\xb2\xf1\x9e\xb2\x92\x11\x17\xef*\xea\\\xb0~S*\xf1\xe5\xb4"\xe09\x08\xa7\x96\x8af\xef\xaa^', b'ht>:n\x1d\xeeP\x00\xcd\x0b\xb9o*\x02H\xc7-\xe0i\x9bG\xc3~\xa5\xfaz\x11A\xb4\\\xce', b'X\xa8&eh\x9f*G6Ud\xd2\x99\xa2\x19\x1c?3\xd0)\x1b\x07\x8c\x93\x08#\xbd+\x18O+\xbb', b',\xa3\xe7~\xf8*\xaf\xd3\xdd\xa8Y\x8a.E&6S\r\x0c\x86\x14\x1f\x1b\xc9xJ\xba\xd4$\x18\xe1\xcd', b'q\xe5c\xda\xb1Cb\x17\x0e*&\xafB\xf0\x84S\xe52\xdf\xeb\xf2\xe7\xf2\x93X\x02\x97\xd1\xdfI\xaa\xc7', b'\x1b9\xb4\x8dN\x9a\xf9\t\xf2P\xf59{\xc513\x17\x93\x10\x9b\x88\xfb)k\xae\x8d\x9eT.\xb2\x8d\x88', b'_\x13\x13\x01[\x8fe\x1e\xf1\x9e\xbf\xa8\xaef->$22a\xadL{\xef\xf9 \xeb\\U\xc3\xf1\x9e', b'(\\"\x15\xa9\xd6h\x9c&\xc6r\x91lh\xabZ\xaa\xc1\x19u\x0cQ\x04\xdc\xa4\xb5\xfb\x14\x9a\x8f$\x85', b'($\xb6i\x7f\x81xi\x85Eo\xe1\x14\xf3A\xa3\x83+V\xaf\xe3\x11\xf2!nsn\xf2\xe4\xb4\xae\r', b'w\t\x96\xf3\xe7m!\xdb\xc1\xfc\x1b<E\x9f \xf7\xb8:\x0bU\xd1y\xf9\xce\xe0!\xc5\xd8x\xa5\xf3\xe5', b'\xaem\xc5\x81\xae\x03u\xb5\xdc\xfa\xb1\x8b\x9f\xfdLH\xc2\xe1\xb0\xbb%\x14\xe4\xf0G\x97\xd9=D\xc6b\x90', b'Tr}\xe1\x06\xc4j\x80\x11\xf5\xc0\x99f\x8c\xd84X\x07\xff\\\xb8\x88K\xf5K\xd3=O\xe3v\\\\', b'6\xb2\xd15;\x01$\x82{dam\xc6\x80\x88\xa3\x81E\xfc\xd2$\x9a\xb5\xc2\xb9\x12\x10\x85\xe1yp-', b'\x8f}\xf4\xbd\xaeW\xb8\xcd_r\xf6\tZ\x1c\xa5\x8a\xe7t\x86\x12\xf8\xf8\xdao\xf5\xa4\xb2\xc5\x81q @', b";\xb5\x87\xba\xd8\xf3\xc0>\xcd\xbc|\xc4v\x87'\xfa\x1c\xb4\xfc\x04\xb31i\x80\x98\n;$\xdfk\xecg", b'\xc0\xaci?h<\x88\xda\x16\xb8h6\xc7CB\xb4\xae\x0f\x0f3\x05\xd4\xd2p\xb8=\x98Y4\xa9\xa6\x83', b'=\xe4\x05!]\xbfB\x86\xd1\xf9\xa4\x91\xa7\xc8\xcfH\xd9\xd4\xd7\x1e\x9a\xf8>\xdaP\x06\x1b\x06\xda\xdc\xd0\xbe', b'\xff\xf4\x8c\xaf\xa9J\xfa5=\xf7x\x00\xe2V\xd9@\x17\xdb\xa9\x879\x84\xa8L\xb09\xa5\x99\xb7\x08\xa8\x9c', b'\xd7\xe5\xa5\x8bYTCHH\xdb$i\xd1\xd4H\x9f\x840\x10@#\xbe\x88\xa4\xd3\xec\xba\x06\xc0\xae\xb23', b'5\x00\xcb\x97m\x14^)(\x83\x9f\xf4\xa7\xb4S\x98\xb1\x00A\xecz\x81\xd38Dl\xe3Z-\x91\xb6\x83', b'\x86\xa2\xbcL\x1cj_\rY\xd0\xedGG*a\xb7\x85\xd0\x81\x8b\x12\x1aN\x0cZcx\xfe\x17\xf4\xd8\x89', b"*\x99\x07e`\xf7\xc58)F\x8a~*Z\x1a\x02\xb1l\x82D\x92+b9\x9b\xd1\xa0\xd9\x8b\xc6'\x17", b'\xf68\xad\xb4\x1c?\x80\xa5\xb9v+\xd1\xce\xa8$\x7f\ni\xf1\x05\xb1\xe1\xdf`#\x88\xed(rP\x88{', b'c+&\xe8\x96\xc8\n\xfd`\xd8\xaf\xe2\xa0g\x88\x87\xc3\xd4\x95Z\xe8H^\xc2\xc2_\xd1\x83\xaf\xb0\xa5\x99', b'\xd4\x89G\x08\xa0\x0c\x02Z\xd6\xac\x0bx6\x9f\xe9R3><\xfb\xc4#\xdf\x8a\x8a\x81\xf9\xedo\xd94\x19', b'\xff\xa9\x08\xd1\xb5\xd4ta\x8c\xe2s\xc3%\xdf_\xed/\xf0D\xb7\x18aD\xd2\x0b\x11\x9b\xd8w\xe1\x98\xd0', b"S\xae~\xb4\x8d\x83yp\xeb\xa0\xfeC\x08'^\xb6\xab\xad\x8c\xc9\xcf(a\xdc\x8d\xe9\xa7)A*\t\xe4", b'\xff\x99\xe1c\xa0\x10\xce0`\xab\xe4\xd0\x95[\x15\xea\x8c\x11\xb01\xc2C,\xa3\xf0\xa0\xe1\x0e\xc3\xaaB\xdf', b'Y\xccMu\x0f5\xba\xac\xd4RQ\x1b\xeb\xd8mD5\xce\x84\x12@[\xa3\x12\xa7\xbc\x96\xb6\xd1p\xc3V', b'\x08\xb7\x8e\xf5]\xb9\xefV\xb0\xdc\xfc\x07\x99\x9f\x15X\xc5\x83\x1cI>\xd9\xa8\xa1\xf5zp\x8a\xa7yV\x0b', b'R\xdeh\x17\xe5\x97\xff\x83\xc7\xbft]\x04\x06\x9a\xf2\xa6\x1a\xaa~q\x9e\x86N\xecp\xc3Z\xf3\xfa\tn', b'\xaa\x08S\xf8\x9b\xaf\xedG\xafM7\\<\x90\x97\xdd\xda\x12\xb7\xae\xe2c\x7f\x0f\xfa\x8a\xb0\xe1\xfd3j\xe0', b'\x9c\xea\xe9X\xad\x85\xe8\xf6\x13#b\x05;\xfe\xfae\xd5s\xf6\xc6I\xd3\xb2\xcb\xf9\xda$t\xe4\xee"\x82', b'\xc8/#\xb2\x8e\x81\xe4=\xb7\xce\x0b\x1a\\\xb2\xed\xbd\xf3@,@\xf1\x0en\x88\xaf\xefe\xdfX\xb4\xe8\xd8', b'\x14\x1d\xeb\xfc%\xe7\xa5\xc7v*\xe6\x07\xb229-P\x85\x82&\xc3\xcf{\xae\x14l\xf4G:\xa8g[', b'"x\x80\x03:\xbc\xe1\xbc=e\x83\xb5\x17\x15\x99\x80\xbcm\xe0r<\xf7\x15g&\xe4\xe8\xbb\xb6\xb7N\xee', b'!\x876\xd3\xe5\xe4\x7f\x96\x84\xf8Jm\x98\xa6\x12\x0bL\xd7\xfa\xea\xbfN\xfe-\xea\x9a\xeb\x8f\x8d\xa2}P', b'0\xb37e\x87\xd6\xc0\xf3\xad\x8ft\xf2\xf1g\xbe\xbf\x16Tw8\xb6\xb6-\xb6*\xd0\xcb2=\xb1\x07\xda', b'\xaf<\xa7\x017\x88\\\x93\r\xd4\xbb\x0b\x10m\xc7m`\xaa\xaaZ\xd4\xedu\x1fZ\x97\x02\xaf\xb4\x9e9\xf3', b'\xfa\xab\x93\x9b+^t\xec\xa6:w\x01\x87\x92\x81,\x1eW\x91\x05\xdb%\x1bvb\xbaZ@\xdf\x0c\xd6\x06', b'\xba\x92 \xef\x1c\xdcz\xb5\xe0\x8cP\r\xb2\x1a6\xd4\x83}\x01\xe20\xb5\xf1\xa0\xbb\x90\xb6p\xc9Sa\xb3', b'\xd6\xad@\xfc\xbf(\x11}>\xd0\x16\x02@2\x02IS\xfc\xfd<\xd2\n\x93\x13J\x06\x9cPE\xad\x0f\x86', b'\xfc\xb3\x08\xab\x7f\xf9K\x88\xd5\x1b\xcfQ+DN\x039\xceh\t;\x86ww\r\xe2$[\xdd\xb5\x9a\xdd', b'0\x07\x04{I\xbf\xc7\x0c\xdd\x9b\xa2\x18\x7f\x01\th\xf8\x1b.\xdaI\xf2\x04\xde0>N\xebv\xb3Y_', b'\x86\x9d\xdf\xb9b\x8e\xd2\xafS\xce\r\xc3dw\xfa"\xbd\x18{\xed\x11\x0e\xfb\x99@o\xa9\x00?tM\x89', b'T\x9c\xbeF\xcf\x8b{>4\x7fI0\xfc\xc2u%\xccn\x8d<\x0e\x06\x9e\x1b\x01\xee\\%\x18\x14\x08g', b'\x14\xa6O\xa3\x17\xe1.\xed!\xd6w\xa0ll\x90\xb3\xfeRhD~\xb0"\x0c<\x1e\xc0cX:%\x98', b'&hW\xc6\xb4JT\xd3\xe9\x90\xd8\xb5\xe6E\x83/\x01\x9d\xe6\x96*/\xfds\xddN\xef\xd2\xbb\xe7\x9f\xe5', b'\xf4\x88\x89;\xd8\xd6Osa\xbe\xdfU\xff|]v\xfb\xc5\xf7e\xf7\x83\x07}:\xa2\xed\x80\x90r\x9d\xdd', b'KN\xd9>u\x8eg\xb23\xc9\x1b\x9d\xc2\xb1\xb2\x8fc\xb4\xaa\xaa>\xe1<\xe7\xba\xee\xadE\xa2\x7f\x9c\xf7', b'\xe8\x0e\xb0\xb5]\xc7\x11^p\xf0\x90\x05\x85\x0e\x1a8\n`$\\\xb1sTNX\x06\x0f_\x99\xa6\xe1F', b'\xb3\xcd\xb5\xf9n\xfd\xb5\xd0\x90T\x04G\xa0\xb9M\xf4\xb2\xbb\xcb\x0c\x18DS\xe7u\xe7\xc6K4tVK', b'\x17\\\xf3\xc1\x01\xa0Z\x1fv=OY5\xdeg\xfeG\xb7\xdc\x15ls\x15\x96\xcbNU)\x8eX\xfa\xa0', b'\xbbS\x92P,Z3\xc4\xa5\x87P\xf4\x9a\x1f\xe5N\x04\xd8C+Q\xb20\xd1k\xcf\x89|Wpt\x14', b'\xd0\xbe\xb6\xc7\xb2\x02\r\x1ar\xbd3\xfav\xb0\x98\xf2\x8a\xa6^t\xbe\xdb\xd9**[\xdb\xc5\xd5c\x84\xd2', b"8\x80\xb5{|lr$\xe7t\xc2\xcb\xef\x0ek\xd8x\\\x01\xeeb\x92rz\xf4Z\x10\xb4'\x03\xecj", b'\x8d\xc7\xc3\xff:\x84\x01\x9a\x1f\x9a\x02\xa6\x93M\xb1\x14{\xb3G\xc0^\xc5\xe1\xfe\xbaF\xff\x7f\xff\xfb\xdbZ', b'\x92\x86H\xc1\xc7\x0f\x81\xed\xbf\xdf\xf7\xec@\x82\xac\r\xac\xc0\xb1]\xb3\x92]\xd5\xe6\xf8\xe5\xda\x9fe\x15\xde', b"\x00\xc4\xb8\xb5\x0eA\x98B\x9e\xc1G\x10z\xdd}\xcd\xfd6P\x85T\xb4C\xb2\x9b\x05\x94\xe8'x\x1e\xc5", b'\xb9\x00\xe1N\xf2\xf6\x10r\x8aK\x9b\x19\x87L\x80\x858*<_\t"\xd9\xba4i>\x00A\xc6c(']

def create_dev_test_random_blockchain_database(base_db):
   
    logger.debug("generating test blockchain db")
        
    #initialize db
    sender_chain = import_genesis_block(base_db)
    
    sender_chain.chaindb.initialize_historical_minimum_gas_price_at_genesis(min_gas_price = 1, net_tpc_cap=5)
    
    order_of_chains = []
    #now lets add 100 send receive block combinations
    for i in range (5):
        random.shuffle(random_private_keys)
        if i == 0:
            privkey = GENESIS_PRIVATE_KEY
            receiver_privkey = keys.PrivateKey(random_private_keys[0])
        else:
            privkey = receiver_privkey
            receiver_privkey = keys.PrivateKey(random_private_keys[0])
        
        sender_chain = MainnetChain(base_db, privkey.public_key.to_canonical_address(), privkey)
        
        #add 3 send transactions to each block
        for j in range(2):
            sender_chain.create_and_sign_transaction_for_queue_block(
                    gas_price=0x01,
                    gas=0x0c3500,
                    to=receiver_privkey.public_key.to_canonical_address(),
                    value=10000000000000000-i*800000-random.randint(0,1000),
                    data=b"",
                    v=0,
                    r=0,
                    s=0
                    )
        
        imported_block = sender_chain.import_current_queue_block()
#        print("imported_block_hash = {}".format(encode_hex(imported_block.hash)))
#        receivable_tx = sender_chain.get_vm().state.account_db.get_receivable_transactions(receiver_privkey.public_key.to_canonical_address())
#        print('receivable_tx from account = {}'.format([encode_hex(x.sender_block_hash) for x in receivable_tx]))
#        exit()
        
        order_of_chains.append(encode_hex(privkey.public_key.to_canonical_address()))
        
        logger.debug("Receiving ")
        
        #then receive the transactions
        receiver_chain = MainnetChain(base_db, receiver_privkey.public_key.to_canonical_address(), receiver_privkey)
        receiver_chain.populate_queue_block_with_receive_tx()
        imported_block = receiver_chain.import_current_queue_block()
        
        imported_block_from_db = receiver_chain.chaindb.get_block_by_number(imported_block.header.block_number, receiver_chain.get_vm().get_block_class(),receiver_privkey.public_key.to_canonical_address())

        logger.debug("finished creating block group {}".format(i))
    
    order_of_chains.append(encode_hex(receiver_privkey.public_key.to_canonical_address()))
    
    #print("order_of_chains")
    #print(order_of_chains)
    #print(sender_chain.chain_head_db.get_historical_root_hashes())
    
    
def create_dev_fixed_blockchain_database(base_db):
    #not finished yet
    logger.debug("generating test fixed blockchain db")
        
    #initialize db
    sender_chain = import_genesis_block(base_db)
    
    privkey = GENESIS_PRIVATE_KEY
    receiver_privkey = keys.PrivateKey(random_private_keys[0])

    sender_chain = MainnetChain(base_db, privkey.public_key.to_canonical_address(), privkey)
    
    #add 3 send transactions to each block
    for j in range(2):
        sender_chain.create_and_sign_transaction_for_queue_block(
                gas_price=0x01,
                gas=0x0c3500,
                to=receiver_privkey.public_key.to_canonical_address(),
                value=10000000000000000-i*800000-random.randint(0,1000),
                data=b"",
                v=0,
                r=0,
                s=0
                )
    
    imported_block = sender_chain.import_current_queue_block()
#        print("imported_block_hash = {}".format(encode_hex(imported_block.hash)))
#        receivable_tx = sender_chain.get_vm().state.account_db.get_receivable_transactions(receiver_privkey.public_key.to_canonical_address())
#        print('receivable_tx from account = {}'.format([encode_hex(x.sender_block_hash) for x in receivable_tx]))
#        exit()
    
    logger.debug("Receiving ")
    
    #then receive the transactions
    receiver_chain = MainnetChain(base_db, receiver_privkey.public_key.to_canonical_address(), receiver_privkey)
    receiver_chain.populate_queue_block_with_receive_tx()
    imported_block = receiver_chain.import_current_queue_block()
    
    imported_block_from_db = receiver_chain.chaindb.get_block_by_number(imported_block.header.block_number, receiver_chain.get_vm().get_block_class(),receiver_privkey.public_key.to_canonical_address())

    logger.debug("finished creating block group {}".format(i))
    
    #print(sender_chain.chain_head_db.get_historical_root_hashes())
    
    
    
def import_genesis_block(base_db):
   
    logger.debug("importing genesis block")
        
    #initialize db
    return MainnetChain.from_genesis(base_db, GENESIS_PRIVATE_KEY.public_key.to_canonical_address(), MAINNET_GENESIS_PARAMS, MAINNET_GENESIS_STATE)
    #return MainnetChain.from_genesis(base_db, GENESIS_PRIVATE_KEY.public_key.to_canonical_address(), GENESIS_PRIVATE_KEY, MAINNET_GENESIS_PARAMS, MAINNET_GENESIS_STATE)
 
    
    
def save_random_private_keys(limit):
    
    private_keys = []
    for i in range(limit):
        seed = bytes(random.randint(0,100000000))
        private_keys.append(keccak(seed))
            
    print(private_keys)
    
#save_random_private_keys(100) 
    
    
def load_peers_from_file():
    path = LOCAL_PEER_POOL_PATH
    #load existing pool
    with open(path, 'r') as peer_file:
        existing_peers_raw = peer_file.read()
        existing_peers = json.loads(existing_peers_raw)
    return existing_peers

def load_local_nodes(local_private_key = None):
    existing_peers = load_peers_from_file()
    peer_pool = []
    for i, peer in enumerate(existing_peers):
        if local_private_key is None or peer[0] != local_private_key.public_key.to_hex():
            peer_pool.append(Node(keys.PublicKey(decode_hex(peer[0])),Address(peer[1], peer[2], peer[3])))
    return peer_pool
        

    