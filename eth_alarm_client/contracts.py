import os
import json

from populus.contracts import Contract


BASE_DIR = os.path.dirname(__file__)
CONTRACT_ABI_PATH = os.path.join(BASE_DIR, 'contracts.json')


contract_json = json.loads(open(CONTRACT_ABI_PATH).read())


future_block_call_meta = contract_json['FutureBlockCall']
FutureBlockCall = Contract(future_block_call_meta, "FutureBlockCall")


call_lib_meta = contract_json['CallLib']
CallLib = Contract(call_lib_meta, "CallLib")
