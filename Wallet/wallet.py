# Import dependencies
import subprocess
import json
from dotenv import load_dotenv
import os
from pprint import pprint
from eth_account import Account

# Load and set environment variables
load_dotenv()
mnemonic=os.getenv("MNEMONIC")

# Import constants.py and necessary functions from bit and web3
# YOUR CODE HERE
from constants import *
from web3 import Web3
from web3.middleware import geth_poa_middleware
from bit import wif_to_key
from bit import PrivateKeyTestnet
from bit import PrivateKey
from bit import Key
from bit.network import NetworkAPI

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

 #set gas price strategy
from web3.gas_strategies.time_based import medium_gas_price_strategy
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

 # Create a function called `derive_wallets`
def derive_wallets(coin = BTC,mnemonic = mnemonic,numderive = 3 ):
    command = f'php ./derive -g --mnemonic="{mnemonic}" --cols=all --coin={coin} --numderive={numderive} --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.
coins = {'eth': derive_wallets(mnemonic=mnemonic, coin=ETH, numderive=3),
        'btc-test': derive_wallets(mnemonic=mnemonic, coin=BTCTEST, numderive=3)}
#pprint(coins)

# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    global account
    if coin == ETH:
        account =Account.privateKeyToAccount(priv_key)
    else:
        account = PrivateKeyTestnet(priv_key)
    return account

bitcoin_priv_key = coins['btc-test'][0]['privkey']
btc_key =  priv_key_to_account(BTCTEST, bitcoin_priv_key)
#pprint(btc_key)

ether_priv_key = coins['eth'][0]['privkey']
eth_key = priv_key_to_account(ETH, ether_priv_key)
#pprint(eth_key)

# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, recipient_address, amount):
    global cre_data
    if coin == ETH: 
        value = w3.toWei(amount, "ether")
        gasEstimate = w3.eth.estimateGas(
            {"to": recipient_address, "from": account.address, "amount": value}
            )
        cre_data= {
            "to": recipient_address,
            "from": account.address,
            "amount": value, 
            "gas": gasEstimate, 
            "gasPrice": w3.eth.generateGasPrice(), 
            "nonce": w3.eth.getTransactionCount(account.address), 
            "chainID": w3.eth.chainID,
        }
        return cre_data
    else:
        cre_data = PrivateKeyTestnet.prepare_transaction(account.address, [(recipient_address,amount,BTC)])
        return cre_data


#create transaction BTC
trns_create = create_tx(BTCTEST, btc_key,'mhU1v1bn6w9goZsunDRaRrz25zfRNDSXa4', 0.0001)
#pprint(trns_create)


# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, recipient_address, amount):
    if coin == ETH:
        raw_tx = create_tx(coin, account, recipient_address, amount)
        signed = w3.eth.signTransaction(raw_tx)
        return w3.eth.sendRawTransaction(signed.rawTransaction)

    if coin == BTCTEST:
        raw_tx = create_tx(coin, account, recipient_address, amount)
        signed = account.sign_transaction(raw_tx)
        return NetworkAPI.broadcast_tx_testnet(signed)

#Send transaction BTC
trns_send = send_tx(BTCTEST, account, 'mhU1v1bn6w9goZsunDRaRrz25zfRNDSXa4',  0.0001)
pprint(trns_send)
