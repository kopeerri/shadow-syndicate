"""
Shadow Syndicate — Cardano Transaction Builder
Builds unsigned $SHADE deposit transactions for CIP-30 wallet signing.
"""
from pycardano import (
    TransactionBuilder, TransactionOutput, Value, Asset, AssetName,
    Network, Address, UTxO, MultiAsset, Transaction, TransactionWitnessSet,
    TransactionInput, TransactionId,
)
from pycardano.hash import ScriptHash
from pycardano.backend.blockfrost import BlockFrostChainContext
from deposit import (
    SHADE_POLICY_ID, SHADE_POLICY_HASH_HEX, SHADE_ASSET_NAME_HEX,
    CASINO_WALLET, NETWORK, BLOCKFROST_API_KEY,
)
import re, cbor2

SHADE_POLICY_HASH = ScriptHash(bytes.fromhex(SHADE_POLICY_HASH_HEX))
SHADE_ASSET_NAME = AssetName(bytes.fromhex(SHADE_ASSET_NAME_HEX))
_chain_context = None

def get_chain_context():
    global _chain_context
    if _chain_context is None:
        n = Network.MAINNET if NETWORK == "mainnet" else Network.TESTNET
        _chain_context = BlockFrostChainContext(project_id=BLOCKFROST_API_KEY, network=n)
    return _chain_context

def decode_address(s):
    if re.match(r'^[0-9a-fA-F]+$', s) and len(s) % 2 == 0:
        return Address.from_primitive(bytes.fromhex(s))
    return Address.decode(s)

def _convert_nested_assets(nested):
    ma = MultiAsset()
    for policy_bytes, assets in nested.items():
        ph = ScriptHash(policy_bytes)
        if ph not in ma: ma[ph] = Asset()
        for name_bytes, qty in assets.items():
            ma[ph][AssetName(name_bytes)] = qty
    return ma

def _convert_flat_assets(flat):
    ma = MultiAsset()
    for key_bytes, qty in flat.items():
        key_hex = key_bytes.hex() if isinstance(key_bytes, bytes) else key_bytes
        ph = ScriptHash(bytes.fromhex(key_hex[:56]))
        an = AssetName(bytes.fromhex(key_hex[56:]))
        if ph not in ma: ma[ph] = Asset()
        ma[ph][an] = qty
    return ma

def parse_cip30_utxo(cbor_hex):
    data = cbor2.loads(bytes.fromhex(cbor_hex))
    inp_data, out_data = data
    tx_input = TransactionInput(TransactionId(inp_data[0]), inp_data[1])
    addr_bytes = out_data[0]
    amount_data = out_data[1]
    coin = 0; multi_asset = None

    if isinstance(amount_data, list):
        if len(amount_data) > 0 and isinstance(amount_data[0], dict):
            for item in amount_data:
                unit = item.get("unit", "lovelace"); qty = int(item.get("quantity", "0"))
                if unit == "lovelace": coin = qty
                else:
                    ph = ScriptHash(bytes.fromhex(unit[:56]))
                    an = AssetName(bytes.fromhex(unit[56:]))
                    if multi_asset is None: multi_asset = MultiAsset()
                    if ph not in multi_asset: multi_asset[ph] = Asset()
                    multi_asset[ph][an] = qty
        elif isinstance(amount_data[0], int):
            coin = amount_data[0]
            if len(amount_data) > 1 and isinstance(amount_data[1], dict):
                raw = amount_data[1]
                first_val = next(iter(raw.values())) if raw else None
                multi_asset = _convert_nested_assets(raw) if isinstance(first_val, dict) else _convert_flat_assets(raw)
    elif isinstance(amount_data, int): coin = amount_data

    addr = Address.from_primitive(addr_bytes)
    return UTxO(tx_input, TransactionOutput(addr, Value(coin, multi_asset) if multi_asset else Value(coin)))

def build_deposit_tx(sender_utxos_hex, sender_change_address, shade_deposit_amount):
    casino_addr = decode_address(CASINO_WALLET)
    change_addr = decode_address(sender_change_address)
    ctx = get_chain_context()
    builder = TransactionBuilder(context=ctx)
    total_lovelace = 0; total_shade = 0

    for uh in sender_utxos_hex:
        utxo = parse_cip30_utxo(uh)
        builder.add_input(utxo)
        total_lovelace += utxo.output.amount.coin
        ma = utxo.output.amount.multi_asset
        if ma:
            for ph, asset in ma.items():
                if str(ph) == SHADE_POLICY_HASH.payload.hex():
                    for an, qty in asset.items(): total_shade += qty

    if total_shade < shade_deposit_amount:
        raise ValueError(f"Insufficient $SHADE. Have: {total_shade:,}, Need: {shade_deposit_amount:,}")

    min_ada = 1_500_000
    casino_ma = MultiAsset(); casino_assets = Asset()
    casino_assets[SHADE_ASSET_NAME] = shade_deposit_amount
    casino_ma[SHADE_POLICY_HASH] = casino_assets
    builder.add_output(TransactionOutput(casino_addr, Value(min_ada, casino_ma)))

    # Fee = a*tx_size + b. For ~373-byte tx: 44*373 + 155381 = 171,793
    # Actual measured: 171,881
    fee = 172_050
    remaining_ada = total_lovelace - min_ada - fee
    remaining_shade = total_shade - shade_deposit_amount

    if remaining_shade > 0:
        cm = MultiAsset(); ca = Asset()
        ca[SHADE_ASSET_NAME] = remaining_shade; cm[SHADE_POLICY_HASH] = ca
        builder.add_output(TransactionOutput(change_addr, Value(remaining_ada, cm)))
    else:
        builder.add_output(TransactionOutput(change_addr, Value(remaining_ada)))

    tx_body = builder.build()
    tx = Transaction(tx_body, TransactionWitnessSet())
    return {"tx_cbor": tx.to_cbor_hex(), "tx_body_cbor": tx_body.to_cbor_hex()}
