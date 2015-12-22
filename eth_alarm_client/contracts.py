import os
import json

from populus.contracts import Contract


BASE_DIR = os.path.dirname(__file__)
CONTRACT_ABI_PATH = os.path.join(BASE_DIR, 'versions', 'v0.6', 'contracts.json')


contract_json = json.loads(open(CONTRACT_ABI_PATH).read())


future_block_call_meta = contract_json['FutureBlockCall']
FutureBlockCall = Contract(future_block_call_meta, "FutureBlockCall")
