import datetime
import hashlib
import json

import psycopg2
from flask import Flask, jsonify


class Blockchain:

    def __init__(self):
        self.conn = psycopg2.connect(dbname='test', user='test', password='test', host='localhost')
        self.conn.autocommit = False

    def create_block(self):
        cursor = None
        block = None
        proof = None
        previous_hash = None
        timestamp = datetime.datetime.now()
        try:
            cursor = self.conn.cursor()

            # Get last block
            cursor.execute(f"SELECT index, proof, previous_hash, timestamp FROM transactions ORDER BY index desc LIMIT 1 FOR UPDATE")
            last_block = cursor.fetchone()
            print(f"Last block: {last_block}")

            if not last_block:
                proof = 1
                previous_hash = '0'
            else:
                last_block = {'index': last_block[0], 'proof': last_block[1], 'previous_hash': last_block[2], 'timestamp': str(last_block[3])}
                proof = self.proof_of_work(last_block['proof'])
                previous_hash = self.hash(last_block)

            # insert to db
            cursor.execute(f"INSERT INTO transactions(proof, previous_hash, timestamp) VALUES ({proof}, '{previous_hash}', '{timestamp}') RETURNING *")
            new_block = cursor.fetchone()
            new_block = {'index': new_block[0], 'proof': new_block[1], 'previous_hash': new_block[2], 'timestamp': str(new_block[3])}
            print(f"New block: {new_block}")
            self.conn.commit()

            block = new_block
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: ", error)
            self.conn.rollback()
        finally:
            if not cursor:
                cursor.close()

        return block

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_all_block(self):
        cursor = None
        blocks = None
        try:
            cursor = self.conn.cursor()
            # Get all block
            cursor.execute(f"SELECT index, proof, previous_hash, timestamp FROM transactions")
            blocks = cursor.fetchall()

        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: ", error)
            self.conn.rollback()
        finally:
            if not cursor:
                cursor.close()

        return blocks

    def chain_valid(self):
        cursor = None
        try:
            cursor = self.conn.cursor()

            # Get all block
            cursor.execute(f"SELECT index, proof, previous_hash, timestamp FROM transactions")
            blocks = cursor.fetchall()

            previous_block = blocks[0]
            index = 1
            while index < len(blocks):
                block = blocks[index]

                if block[2] != self.hash(previous_block):
                    return False

                previous_proof = previous_block[1]
                proof = block[1]
                hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
                if hash_operation[:5] != '00000':
                    return False

                previous_block = block
                index += 1

        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: ", error)
            self.conn.rollback()
        finally:
            if not cursor:
                cursor.close()

        return True


app = Flask(__name__)
blockchain = Blockchain()


@app.route('/mine_block', methods=['GET'])
def mine_block():
    block = blockchain.create_block()
    if not block:
        response = 'Error'
    else:
        response = jsonify(block)
    return response, 200


@app.route('/display_chain', methods=['GET'])
def display_chain():
    chain = blockchain.get_all_block()
    response = {'chain': chain,
                'length': len(chain)}
    return jsonify(response), 200


@app.route('/valid', methods=['GET'])
def valid():
    valid = blockchain.chain_valid()
    if valid:
        response = {'message': 'The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
