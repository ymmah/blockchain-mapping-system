from state import State
from block import Block, BlockHeader
from utils import big_endian_to_int, \
    parse_as_bin, parse_as_int, normalize_address
from config import Env
from db import RefcountDB


def block_from_genesis_declaration(genesis_data, env):
    h = BlockHeader(timestamp=parse_as_int(genesis_data["timestamp"]))
    return Block(h, [])


def state_from_genesis_declaration(
        genesis_data, env, block=None, allow_empties=False, executing_on_head=False):
    if block:
        assert isinstance(block, Block)
    else:
        block = block_from_genesis_declaration(genesis_data, env)

    state = State(env=env)
    for addr, data in genesis_data["alloc"].items():
        addr = normalize_address(addr)
        assert len(addr) == 20
        if 'balance' in data:
            state.set_balance(addr, parse_as_int(data['balance']))
        if 'nonce' in data:
            state.set_nonce(addr, parse_as_int(data['nonce']))
    #get_consensus_strategy(state.config).initialize(state, block)
    if executing_on_head:
        state.executing_on_head = True
    state.commit(allow_empties=allow_empties)
    rdb = RefcountDB(state.db)
    block.header.state_root = state.trie.root_hash
    state.changed = {}
    state.prev_headers = [block.header]
    return state

def mk_basic_state(alloc, header=None, env=None, executing_on_head=False):
    env = env or Env()
    state = State(env=env, executing_on_head=executing_on_head)
    if not header:
        header = {
            "number": 0, "timestamp": 1467446877
        }
    h = BlockHeader(timestamp=parse_as_int(header['timestamp']))
    state.prev_headers = [h]

    for addr, data in alloc.items():
        addr = normalize_address(addr)
        assert len(addr) == 20
        if 'balance' in data:
            state.set_balance(addr, parse_as_int(data['balance']))
        if 'nonce' in data:
            state.set_nonce(addr, parse_as_int(data['nonce']))

    state.block_number = header["number"]
    state.timestamp = header["timestamp"]
    state.commit()
    return state