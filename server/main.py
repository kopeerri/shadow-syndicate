#!/usr/bin/env python3
"""
Shadow Syndicate — Backend Game Server
$SHADE-native casino. Provably fair RNG: Blackjack, Dice, Mines.
Cardano wallet integration via Blockfrost. Real $SHADE deposits.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import hashlib, hmac, secrets, json, os
from datetime import datetime
from pathlib import Path

from deposit import (
    check_shade_deposits,
    get_user_deposits,
    get_shade_balance,
    add_demo_deposit,
    get_casino_info,
    is_configured,
    normalize_address,
    record_balance_delta,
    request_withdrawal,
    get_withdrawal_history,
    get_pending_withdrawals,
    mark_withdrawal_sent,
    SHADE_POLICY_ID,
    BLOCKFROST_API_KEY,
    BLOCKFROST_BASE,
)

app = FastAPI(title="Shadow Syndicate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prevent browser caching — user always gets fresh JS/CSS/HTML
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# ── PROVABLY FAIR RNG ──

class FairRNG:
    def __init__(self):
        self.server_seed = self._load_or_generate_seed()
        self.server_seed_hash = hashlib.sha256(self.server_seed.encode()).hexdigest()
        self.nonce = 0

    def _load_or_generate_seed(self):
        seed_file = Path(__file__).parent / "server_seed.txt"
        if seed_file.exists():
            return seed_file.read_text().strip()
        seed = secrets.token_hex(32)
        seed_file.write_text(seed)
        return seed

    def get_seed_hash(self):
        return self.server_seed_hash

    def roll(self, client_seed: str) -> float:
        self.nonce += 1
        message = f"{self.server_seed}:{client_seed}:{self.nonce}"
        h = hmac.new(self.server_seed.encode(), message.encode(), hashlib.sha256).hexdigest()
        return int(h[:8], 16) / 0xFFFFFFFF

    def roll_int(self, client_seed: str, min_val: int, max_val: int) -> int:
        return min_val + int(self.roll(client_seed) * (max_val - min_val + 1))

    def shuffle(self, client_seed: str, items: list) -> list:
        result = items[:]
        for i in range(len(result) - 1, 0, -1):
            j = self.roll_int(client_seed, 0, i)
            result[i], result[j] = result[j], result[i]
        return result

    def get_proof(self, client_seed: str) -> dict:
        return {
            "server_seed_hash": self.server_seed_hash,
            "client_seed": client_seed,
            "nonce": self.nonce,
        }

rng = FairRNG()

# ── SESSION ──

class PlayerSession:
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address
        self.client_seed = secrets.token_hex(16)
        self.active_games = {}
        self.created_at = datetime.utcnow()

    @property
    def balance(self) -> int:
        """$SHADE balance (in base units: 1 SHADE = 1_000_000)."""
        shade = get_shade_balance(self.wallet_address)
        for g in self.active_games.values():
            if "bet" in g:
                shade -= g["bet"]
        return max(0, shade)

    def to_dict(self):
        return {
            "wallet_address": self.wallet_address,
            "balance": self.balance,
            "balance_units": self.balance,
            "balance_shade": f"{self.balance:,}",
            "shade_policy_id": SHADE_POLICY_ID,
            "client_seed": self.client_seed,
            "active_games": len(self.active_games),
        }

sessions: dict[str, PlayerSession] = {}
operator_tokens: set[str] = set()

def require_operator(authorization: str = Header(default=""), x_operator_token: str = Header(default="")):
    """Require a short-lived operator session token for sensitive operator APIs."""
    token = x_operator_token.strip()
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token or token not in operator_tokens:
        raise HTTPException(401, "Operator authentication required")
    return True

def get_session(wallet_address: str) -> PlayerSession:
    addr = normalize_address(wallet_address)
    if addr not in sessions:
        sessions[addr] = PlayerSession(addr)
    return sessions[addr]

# ── MODELS ──

class BetRequest(BaseModel):
    wallet_address: str
    bet_amount: int  # $SHADE base units (1 SHADE = 1_000_000)

class BlackjackAction(BaseModel):
    wallet_address: str
    game_id: str
    action: str  # hit, stand, double

class DiceRequest(BaseModel):
    wallet_address: str
    bet_amount: int
    target: int  # 2-98

class MinesRequest(BaseModel):
    wallet_address: str
    bet_amount: int
    mine_count: int  # 1-24

class MinesReveal(BaseModel):
    wallet_address: str
    game_id: str
    tile_index: int

class CashoutRequest(BaseModel):
    wallet_address: str
    game_id: str

# ── GAME ENGINES ──

from games.blackjack import BlackjackEngine
from games.dice import DiceEngine
from games.mines import MinesEngine

# ═══════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════

@app.get("/")
def root():
    casino = get_casino_info()
    return {
        "name": "Shadow Syndicate API",
        "status": "operational",
        "network": casino["network"],
        "token": "SHADE",
        "policy_id": SHADE_POLICY_ID,
    }

# ── DEPOSIT ──

@app.get("/deposit/info")
def deposit_info():
    return get_casino_info()

class BalanceSyncRequest(BaseModel):
    wallet_address: str
    delta: int  # positive = win, negative = bet/loss

@app.post("/balance/sync")
def balance_sync(req: BalanceSyncRequest):
    """Sync game balance changes with server. Called after bets and wins."""
    new_balance = record_balance_delta(req.wallet_address, req.delta)
    return {
        "wallet_address": req.wallet_address,
        "delta": req.delta,
        "new_balance": new_balance,
        "new_balance_shade": f"{new_balance:,}",
    }

# ── WITHDRAWALS ──

class WithdrawRequest(BaseModel):
    wallet_address: str
    shade_amount: int

class MarkSentRequest(BaseModel):
    withdrawal_id: str
    tx_hash: str = ""

class OperatorLoginRequest(BaseModel):
    password: str

@app.post("/operator/login")
def operator_login(req: OperatorLoginRequest):
    password = os.getenv("OPERATOR_PASSWORD", "")
    if not password:
        raise HTTPException(503, "Operator auth is not configured")
    if not hmac.compare_digest(req.password, password):
        raise HTTPException(401, "Invalid password")
    token = secrets.token_urlsafe(32)
    operator_tokens.add(token)
    return {"token": token}

@app.post("/withdraw/request")
def withdraw_request(req: WithdrawRequest):
    """Request a withdrawal. Deducts balance, creates pending record for operator to send manually."""
    result = request_withdrawal(req.wallet_address, req.shade_amount)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@app.get("/withdraw/history/{wallet_address}")
def withdraw_history(wallet_address: str):
    return {
        "wallet_address": wallet_address,
        "withdrawals": get_withdrawal_history(wallet_address),
    }

@app.get("/withdraw/pending")
def withdraw_pending(_: bool = Depends(require_operator)):
    return {"pending": get_pending_withdrawals()}

@app.post("/withdraw/mark-sent")
def withdraw_mark_sent(req: MarkSentRequest, _: bool = Depends(require_operator)):
    result = mark_withdrawal_sent(req.withdrawal_id, req.tx_hash)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@app.get("/deposit/check/{wallet_address}")
async def deposit_check(wallet_address: str):
    """Check blockchain for new $SHADE deposits. Credits actual senders."""
    addr = normalize_address(wallet_address)
    new = await check_shade_deposits()
    # Filter to deposits for THIS wallet (both now normalized to bech32)
    my_deposits = [d for d in new if d["sender"] == addr]
    balance = get_shade_balance(addr)
    return {
        "wallet_address": addr,
        "new_deposits": my_deposits,
        "balance_units": balance,
        "balance_shade": f"{balance:,}",
    }

@app.get("/deposit/history/{wallet_address}")
def deposit_history(wallet_address: str):
    addr = normalize_address(wallet_address)
    deposits = get_user_deposits(addr)
    total = sum(d["shade_amount"] for d in deposits)
    return {
        "wallet_address": addr,
        "deposits": deposits,
        "total_shade_units": total,
        "total_shade": f"{total:,}",
    }

# ── DEPOSIT VERIFY (manual send flow) ──

@app.get("/deposit/verify/{wallet_address:path}")
async def deposit_verify(wallet_address: str):
    """Verify a manual $SHADE deposit. Scans blockchain, credits sender. Call after user sends $SHADE to casino address from their wallet."""
    addr = normalize_address(wallet_address)
    if not is_configured():
        return {"wallet_address": addr, "new_deposits": [], "balance_units": 0, "balance_shade": "0", "configured": False, "message": "Blockfrost not configured. Set BLOCKFROST_API_KEY and CASINO_WALLET_ADDRESS in .env"}
    new = await check_shade_deposits()
    my_deposits = [d for d in new if d["sender"] == addr]
    balance = get_shade_balance(addr)
    return {
        "wallet_address": addr,
        "new_deposits": my_deposits,
        "total_credited": sum(d["shade_amount"] for d in my_deposits),
        "balance_units": balance,
        "balance_shade": f"{balance:,}",
        "configured": True,
    }

# ── DEBUG ──

@app.delete("/deposit/reset-seen")
def deposit_reset_seen():
    """Admin: clear seen tx hashes so next scan re-processes all UTXOs."""
    from deposit import _seen_tx_hashes, _deposits, _STATE_FILE
    count_before = len(_seen_tx_hashes)
    _seen_tx_hashes.clear()
    _deposits.clear()
    # Also clear disk persistence
    try:
        _STATE_FILE.write_text('{"seen_tx_hashes": []}')
    except Exception:
        pass
    return {"cleared_seen_hashes": count_before, "cleared_deposits": True}

# ── WALLET ──

@app.get("/wallet/balance/{wallet_address:path}")
async def wallet_balance(wallet_address: str):
    """Query a wallet's $SHADE balance via Blockfrost. Handles hex and bech32 addresses."""
    from deposit import fetch_address_utxos_asset, SHADE_ASSET_UNIT
    import re

    if not is_configured():
        return {"wallet_address": wallet_address, "shade_balance": 0, "shade_display": "0.00"}

    # Normalize: if hex, convert to bech32 for Blockfrost
    query_addr = normalize_address(wallet_address)

    utxos = await fetch_address_utxos_asset(query_addr, SHADE_ASSET_UNIT)
    total = 0
    for u in utxos:
        for amt in u.get("amount", []):
            if amt.get("unit", "lovelace") != "lovelace":
                total += int(amt.get("quantity", 0))
    return {"wallet_address": wallet_address, "shade_balance": total, "shade_display": f"{total:,}"}

# ── SESSION ──

@app.get("/session/{wallet_address}")
def session_get(wallet_address: str):
    return get_session(wallet_address).to_dict()

# ── FAIRNESS ──

@app.get("/fairness/seed-hash")
def fairness_seed():
    return {"server_seed_hash": rng.get_seed_hash()}

# ── BLACKJACK ──

blackjack_rooms: dict[str, BlackjackEngine] = {}

@app.post("/blackjack/start")
def blackjack_start(req: BetRequest):
    session = get_session(req.wallet_address)
    if session.balance < req.bet_amount:
        needed = req.bet_amount 
        have = session.balance 
        raise HTTPException(400, f"Insufficient $SHADE. Have: {have:,.0f}, Need: {needed:,.0f}")

    game = BlackjackEngine(rng, session.client_seed, req.bet_amount)
    game.deal()
    game_id = secrets.token_hex(8)
    blackjack_rooms[game_id] = game
    session.active_games[game_id] = {"type": "blackjack", "bet": req.bet_amount}

    return {
        "game_id": game_id,
        "player_hand": game.player_hand,
        "dealer_hand": [game.dealer_hand[0], "???"],
        "player_score": game.player_score,
        "bet_amount": req.bet_amount,
        "bet_display": f"{req.bet_amount:,} SHADE",
        "can_double": game.can_double,
    }

@app.post("/blackjack/action")
def blackjack_action(req: BlackjackAction):
    game = blackjack_rooms.get(req.game_id)
    if not game:
        raise HTTPException(404, "Game not found")

    session = get_session(req.wallet_address)

    if req.action == "hit":
        game.hit()
    elif req.action == "stand":
        game.stand()
    elif req.action == "double":
        if session.balance < game.bet_amount * 2:
            raise HTTPException(400, "Insufficient balance for double")
        game.double_down()
    else:
        raise HTTPException(400, f"Unknown action: {req.action}")

    result = game.get_state()
    result["game_id"] = req.game_id

    if result.get("game_over"):
        payout = result.get("payout", 0)
        if payout > 0:
            add_demo_deposit(req.wallet_address, payout)
        del blackjack_rooms[req.game_id]
        session.active_games.pop(req.game_id, None)
        result["new_balance_units"] = session.balance
        result["new_balance_shade"] = f"{session.balance:,}"

    result["proof"] = rng.get_proof(session.client_seed)
    return result

# ── DICE ──

@app.post("/dice/roll")
def dice_roll(req: DiceRequest):
    session = get_session(req.wallet_address)
    if session.balance < req.bet_amount:
        raise HTTPException(400, "Insufficient $SHADE balance")
    if req.target < 2 or req.target > 98:
        raise HTTPException(400, "Target must be 2-98")

    game = DiceEngine(rng, session.client_seed)
    result = game.roll(req.bet_amount, req.target)

    if result["payout"] > 0:
        add_demo_deposit(req.wallet_address, result["payout"])

    result["new_balance_units"] = session.balance
    result["new_balance_shade"] = f"{session.balance:,}"
    result["proof"] = rng.get_proof(session.client_seed)
    return result

# ── MINES ──

mines_rooms: dict[str, MinesEngine] = {}

@app.post("/mines/start")
def mines_start(req: MinesRequest):
    session = get_session(req.wallet_address)
    if session.balance < req.bet_amount:
        raise HTTPException(400, "Insufficient $SHADE balance")
    if req.mine_count < 1 or req.mine_count > 24:
        raise HTTPException(400, "Mine count must be 1-24")

    game = MinesEngine(rng, session.client_seed, req.bet_amount, req.mine_count)
    game_id = secrets.token_hex(8)
    mines_rooms[game_id] = game
    session.active_games[game_id] = {"type": "mines", "bet": req.bet_amount}

    return {
        "game_id": game_id,
        "board": game.get_board(),
        "mine_count": req.mine_count,
        "bet_amount": req.bet_amount,
        "bet_display": f"{req.bet_amount:,} SHADE",
        "revealed": [],
        "current_multiplier": 1.0,
        "next_multiplier": game.get_next_multiplier(),
    }

@app.post("/mines/reveal")
def mines_reveal(req: MinesReveal):
    game = mines_rooms.get(req.game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    result = game.reveal(req.tile_index)
    if result.get("busted"):
        del mines_rooms[req.game_id]
        return {
            "game_id": req.game_id,
            "busted": True,
            "board": game.get_board(),
            "mine_positions": game.mine_positions,
            "proof": rng.get_proof(get_session(req.wallet_address).client_seed),
        }
    return {
        "game_id": req.game_id,
        "board": game.get_board(),
        "revealed": game.revealed,
        "current_multiplier": game.current_multiplier,
        "next_multiplier": game.get_next_multiplier(),
        "can_cashout": True,
    }

@app.post("/mines/cashout")
def mines_cashout(req: CashoutRequest):
    session = get_session(req.wallet_address)
    game = mines_rooms.get(req.game_id)
    if not game:
        raise HTTPException(404, "Game not found")

    payout = int(game.bet_amount * game.current_multiplier)
    add_demo_deposit(req.wallet_address, payout)

    del mines_rooms[req.game_id]
    session.active_games.pop(req.game_id, None)

    return {
        "game_id": req.game_id,
        "payout": payout,
        "multiplier": game.current_multiplier,
        "revealed_count": len(game.revealed),
        "mine_positions": game.mine_positions,
        "new_balance_units": session.balance,
        "new_balance_shade": f"{session.balance:,}",
        "proof": rng.get_proof(session.client_seed),
    }

# ── STATIC FILES (serve the frontend) ──

BUILD_DIR = Path(__file__).parent.parent / "build"

# Mount static assets AFTER all API routes — FastAPI resolves explicit routes first
# html=True means /deposit serves deposit.html, /dashboard serves dashboard.html, etc.
app.mount("/", StaticFiles(directory=str(BUILD_DIR), html=True), name="static")

# ── STARTUP ──

if __name__ == "__main__":
    import uvicorn
    casino = get_casino_info()
    print(f"  ⬡ Shadow Syndicate API v1.0 — $SHADE Native")
    print(f"  Network: {casino['network']}")
    print(f"  Token: $SHADE")
    print(f"  Policy ID: {SHADE_POLICY_ID}")
    print(f"  Server seed hash: {rng.get_seed_hash()}")
    print(f"  Blockfrost: {'✓ Connected' if is_configured() else '✗ Demo mode'}")
    print(f"  Frontend: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
