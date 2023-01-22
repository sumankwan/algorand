from algosdk.v2client import algod
from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk.mnemonic import to_private_key
import json

algod_address = "https://testnet-api.algonode.cloud"
algod_client = algod.AlgodClient("", algod_address)

asset_creator_address = "KLJ35ACNKEVAP5RBVPFMOXNPGANDZJSPQXKK3OIFLYVRMCKUCERSFT3FYU"
passphrase = "track dwarf panic oven retreat echo daughter vague mango kick predict advice subject pause rail knife blast security fever survey reduce december kit able squeeze"

private_key = to_private_key(passphrase)

txn = AssetConfigTxn(
    sender=asset_creator_address,
    sp=algod_client.suggested_params(),
    total=1000,
    default_frozen=False,
    unit_name="LATINUM",
    manager=asset_creator_address,
    reserve=asset_creator_address,
    freeze=asset_creator_address,
    clawback=asset_creator_address,
    url="https://path/to/my/asset/details",
    decimals=0,
)

signed_txn = txn.sign(private_key)
# Send the transaction to the network and retrieve the txid
try:
    txid = algod_client.send_transaction(signed_txn)
    print("Signed transaction with txID: {}".format(txid))
    # Wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
    print("TXID", txid)
    print("Result confirmed in round: {}".format(confirmed_txn["confirmed-round"]))
except Exception as err:
    print(err)
# Retrieve the asset ID of the newly created assets by first ensuring that the creation transaction was confirmed, then grabbing the asset id from the transaction
print("Transaction information: {}".format(json.dumps(confirmed_txn, indent=4)))
