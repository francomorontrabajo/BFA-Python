import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import time
import asyncio
from web3 import Web3

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "http://bfa:8545")
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
SMART_CONTRACT_ADDRESS = os.getenv("SMART_CONTRACT_ADDRESS")
CONTRACT = None
NETWORK_ID = None
CHAIN_ID = None

with open("./contract/abi.json") as f:
    SMART_CONTRACT_ABI = json.load(f)

web3 = Web3(Web3.HTTPProvider(RPC_URL))

def setup_web3():
    global CONTRACT, CHAIN_ID, NETWORK_ID

    if not (WALLET_PRIVATE_KEY and WALLET_ADDRESS and SMART_CONTRACT_ADDRESS and SMART_CONTRACT_ABI):
        print("❌ Error: Debes establecer las variables de entorno.")
        exit(1)

    if not web3.is_connected():
        print("❌ Error: No se pudo conectar a", RPC_URL)
        exit(1)

    CONTRACT = web3.eth.contract(
        address=SMART_CONTRACT_ADDRESS,
        abi=SMART_CONTRACT_ABI
    )

    CHAIN_ID = web3.eth.chain_id
    NETWORK_ID = web3.net.version

    print(f"""✅ Conectado exitosamente:
    > host: {RPC_URL}
    > chainId: {CHAIN_ID}
    > networkId: {NETWORK_ID}
    > account: {WALLET_ADDRESS}
    > contract: {SMART_CONTRACT_ADDRESS}
    """)

setup_web3()

class HashesModel(BaseModel):
    hashes: List[str]

async def wait1block(max_attempts: int = 10, interval: float = 0.5):
    """Espera hasta que aparezca un bloque nuevo o devuelve error por timeout"""
    start_block = web3.eth.block_number
    attempts = 0

    while attempts < max_attempts:
        current_block = web3.eth.block_number
        if current_block > start_block:
            return current_block
        await asyncio.sleep(interval)
        attempts += 1

    raise TimeoutError("Timeout. Tal vez el nodo local no está sincronizado.")


def stamp_hashes(hashes: List[str]):
    """Envia los hashes al smart contract"""
    # Normalizamos: agregamos 0x si falta
    hashes = [h if h.startswith('0x') else '0x'+h for h in hashes]

    # Convertir strings a bytes32
    hashes_bytes32 = [bytes.fromhex(h[2:]).ljust(32, b'\0') for h in hashes]

    # Construir la transacción
    tx = CONTRACT.functions.put(hashes_bytes32).build_transaction({
        'from': WALLET_ADDRESS,
        'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
        'gas': 300000,
        'gasPrice': web3.to_wei('1', 'gwei')
    })

    # Firmar la transacción
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=WALLET_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction) 

    return web3.to_hex(tx_hash)

def verify_hash(h):
    """Verifica un hash en el contrato"""
    if not h.startswith('0x'):
        h = '0x' + h
    h_bytes32 = bytes.fromhex(h[2:]).ljust(32, b'\0')

    count = CONTRACT.functions.getObjectCount(h_bytes32).call()
    if count == 0:
        raise ValueError("No existe el hash en la base de datos")

    # Traemos información básica: blockNo de la primera aparición
    block_no = CONTRACT.functions.getBlockNo(h_bytes32, WALLET_ADDRESS).call()
    return {"hash": h, "count": count, "first_block": block_no}


app = FastAPI()

@app.get("/")
def read_root():
    return {"Status": "Ok", "Message": "Hello INTI!"}

@app.get("/status/network")
def check_connection():
    if web3.is_connected():
        return {"Status": "OK", "NetworkId": NETWORK_ID, "ChainId": CHAIN_ID}
    return {"Status": "ERROR"}

@app.get("/status/contract")
def status_contract():
    if CONTRACT:
        return {
            "Status": "OK",
            "ContractAddress": SMART_CONTRACT_ADDRESS,
            "Functions": [fn.fn_name for fn in CONTRACT.functions]
        }
    else:
        return {"Status": "ERROR", "Error": "Contrato no inicializado"}

@app.get("/status/account")
def status_account():
    try:
        balance = web3.eth.get_balance(WALLET_ADDRESS)
        return {
            "Status": "OK",
            "Address": WALLET_ADDRESS,
            "BalanceWei": balance,
"BalanceEther": web3.from_wei(balance, "ether")
        }
    except Exception as e:
        return {"Status": "ERROR", "Error": str(e)}

@app.get("/status/tx/{tx_hash}")
def status_tx(tx_hash: str):
    try:
        receipt = web3.eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            return {"Status": "Pending"}
        return {
            "Status": "Confirmed",
            "BlockNumber": receipt.blockNumber,
            "GasUsed": receipt.gasUsed,
            "ContractAddress": receipt.contractAddress
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/wait1block")
async def api_wait1block():
    try:
        block_no = await wait1block()
        return {"success": True, "blocknumber": block_no}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stamp")
def api_stamp(data: HashesModel):
    if not data.hashes or not isinstance(data.hashes, list):
        raise HTTPException(status_code=422, detail="La clave 'hashes' debe ser un array")

    try:
        tx_hash = stamp_hashes(data.hashes)
        return {"status": "success", "txHash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/verify/{hash_value}")
def api_verify(hash_value: str):
    try:
        info = verify_hash(hash_value)
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))