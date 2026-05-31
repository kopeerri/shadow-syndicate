"""
Shadow Syndicate — $SHADE Deposit Module
Tracks $SHADE native token deposits via Blockfrost.
$SHADE Policy ID: fd4706d9fc0f5783813039dd3c27de0c648971e151ae8abfaf9f46b55348414445
"""
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BLOCKFROST_API_KEY = os.getenv("BLOCKFROST_API_KEY", "")
CASINO_WALLET = os.getenv("CASINO_WALLET_ADDRESS", "")
SHADE_POLICY_ID = "fd4706d9fc0f5783813039dd3c27de0c648971e151ae8abfaf9f46b55348414445"
# The full 66-char value is policy_id (56) + asset_name_hex (10 = "SHADE").
# Split for pycardano which needs just the 56-char policy hash.
SHADE_POLICY_HASH_HEX = SHADE_POLICY_ID[:56]
SHADE_ASSET_NAME_HEX = SHADE_POLICY_ID[56:] or "5348414445"  # "SHADE"

# $SHADE asset unit = policy_id + hex-encoded asset name
# Standard CIP-68 or basic token: just the policy ID. If there's a name, it's policy_id + hex(name)
SHADE_ASSET_UNIT = SHADE_POLICY_ID  # Full unit = policy_id(56) + asset_name(10) = 66 chars

NETWORK = "mainnet" if BLOCKFROST_API_KEY.startswith("mainnet") else "preprod"
BLOCKFROST_BASE = f"https://cardano-{NETWORK}.blockfrost.io/api/v0"


def normalize_address(addr: str) -> str:
    """Convert any Cardano address format to bech32 for consistent comparison.
    Blockfrost returns bech32 (addr1...), CIP-30 wallets may return hex."""
    import re
    if not addr:
        return addr
    # Already bech32
    if addr.startswith("addr1") or addr.startswith("addr_test1"):
        return addr
    # Hex address — convert to bech32 via pycardano
    if re.match(r'^[0-9a-fA-F]+$', addr) and len(addr) % 2 == 0:
        try:
            from pycardano import Address
            return str(Address.from_primitive(bytes.fromhex(addr)))
        except Exception:
            pass
    return addr


@dataclass
class DepositRecord:
    tx_hash: str
    sender_address: str
    shade_amount: int
    confirmed: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_deposits: dict[str, list[DepositRecord]] = {}  # sender_address -> [records]
_seen_tx_hashes: set[str] = set()  # global dedup across all users

# Persistent state file to survive server restarts
_STATE_FILE = Path(__file__).parent / "chain_state.json"


def _load_state():
    """Load persisted state from disk."""
    global _seen_tx_hashes, _deposits
    try:
        if _STATE_FILE.exists():
            data = json.loads(_STATE_FILE.read_text())
            _seen_tx_hashes = set(data.get("seen_tx_hashes", []))
            # Rebuild deposit records from persisted data
            for entry in data.get("deposits", []):
                addr = entry["sender_address"]
                record = DepositRecord(
                    tx_hash=entry["tx_hash"],
                    sender_address=addr,
                    shade_amount=entry["shade_amount"],
                    confirmed=True,
                    timestamp=entry.get("timestamp", datetime.now(timezone.utc).isoformat()),
                )
                if addr not in _deposits:
                    _deposits[addr] = []
                _deposits[addr].append(record)
    except Exception:
        pass


def _save_state():
    """Persist full state to disk."""
    try:
        all_deposits = []
        for addr, records in _deposits.items():
            for r in records:
                all_deposits.append({
                    "tx_hash": r.tx_hash,
                    "sender_address": r.sender_address,
                    "shade_amount": r.shade_amount,
                    "timestamp": r.timestamp,
                })
        _STATE_FILE.write_text(json.dumps({
            "seen_tx_hashes": list(_seen_tx_hashes),
            "deposits": all_deposits,
        }))
    except Exception:
        pass


import json
_load_state()


def get_blockfrost_headers() -> dict:
    return {"project_id": BLOCKFROST_API_KEY} if BLOCKFROST_API_KEY else {}


def is_configured() -> bool:
    return bool(BLOCKFROST_API_KEY and CASINO_WALLET)


async def fetch_json(url: str) -> dict | list:
    """Thin wrapper with error handling."""
    if not BLOCKFROST_API_KEY:
        return {} if "txs/" not in url else []
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=get_blockfrost_headers())
        if resp.status_code == 200:
            return resp.json()
        return [] if "utxos" in url or "transactions" in url else {}


async def fetch_address_utxos_asset(address: str, asset: str) -> list[dict]:
    """Fetch UTXOs at an address that contain a specific asset."""
    url = f"{BLOCKFROST_BASE}/addresses/{address}/utxos/{asset}"
    return await fetch_json(url)


async def fetch_tx_utxos(tx_hash: str) -> dict:
    """Get inputs + outputs for a transaction."""
    url = f"{BLOCKFROST_BASE}/txs/{tx_hash}/utxos"
    result = await fetch_json(url)
    return result if isinstance(result, dict) else {}


async def fetch_tx_metadata(tx_hash: str) -> dict:
    """Get transaction metadata (for confirmations, block time, etc.)."""
    url = f"{BLOCKFROST_BASE}/txs/{tx_hash}/metadata"
    result = await fetch_json(url)
    return result if isinstance(result, dict) else {}


async def check_shade_deposits() -> list[dict]:
    """
    Scan the casino wallet for incoming $SHADE UTXOs.
    For each, trace the transaction back to the sender's address.
    Credits the actual sender, not the caller.
    Returns list of NEW deposits discovered this scan.
    """
    if not is_configured():
        return []

    new_deposits = []

    # Get all UTXOs at casino wallet that contain $SHADE
    utxos = await fetch_address_utxos_asset(CASINO_WALLET, SHADE_ASSET_UNIT)

    for utxo in utxos:
        tx_hash = utxo.get("tx_hash", "")
        if not tx_hash or tx_hash in _seen_tx_hashes:
            continue

        # Extract $SHADE quantity from this UTXO's amounts
        shade_qty = 0
        for amt in utxo.get("amount", []):
            unit = amt.get("unit", "")
            if unit != "lovelace" and SHADE_POLICY_ID in unit:
                shade_qty += int(amt.get("quantity", 0))

        if shade_qty <= 0:
            continue

        # Trace back: which address SENT this $SHADE?
        # Look at transaction inputs — find the input that contained $SHADE
        sender = None
        tx_data = await fetch_tx_utxos(tx_hash)

        for inp in tx_data.get("inputs", []):
            inp_addr = inp.get("address", "")
            inp_amount = inp.get("amount", [])
            for amt in inp_amount:
                unit = amt.get("unit", "")
                if unit != "lovelace" and SHADE_POLICY_ID in unit:
                    sender = inp_addr
                    break
            if sender:
                break

        # Fallback: if we can't determine the sender from inputs,
        # use the first non-casino input address
        if not sender:
            for inp in tx_data.get("inputs", []):
                inp_addr = inp.get("address", "")
                if inp_addr and inp_addr != CASINO_WALLET:
                    sender = inp_addr
                    break

        if not sender:
            sender = "unknown"

        # Normalize to bech32 so comparisons with wallet addresses always match
        sender = normalize_address(sender)

        _seen_tx_hashes.add(tx_hash)
        _save_state()  # persist so deposit can't be double-credited after restart

        record = DepositRecord(
            tx_hash=tx_hash,
            sender_address=sender,
            shade_amount=shade_qty,
            confirmed=True,
        )

        if sender not in _deposits:
            _deposits[sender] = []
        _deposits[sender].append(record)

        new_deposits.append({
            "tx_hash": tx_hash,
            "sender": sender,
            "shade_amount": shade_qty,
            "shade_display": f"{shade_qty:,}",
            "timestamp": record.timestamp,
        })

    return new_deposits


def get_user_deposits(wallet_address: str) -> list[dict]:
    records = _deposits.get(wallet_address, [])
    return [
        {
            "tx_hash": r.tx_hash,
            "shade_amount": r.shade_amount,
            "shade_display": f"{r.shade_amount:,}",
            "confirmed": r.confirmed,
            "timestamp": r.timestamp,
        }
        for r in records
    ]


def get_shade_balance(wallet_address: str) -> int:
    return sum(r.shade_amount for r in _deposits.get(wallet_address, []))


def record_balance_delta(wallet_address: str, delta: int) -> int:
    """Record a balance change from game play (bet deduction or win payout).
    Positive delta = win/payout. Negative delta = bet deducted.
    Returns new balance."""
    addr = normalize_address(wallet_address)
    record = DepositRecord(
        tx_hash=f"game_{secrets.token_hex(8)}",
        sender_address=addr,
        shade_amount=delta,
        confirmed=True,
    )
    if addr not in _deposits:
        _deposits[addr] = []
    _deposits[addr].append(record)
    _seen_tx_hashes.add(record.tx_hash)
    _save_state()
    return get_shade_balance(addr)


def add_demo_deposit(wallet_address: str, shade_amount: int) -> DepositRecord:
    record = DepositRecord(
        tx_hash=f"demo_{secrets.token_hex(8)}",
        sender_address=wallet_address,
        shade_amount=shade_amount,
        confirmed=True,
    )
    if wallet_address not in _deposits:
        _deposits[wallet_address] = []
    _deposits[wallet_address].append(record)
    _seen_tx_hashes.add(record.tx_hash)
    return record


def get_casino_info() -> dict:
    return {
        "casino_wallet": CASINO_WALLET,
        "network": NETWORK,
        "shade_policy_id": SHADE_POLICY_ID,
        "configured": is_configured(),
    }


# ── WITHDRAWALS ──

@dataclass
class WithdrawalRecord:
    id: str
    wallet_address: str
    shade_amount: int
    status: str  # "pending", "sent", "confirmed"
    tx_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_withdrawals: dict[str, list[WithdrawalRecord]] = {}  # wallet_address -> records
_pending_withdrawals: dict[str, WithdrawalRecord] = {}  # id -> record


def request_withdrawal(wallet_address: str, shade_amount: int) -> dict:
    """Request a withdrawal. Deducts balance, creates pending record."""
    addr = normalize_address(wallet_address)
    balance = get_shade_balance(addr)
    if shade_amount <= 0:
        return {"error": "Amount must be positive"}
    if shade_amount > balance:
        return {"error": f"Insufficient balance. Have: {balance:,}, Requested: {shade_amount:,}"}

    # Deduct from balance
    record_balance_delta(addr, -shade_amount)

    # Create withdrawal record
    wid = f"wd_{secrets.token_hex(6)}"
    wr = WithdrawalRecord(
        id=wid,
        wallet_address=addr,
        shade_amount=shade_amount,
        status="pending",
    )
    _pending_withdrawals[wid] = wr
    if addr not in _withdrawals:
        _withdrawals[addr] = []
    _withdrawals[addr].append(wr)

    return {
        "id": wid,
        "wallet_address": addr,
        "shade_amount": shade_amount,
        "status": "pending",
        "new_balance": get_shade_balance(addr),
        "message": f"Withdrawal of {shade_amount:,} $SHADE requested. Send manually from casino wallet to {addr}.",
        "casino_wallet": CASINO_WALLET,
    }


def get_withdrawal_history(wallet_address: str) -> list[dict]:
    addr = normalize_address(wallet_address)
    records = _withdrawals.get(addr, [])
    return [
        {
            "id": r.id,
            "shade_amount": r.shade_amount,
            "status": r.status,
            "tx_hash": r.tx_hash,
            "timestamp": r.timestamp,
        }
        for r in records
    ]


def get_pending_withdrawals() -> list[dict]:
    return [
        {
            "id": r.id,
            "wallet_address": r.wallet_address,
            "shade_amount": r.shade_amount,
            "status": r.status,
            "timestamp": r.timestamp,
        }
        for r in _pending_withdrawals.values()
    ]


def mark_withdrawal_sent(wid: str, tx_hash: str = "") -> dict:
    """Mark a pending withdrawal as sent (operator confirms they sent the funds)."""
    wr = _pending_withdrawals.get(wid)
    if not wr:
        return {"error": "Withdrawal not found"}
    wr.status = "sent"
    wr.tx_hash = tx_hash
    del _pending_withdrawals[wid]
    return {"id": wid, "status": "sent", "tx_hash": tx_hash}
