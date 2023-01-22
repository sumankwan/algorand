from algosdk.v2client import algod
from algosdk.future.transaction import (
    AssetConfigTxn,
    wait_for_confirmation,
    AssetTransferTxn,
    AssetFreezeTxn,
)
from algosdk.mnemonic import to_private_key
import json

# Define parameters
algod_address = "https://testnet-api.algonode.cloud"
algod_client = algod.AlgodClient("", algod_address)
account1 = "7XBHR7UM6G5VM6JVBQUIUTQY2XREF4PNJX75P4VQGIPLRT3NHS35KPROSE"
passphrase1 = "drive parade alarm permit loud option roof absorb health own basic umbrella scrub music mother capital bounce web art wealth penalty meat own above escape"
private_key1 = to_private_key(passphrase1)
account2 = "BDJJBU4T5XQ2OEDQB7UVFSI2XNEY3IFTAIFHWZVZB2XAGYVKBI6ZFRNPDA"
passphrase2 = "misery chaos virus grant again repeat ladder oppose pig baby assist sample goat cable fame indicate piano draft side have cattle cart silent absorb sense"
private_key2 = to_private_key(passphrase2)
account3 = "RKTKEAXTMNWFWOE6WTGMUATRGU35DKZS4IAVGHII4T7AYC2SJH6HDDHDW4"
passphrase3 = "car place pistol boost nature riot glimpse toss traffic claim allow toilet oppose seminar balcony fashion vendor chef gold miracle stay still game abstract spare"
private_key3 = to_private_key(passphrase3)
params = algod_client.suggested_params()


# Define functions to retrieve asset information
def print_created_asset(algodclient, account, assetid):
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["created-assets"]:
        scrutinized_asset = account_info["created-assets"][idx]
        idx = idx + 1
        if scrutinized_asset["index"] == assetid:
            print("Asset ID: {}".format(scrutinized_asset["index"]))
            print(json.dumps(my_account_info["params"], indent=4))
            break


def print_asset_holding(algodclient, account, assetid):
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["assets"]:
        scrutinized_asset = account_info["assets"][idx]
        idx = idx + 1
        if scrutinized_asset["asset-id"] == assetid:
            print("Asset ID: {}".format(scrutinized_asset["asset-id"]))
            print(json.dumps(scrutinized_asset, indent=4))
            break


# 1. CREATE ASSET
# account1 creates an asset called ALGOFIN and sets account2 as the manager, reserve, freeze, and clawback address.
txn_create = AssetConfigTxn(
    sender=account1,
    sp=params,
    total=1000,
    default_frozen=False,
    unit_name="ALGOFIN",
    manager=account2,
    reserve=account2,
    freeze=account2,
    clawback=account2,
    url="https://path/to/my/asset/details",
    decimals=0,
)

# Sign transaction
signed_txn_create = txn_create.sign(private_key1)

# Execute transaction
try:
    txid_create = algod_client.send_transaction(signed_txn_create)
    print("Signed transaction for asset creation with txID: {}".format(txid_create))
    confirmed_txn_create = wait_for_confirmation(algod_client, txid_create, 4)
    print("TXID for asset modification", txid_create)
    print(
        "Result for asset creation confirmed in round: {}".format(
            confirmed_txn_create["confirmed-round"]
        )
    )
except Exception as err:
    print(err)
print(
    "Transaction information for asset creation: {}".format(
        json.dumps(confirmed_txn_create, indent=4)
    )
)

# Check pending transaction
try:
    ptx = algod_client.pending_transaction_info(txid_create)
    asset_id = ptx["asset-index"]
    idx = 0
    print_created_asset(algod_client, account1, asset_id)
    print_asset_holding(algod_client, account1, asset_id)
    # print(json.dumps(account_info1["assets"][0], indent=4))
except Exception as err:
    print(err)

# 2. CHANGE MANAGER
# The current manager(account2) issues an asset configuration transaction that assigns account1 as the new manager.
# Keep reserve, freeze, and clawback address same as before, i.e. account2
txn_modify = AssetConfigTxn(
    sender=account2,
    sp=params,
    index=asset_id,
    manager=account1,
    reserve=account2,
    freeze=account2,
    clawback=account2,
)

# Sign transaction
signed_txn_modify = txn_modify.sign(private_key2)

# Execute transaction
try:
    txid_modify = algod_client.send_transaction(signed_txn_modify)
    print("Signed transaction for asset modification with txID: {}".format(txid_modify))
    confirmed_txn_modify = wait_for_confirmation(algod_client, txid_modify, 4)
    print("TXID for asset modification: ", txid_modify)
    print(
        "Result for asset modification confirmed in round: {}".format(
            confirmed_txn_modify["confirmed-round"]
        )
    )

except Exception as err:
    print(err)

print_created_asset(algod_client, account1, asset_id)

# 3. OPT-IN
account_info = algod_client.account_info(account3)
holding = None
idx = 0
for my_account_info in account_info["assets"]:
    scrutinized_asset = account_info["assets"][idx]
    idx = idx + 1
    if scrutinized_asset["asset-id"] == asset_id:
        holding = True
        break
if not holding:
    txn_optin = AssetTransferTxn(
        sender=account3, sp=params, receiver=account3, amt=0, index=asset_id
    )
    signed_txn_optin = txn_optin.sign(private_key3)

    # Execute transaction
    try:
        txid_optin = algod_client.send_transaction(signed_txn_optin)
        print("Signed transaction for asset transfer with txID: {}".format(txid_optin))
        confirmed_txn_optin = wait_for_confirmation(algod_client, txid_optin, 4)
        print("TXID: ", txid_optin)
        print(
            "Result for asset transfer confirmed in round: {}".format(
                confirmed_txn_optin["confirmed-round"]
            )
        )
    except Exception as err:
        print(err)

    print_asset_holding(algod_client, account3, asset_id)

# 4. TRANSFER ASSET
txn_transfer = AssetTransferTxn(
    sender=account1, sp=params, receiver=account3, amt=10, index=asset_id
)

# Sign transaction
signed_txn_transfer = txn_transfer.sign(private_key1)

# Execute transaction
try:
    txid_transfer = algod_client.send_transaction(signed_txn_transfer)
    print("Signed transaction for asset transfer with txID: {}".format(txid_transfer))
    confirmed_txn_transfer = wait_for_confirmation(algod_client, txid_transfer, 4)
    print("TXID for asset transfer: ", txid_transfer)
    print(
        "Result for asset transfer confirmed in round: {}".format(
            confirmed_txn_transfer["confirmed-round"]
        )
    )
except Exception as err:
    print(err)

print_asset_holding(algod_client, account3, asset_id)

# 5. FREEZE ASSET
txn_freeze = AssetFreezeTxn(
    sender=account2, sp=params, index=asset_id, target=account3, new_freeze_state=True
)

# Sign transaction
signed_txn_freeze = txn_freeze.sign(private_key2)

# Execute transaction
try:
    txid_freeze = algod_client.send_transaction(signed_txn_freeze)
    print("Signed transaction for asset freeze with txID: {}".format(txid_freeze))
    confirmed_txn_freeze = wait_for_confirmation(algod_client, txid_freeze, 4)
    print("TXID for asset freeze: ", txid_freeze)
    print(
        "Result for asset freeze confirmed in round: {}".format(
            confirmed_txn_freeze["confirmed-round"]
        )
    )
except Exception as err:
    print(err)

print_asset_holding(algod_client, account3, asset_id)

# 6. REVOKE ASSET
txn_revoke = AssetTransferTxn(
    sender=account2,
    sp=params,
    receiver=account1,
    amt=10,
    index=asset_id,
    revocation_target=account3,
)

# Sign transaction
signed_txn_revoke = txn_revoke.sign(private_key2)

# Execute transaction
try:
    txid_revoke = algod_client.send_transaction(signed_txn_revoke)
    print("Signed transaction for asset revocation with txID: {}".format(txid_revoke))
    confirmed_txn_revoke = wait_for_confirmation(algod_client, txid_revoke, 4)
    print("TXID for asset revocation: ", txid_revoke)
    print(
        "Result for asset revocation confirmed in round: {}".format(
            confirmed_txn_revoke["confirmed-round"]
        )
    )
except Exception as err:
    print(err)


# 7. DESTROY ASSET
txn_destroy = AssetConfigTxn(
    sender=account1, sp=params, index=asset_id, strict_empty_address_check=False
)

# Sign transaction
signed_txn_destroy = txn_destroy.sign(private_key1)

# Execute transaction
try:
    txid_destroy = algod_client.send_transaction(signed_txn_destroy)
    print("Signed transaction for asset destruction with txID: {}".format(txid_destroy))
    confirmed_txn_destroy = wait_for_confirmation(algod_client, txid_destroy, 4)
    print("TXID for asset destruction: ", txid_destroy)
    print(
        "Result for asset destruction confirmed in round: {}".format(
            confirmed_txn_destroy["confirmed-round"]
        )
    )
except Exception as err:
    print(err)
# Asset was deleted.
try:
    print("Account 3 must do a transaction for an amount of 0, ")
    print(
        "with a close_assets_to to the creator account, to clear it from its accountholdings"
    )
    print(
        "For Account 1, nothing should print after this as the asset is destroyed on the creator account"
    )
    print_asset_holding(algod_client, account1, asset_id)
    print_created_asset(algod_client, account1, asset_id)
    # asset_info = algod_client.asset_info(asset_id)
except Exception as e:
    print(e)
