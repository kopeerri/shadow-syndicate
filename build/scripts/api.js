/**
 * SHADOW SYNDICATE — $SHADE Betting API Client
 */
class SyndicateAPI {
    constructor() {
        this.baseURL = SYNDICATE_API + '';
        this.walletAddress = null;
    }

    setWallet(address) { this.walletAddress = address; }

    async _post(path, body) {
        const res = await fetch(`${this.baseURL}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' },
            body: JSON.stringify({ ...body, wallet_address: this.walletAddress }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || 'API error');
        }
        return res.json();
    }

    async _get(path) {
        const res = await fetch(`${this.baseURL}${path}`, {
            headers: { 'ngrok-skip-browser-warning': '1' },
        });
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
    }

    // Session
    async getSession() { return this._get(`/session/${this.walletAddress}`); }

    // Deposits
    async getDepositInfo() { return this._get('/deposit/info'); }
    async checkDeposits() { return this._get(`/deposit/check/${this.walletAddress}`); }
    async getDepositHistory() { return this._get(`/deposit/history/${this.walletAddress}`); }

    // Fairness
    async getSeedHash() { return this._get('/fairness/seed-hash'); }

    // Blackjack
    async blackjackStart(betShade) { return this._post('/blackjack/start', { bet_amount: betShade }); }
    async blackjackAction(gameId, action) { return this._post('/blackjack/action', { game_id: gameId, action }); }

    // Dice
    async diceRoll(betShade, target) { return this._post('/dice/roll', { bet_amount: betShade, target }); }

    // Mines
    async minesStart(betShade, mineCount) { return this._post('/mines/start', { bet_amount: betShade, mine_count: mineCount }); }
    async minesReveal(gameId, tileIndex) { return this._post('/mines/reveal', { game_id: gameId, tile_index: tileIndex }); }
    async minesCashout(gameId) { return this._post('/mines/cashout', { game_id: gameId }); }
}

const API = new SyndicateAPI();
