#!/usr/bin/env python3
# Copyright (c) 2017-2022 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
""" An exercice functional test

Create a new test file. Set it up to have 3 nodes. 
Add an outbound P2P connection to the 3rd node. 
Create a mempool transaction and submit it to node 1. 
How can you confirm that the P2P connection recieved the transaction?
"""
import threading
from test_framework.p2p import (
    P2PInterface,
)

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

p2p_lock = threading.Lock()

class TestP2PConn(P2PInterface):
    def __init__(self):
        super().__init__()
        self.last_message = {}
        
    def wait_for_tx(self, txid, timeout=60):
        if not self.last_message.get('tx'):
            return False
        return self.last_message['tx'].tx.rehash() == txid
        
class ExampleTest2(BitcoinTestFramework):
    
    def add_options(self, parser):
        self.add_wallet_options(parser)
    def set_test_params(self):
        self.setup_clean_chain = False
        self.num_nodes = 3
        self.rpc_timeout = 120
        
    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def setup_network(self):
        self.setup_nodes()

        self.connect_nodes(0, 1)
        self.connect_nodes(1, 2)
        
        self.sync_all()


    def run_test(self):
        # Add an outbound P2P connection to the 3rd node. 
        peer_receiving = self.nodes[2].add_outbound_p2p_connection(TestP2PConn(), p2p_idx=0, connection_type="outbound-full-relay")
        
        # Generate blocks to obtain coins on Node 2 & get out of IBD
        self.generate(self.nodes[2], 101)
        self.sync_all()

        # Get a new address from Node 1
        address = self.nodes[1].getnewaddress()

        # Create a transaction from Node 2 to Node 1
        txid = self.nodes[2].sendtoaddress(address, 10.0)

        # Manually submit the transaction to Node 1's mempool
        raw_tx = self.nodes[2].getrawtransaction(txid)
        self.nodes[1].sendrawtransaction(raw_tx)

        self.sync_all()

        # Wait for Node 2's P2P connection to receive the transaction 
        peer_receiving.wait_for_tx(txid)
        
        # pdb.set_trace()
        # Check if Node 2's P2P connection received the transaction
        assert peer_receiving.last_message['tx'].tx.rehash() == txid
        self.log.info("P2P connection on Node 2 received the transaction")


if __name__ == '__main__':
    ExampleTest2().main()


