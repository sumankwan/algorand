import base64

from algosdk.future import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod
from pyteal import compileTeal, Mode
from contract import approval_program, clear_state_program
from algosdk.future.transaction import (
    AssetConfigTxn,
    AssetTransferTxn
    # wait_for_confirmation
)
import json

# user declared account mnemonics
creator_mnemonic = "drive parade alarm permit loud option roof absorb health own basic umbrella scrub music mother capital bounce web art wealth penalty meat own above escape"
user_mnemonic = "misery chaos virus grant again repeat ladder oppose pig baby assist sample goat cable fame indicate piano draft side have cattle cart silent absorb sense"

# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "https://testnet-api.algonode.cloud"


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
            return scrutinized_asset["index"]


def print_asset_holding(algodclient, account, assetid):
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["assets"]:
        scrutinized_asset = account_info["assets"][idx]
        idx = idx + 1
        if scrutinized_asset["asset-id"] == assetid:
            print("Asset ID: {}".format(scrutinized_asset["asset-id"]))
            print(json.dumps(scrutinized_asset, indent=4))
            amount = json.dumps(scrutinized_asset["amount"], indent=4)
            return scrutinized_asset["asset-id"], amount


# helper function to compile program source
def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response["result"])


# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


# helper function that waits for a given txid to be confirmed by the network
def wait_for_confirmation(client, txid):
    last_round = client.status().get("last-round")
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print(
        "Transaction {} confirmed in round {}.".format(
            txid, txinfo.get("confirmed-round")
        )
    )
    return txinfo


def wait_for_round(client, round):
    last_round = client.status().get("last-round")
    print(f"Waiting for round {round}")
    while last_round < round:
        last_round += 1
        client.status_after_block(last_round)
        print(f"Round {last_round}")


def create_asset(client, creator_private_key, user_private_key):
    account1 = "7XBHR7UM6G5VM6JVBQUIUTQY2XREF4PNJX75P4VQGIPLRT3NHS35KPROSE"
    passphrase1 = "drive parade alarm permit loud option roof absorb health own basic umbrella scrub music mother capital bounce web art wealth penalty meat own above escape"
    private_key1 = get_private_key_from_mnemonic(passphrase1)
    account2 = "BDJJBU4T5XQ2OEDQB7UVFSI2XNEY3IFTAIFHWZVZB2XAGYVKBI6ZFRNPDA"
    passphrase2 = "misery chaos virus grant again repeat ladder oppose pig baby assist sample goat cable fame indicate piano draft side have cattle cart silent absorb sense"
    private_key2 = get_private_key_from_mnemonic(passphrase2)
    params = client.suggested_params()

    txn_create = AssetConfigTxn(
        sender=account1,
        sp=params,
        total=100000,
        default_frozen=False,
        unit_name="ENB",
        manager=account1,
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
        txid_create = client.send_transaction(signed_txn_create)
        print("Signed transaction for asset creation with txID: {}".format(txid_create))
        confirmed_txn_create = wait_for_confirmation(client, txid_create)
        print("TXID for asset creation", txid_create)
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
    
    try:
        ptx = client.pending_transaction_info(txid_create)
        asset_id = ptx["asset-index"]
        asset_id1 = print_created_asset(client, account1, asset_id)
        asset_id2, amount = print_asset_holding(client, account1, asset_id)
        # return asset_id1, asset_id2, amount
    except Exception as err:
        print(err)

    # account 2 opting-in
    txn_optin = AssetTransferTxn(
        sender=account2, sp=params, receiver=account2, amt=0, index=asset_id1
    )
    signed_txn_optin = txn_optin.sign(private_key2)

    # Execute transaction
    try:
        txid_optin = client.send_transaction(signed_txn_optin)
        print("Signed transaction for asset optin for account 2 with txID: {}".format(txid_optin))
        confirmed_txn_optin = wait_for_confirmation(client, txid_optin)
        print("TXID: ", txid_optin)
        print(
            "Result for asset optin for account 2 confirmed in round: {}".format(
                confirmed_txn_optin["confirmed-round"]
            )
        )
    except Exception as err:
        print(err)

    print_asset_holding(client, account2, asset_id1)

    # transfer asset
    txn_transfer = AssetTransferTxn(
        sender=account1, sp=params, receiver=account2, amt=1000, index=asset_id1
    )

    # Sign transaction
    signed_txn_transfer = txn_transfer.sign(private_key1)

    # Execute transaction
    try:
        txid_transfer = client.send_transaction(signed_txn_transfer)
        print("Signed transaction for asset transfer with txID: {}".format(txid_transfer))
        confirmed_txn_transfer = wait_for_confirmation(client, txid_transfer)
        print("TXID for asset transfer: ", txid_transfer)
        print(
            "Result for asset transfer confirmed in round: {}".format(
                confirmed_txn_transfer["confirmed-round"]
            )
        )
    except Exception as err:
        print(err)
    
    print("this is asset holding of account 2")
    print_asset_holding(client, account2, asset_id1)
    return asset_id1, asset_id2, amount, account2


# create new application
def create_app(
    client,
    private_key,
    approval_program,
    clear_program,
    global_schema,
    local_schema,
    app_args,
):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
        app_args,
    )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response["application-index"]
    print("Created new app-id:", app_id)

    return app_id


# opt-in to application
def opt_in_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()

    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationOptInTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptIn to app-id:", transaction_response["txn"]["txn"]["apid"])


# call application
def call_app(client, private_key, index, app_args, asset_id):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args, [], [], [asset_id])

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)


def format_state(state):
    formatted = {}
    for item in state:
        key = item["key"]
        value = item["value"]
        formatted_key = base64.b64decode(key).decode("utf-8")
        if value["type"] == 1:
            # byte string
            if formatted_key == "voted":
                formatted_value = base64.b64decode(value["bytes"]).decode("utf-8")
            else:
                formatted_value = value["bytes"]
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value["uint"]
    return formatted


# read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)
    for local_state in results["apps-local-state"]:
        if local_state["id"] == app_id:
            if "key-value" not in local_state:
                return {}
            return format_state(local_state["key-value"])
    return {}


# read app global state
def read_global_state(client, addr, app_id):
    results = client.account_info(addr)
    apps_created = results["created-apps"]
    for app in apps_created:
        if app["id"] == app_id:
            return format_state(app["params"]["global-state"])
    return {}


# delete application
def delete_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationDeleteTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Deleted app-id:", transaction_response["txn"]["txn"]["apid"])


# close out from application
def close_out_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationCloseOutTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Closed out from app-id: ", transaction_response["txn"]["txn"]["apid"])


# clear application
def clear_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationClearStateTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Cleared app-id:", transaction_response["txn"]["txn"]["apid"])


# convert 64 bit integer i to byte string
def intToBytes(i):
    return i.to_bytes(8, "big")


def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient("", algod_address)

    # define private keys
    creator_private_key = get_private_key_from_mnemonic(creator_mnemonic)
    user_private_key = get_private_key_from_mnemonic(user_mnemonic)

    # create asset
    asset_id1 = ''
    try:
        asset_id1, asset_id2, amount, account2 = create_asset(algod_client, creator_private_key, user_private_key)
        print("this is it", asset_id1, asset_id2, amount)
    except Exception as err:
        print(err)

    # declare application state storage (immutable)
    local_ints = 8
    local_bytes = 8
    global_ints = (
        32  # 4 for setup + 20 for choices. Use a larger number for more choices.
    )
    global_bytes = 8
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # get PyTeal approval program
    approval_program_ast = approval_program()

    # compile program to TEAL assembly
    approval_program_teal = compileTeal(
        approval_program_ast, mode=Mode.Application, version=6
    )
    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program_teal)

    # get PyTeal clear state program
    clear_state_program_ast = clear_state_program()
    # compile program to TEAL assembly
    clear_state_program_teal = compileTeal(
        clear_state_program_ast, mode=Mode.Application, version=6
    )
    # compile program to binary
    clear_state_program_compiled = compile_program(
        algod_client, clear_state_program_teal
    )

    # configure registration and voting period
    status = algod_client.status()
    regBegin = status["last-round"] + 10
    regEnd = regBegin + 10
    voteBegin = regEnd + 1
    voteEnd = voteBegin + 10

    print(f"Registration rounds: {regBegin} to {regEnd}")
    print(f"Vote rounds: {voteBegin} to {voteEnd}")

    # create list of bytes for app args
    app_args = [
        intToBytes(regBegin),
        intToBytes(regEnd),
        intToBytes(voteBegin),
        intToBytes(voteEnd),
        intToBytes(0),
        intToBytes(0)
    ]
    
    # create new application
    app_id = create_app(
        algod_client,
        creator_private_key,
        approval_program_compiled,
        clear_state_program_compiled,
        global_schema,
        local_schema,
        app_args,
    )
    
    # read global state of application
    print(
        "Global state:",
        read_global_state(
            algod_client, account.address_from_private_key(creator_private_key), app_id
        ),
    )

    # wait for registration period to start
    wait_for_round(algod_client, regBegin)

    # opt-in to application
    opt_in_app(algod_client, user_private_key, app_id)

    wait_for_round(algod_client, voteBegin)

    # call application without arguments
    stake = int(1000 / 100000)
    vote = "something"
    vote = "abstain"
    vote = "no"
    vote = "yes"
    # print("this is asset-id", asset_id1)
    app_args = [
        b"vote", # voting round identifier
        b"choiceA", # choice
        bytes(vote, 'utf-8'), # type of vote
        intToBytes(stake), # stake
        intToBytes(asset_id1), # asset id
        bytes("BDJJBU4T5XQ2OEDQB7UVFSI2XNEY3IFTAIFHWZVZB2XAGYVKBI6ZFRNPDA", "utf-8") # account 2
    ]

    call_app(algod_client, user_private_key, app_id, app_args, asset_id1)

    # read local state of application from user account
    print(
        "Local state:",
        read_local_state(
            algod_client, account.address_from_private_key(user_private_key), app_id
        ),
    )

    # wait for registration period to start
    wait_for_round(algod_client, voteEnd)

    # read global state of application
    global_state = read_global_state(
        algod_client, account.address_from_private_key(creator_private_key), app_id
    )
    print("Global state:", global_state)

    max_votes = 0
    max_votes_choice = None
    for key, value in global_state.items():
        print("key value", key, value)
        if key not in (
            "RegBegin",
            "RegEnd",
            "VoteBegin",
            "VoteEnd",
            "Creator"
        ) and isinstance(value, int):
            print("this is it too", key, value, max_votes)
            if value > max_votes:
                max_votes = value
                max_votes_choice = key

    print("The winner is:", max_votes_choice)

    # delete application
    delete_app(algod_client, creator_private_key, app_id)

    # clear application from user account
    clear_app(algod_client, user_private_key, app_id)
    

if __name__ == "__main__":
    main()