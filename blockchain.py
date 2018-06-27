#!/usr/bin/python3
"""
blockchain.py                                                        2018.01.24
 The best way to learn about blockchains is to make one.
 python3.6, virtualenv + virtualenvwrapper, Flask==0.12.2 requests==2.18.4
"""
# imports
import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse


class Blockchain(object):
    # Constructor for the Blockchain class -- this will be used to instantiate
    # a Blockchain.
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block (root block)
        self.new_block(previous_hash=1, proof=100)

    # Instantiate our Node
    app = Flask(__name__)

    # Generate a globally unique address for this Node
    node_identifier = str(uuid4()).replace('-', '')

    # Instantiate the Blockchain
    blockchain = Blockchain()

    def new_block(self, proof, previous_hash=None):
        # Creates a new Block and adds it to the chain.
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm.
        :param previous_hash: (Optional) <str> hash of the previous Block.
        :return: <dict> New Block
        """
        block = {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': self.current_transactions,
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.chain[-1]),
                }
        # reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        # Adds a new transaction to the list of transactions.
        """
        Creates a new transaction to go into the next mined Block.

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction.
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        # hashes a Block
        """
        Creates a SHA-256 hash of a Block

        :param block: <dict> Block
        :return: <str> the hash
        """
        # We must make sure that the Dictionary is Ordered, or we'll have
        # inconistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns the last Block in the chain.
        return self.chain[-1]

    """
    Understanding Proof of Work
    ---------------------------
    A Proof of Work(PoW) algorithm is how new Blocks are created (or mined) on
    the blockchain. The goal of PoW is to discover a number which solves a
    problem. The number must be *difficult*to*find*but*easy*to*verify* --
    computationally speaking -- by anyone on the network. This is the core idea
    behind Proof of Work.

    The rule implemented below for our PoW algorithm is as follows:

        Find a number p such that when hashed with the previous block's
        solutions a hash with four leading zeroes is produced.

    An easy way to adjust the difficulty of the algorithm is to modify the
    number of leading zeroes needed. For our simple example, four is enough;
    even adding a single zero to the rule increases the time needed by an
    exponential amount.

    In Bitcoin, the PoW algorithm is called Hashcash, and it isn't too
    different from the rule implemented below.
    """
    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
            - Find a number p' such that hash(pp') contains 4 leading zeroes,
              where p is the previous p'.
            - p is the previous proof, and p' is the new proof.

        :param last_proof: <int> the previous Proof
        :return: <int> the new Proof
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain four leading
        zeroes?

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False otherwise
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    """
    The Mining Endpoint
    -------------------
    This is where the 'magic' happens. The 'magic' can be broken down into
    three things:
        1. Calculate the Proof of Work.
        2. Reward the miner(us) by adding a transaction granting us one coin.
        3. Forge the new Block by adding it to the chain.
    """
    @app.route('/mine', methods=['GET'])
    def mine():
        # We run the Proof of Work algorithm to get the next proof.
        last_block = blockchain.last_block
        last_proof = last_block['proof']
        proof = blockchain.proof_of_work(last_proof)
        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
        blockchain.new_transaction(
                sender="0",
                recipient=node_identifier,
                amount=1,
                )
        # Forge the new Block by adding it to the chain.
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)
        response = {
                'message': "New Block Forged.",
                'index': block['index'],
                'transactions': block['transactions'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                }
        return jsonify(response)

    @app.route('/transactions/new', methods=['POST'])
    def new_transaction_flask():
        values = request.get_json()
        # check that the required fields are in the POST'd data
        required = ['sender', 'recipient', 'amount']
        if not all(k in values for k in required):
            return 'Missing values', 400
        # create a new transaction
        index = blockchain.new_transaction(values['sender'],
                                           values['recipient'],
                                           values['amount'])
        response = {'message': f'Transaction will be added to Block {index}'}
        return jsonify(response), 201

    @app.route('/chain', methods=['GET'])
    def full_chain():
        response = {
                'chain': blockchain.chain,
                'length': len(blockchain.chain),
                }
        return jsonify(response), 200

    """
    Consensus
    =========
        It's all very well if we have a blockchain for ourselves, but the whole
    point of blockchains is that they're decentralized, meaning there is more
    than one node in the network. But if we have multiple nodes in the network,
    how do we ensure that everyone has the same chain? (or know whose chain is
    the authoritative one?

        This is where Consensus comes in. Our consensus algorithm will allow us
    to resolve any conflicts that occur. However, in order to even have any
    conflicts there must be a way to discover new nodes in our network and
    register them to keep track of them.

        In our simple example here, an easy to understand (and more
    importantly, easy to implement,) rule should be utilized and such an
    algorithm can be described as follows: "The longest, valid chain is
    authoritative." id est, the longest chain on the network is the de-facto
    chain.

        First, in order to use our Consensus algorithm to resolve conflicts in
    the network, we must implement a method for validating a given chain. The
    mehtod valid_chain() takes a Blockchain as an argument and returns a
    boolean value to signify if the argument chain is a valid one or not.
        Specifically, it sets up the process by initializing 'last_block' to
    the genesis (or root) block in the chain and sets 'block' to the second
    block in the chain. For each block in the chain, valid_chain() checks to
    see if the previous hash of the current block is equal to the self.hash()
    function with the previous block as an argument; if they are equal, update
    'last_block' to the current block and increment the counter.
    """
    def valid_chain(self, chain):
        """
        Determine if a given Blockchain is valid.

        :param chain: <list> A blockchain
        :return: <bool> True if valid, False otherwise.
        """
        last_block = chain[0]
        current_index += 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n=-~-=-~-=-~-=-~-=-~-=-~-=-~-=\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        This is our Consensus algorithm described above. It resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: <bool> True if our chain was replaced, false otherwise
        """
        neighbours = self.nodes
        new_chain = None
        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        # Grab and verify the chains from all the nodes in our network
        for node in neigbours:
            response = requests.get(f"http://{node}/chain")
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # Replace our chain if we discovered a new, valid chain longer than
        # ours.
        if new_chain:
            self.chain = new_chain
            return True
        return False

    """
    Registering New Nodes
    ---------------------
    Each Node should keep a registry of neighbouring Nodes in our network.
    Thus the following endpoints are needed:
        /nodes/register : this will accept a list of new Nodes as URLs
        /nodes/resolve  : will be the Consensus algorithm, to resolve conflicts
    """
    def register_node(self, address):
        """
        Add a new Node to the list of Nodes.

        :param address: <str> Address of Node. e.g. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
