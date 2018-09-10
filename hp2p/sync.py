import logging
import time

from hvm.chains import AsyncChain
from hvm.constants import (
    BLANK_ROOT_HASH,
    FAST_SYNC_CUTOFF,
)
from hvm.db.backends.base import BaseDB
from hvm.db.chain import AsyncChainDB

from hp2p.cancel_token import CancelToken
from hp2p.peer import PeerPool
from hp2p.chain import FastChainSyncer, RegularChainSyncer
from hp2p.service import BaseService
from hp2p.state import StateDownloader


# How old (in seconds) must our local head be to cause us to start with a fast-sync before we
# switch to regular-sync.



class FullNodeSyncer(BaseService):
    logger = logging.getLogger("hp2p.sync.FullNodeSyncer")

    consensus = None
    chain: AsyncChain = None
    chaindb: AsyncChainDB = None
    base_db: BaseDB = None
    peer_pool: PeerPool = None
    syncing_to_timestamp = None
    
    def __init__(self,
                 chain: AsyncChain,
                 chaindb: AsyncChainDB,
                 base_db: BaseDB,
                 peer_pool: PeerPool,
                 chain_head_db,
                 consensus,
                 node,
                 token: CancelToken = None,
                 
                 ) -> None:
        super().__init__(token)
        self.node = node
        self.consensus = consensus
        self.chain = chain
        self.chaindb = chaindb
        self.base_db = base_db
        self.peer_pool = peer_pool
        self.chain_head_db = chain_head_db
        
        

    async def _run(self) -> None:
        latest_chain_head_root_timestamp = self.chain_head_db.get_latest_timestamp()
        #head = await self.wait(self.chaindb.coro_get_canonical_head())
        # We're still too slow at block processing, so if our local head is older than
        # FAST_SYNC_CUTOFF we first do a fast-sync run to catch up with the rest of the network.
        # See https://github.com/ethereum/py-evm/issues/654 for more details
        #if latest_chain_head_root_timestamp < time.time() - FAST_SYNC_CUTOFF:
        
        #TODO: create consensus class that saves each peer's chain head root hash to their object. It should also label who is in the majority
        # Fast-sync chain data.
        self.logger.info("Starting fast-sync")
        #chain_syncer = FastChainSyncer(self.chain, self.chaindb, self.chain_head_db, self.base_db, self.peer_pool, consensus = self.consensus, token = self.cancel_token, node = self.node)
        self.chain_syncer = RegularChainSyncer(self.chain, self.chaindb, self.chain_head_db, self.base_db, self.peer_pool, consensus = self.consensus, token = self.cancel_token, node = self.node)
        await self.chain_syncer.run()

        # Ensure we have the state for our current head.
        #head = await self.wait(self.chaindb.coro_get_canonical_head())
#        if head.state_root != BLANK_ROOT_HASH and head.state_root not in self.base_db:
#            self.logger.info(
#                "Missing state for current head (#%d), downloading it", head.block_number)
#            downloader = StateDownloader(
#                self.base_db, head.state_root, self.peer_pool, self.cancel_token)
#            await downloader.run()

        # Now, loop forever, fetching missing blocks and applying them.
#        self.logger.info("Starting regular sync")
#        # This is a bit of a hack, but self.chain is stuck in the past as during the fast-sync we
#        # did not use it to import the blocks, so we need this to get a Chain instance with our
#        # latest head so that we can start importing blocks.
#        new_chain = type(self.chain)(self.base_db)
#        chain_syncer = RegularChainSyncer(
#            new_chain, self.chaindb, self.peer_pool, self.cancel_token)
        #await chain_syncer.run()

    async def _cleanup(self):
        # We don't run anything in the background, so nothing to do here.
        pass


def _test():
    import argparse
    import asyncio
    from concurrent.futures import ProcessPoolExecutor
    import signal
    from hp2p import ecies
    from hp2p.peer import ETHPeer, HardCodedNodesPeerPool
    from hvm.chains.ropsten import RopstenChain
    from hvm.db.backends.level import LevelDB
    from tests.p2p.integration_test_helpers import (
        FakeAsyncChainDB, FakeAsyncRopstenChain, LocalGethPeerPool)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('-db', type=str, required=True)
    parser.add_argument('-local-geth', action="store_true")
    args = parser.parse_args()

    chaindb = FakeAsyncChainDB(LevelDB(args.db))
    chain = FakeAsyncRopstenChain(chaindb)
    privkey = ecies.generate_privkey()
    if args.local_geth:
        peer_pool = LocalGethPeerPool(ETHPeer, chaindb, RopstenChain.network_id, privkey)
    else:
        discovery = None
        peer_pool = HardCodedNodesPeerPool(
            ETHPeer, chaindb, RopstenChain.network_id, privkey, discovery,
        )
    asyncio.ensure_future(peer_pool.run())

    loop = asyncio.get_event_loop()
    loop.set_default_executor(ProcessPoolExecutor())

    syncer = FullNodeSyncer(chain, chaindb, chaindb.db, peer_pool)

    sigint_received = asyncio.Event()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, sigint_received.set)

    async def exit_on_sigint():
        await sigint_received.wait()
        await syncer.cancel()
        await peer_pool.cancel()
        loop.stop()

    loop.set_debug(True)
    asyncio.ensure_future(exit_on_sigint())
    asyncio.ensure_future(syncer.run())
    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    _test()