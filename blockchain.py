#!/usr/bin/python3
"""
 blockchain.py                                                        2018.01.24
 The best way to learn about blockchains is to make one.
 python3.6, virtualenv + virtualenvwrapper, Flask==0.12.2 requests==2.18.4
"""

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

    def new_block(self):
        # Creates a new Block and adds it to the chain.
        pass

    def new_transaction(self):
        # Adds a new transaction to the list of transactions.
        pass

    @staticmethod
    def hash(block):
        # hashes a Block
        pass

    @property
    def last_block(self):
        # Returns the last Block in the chain.
        pass
