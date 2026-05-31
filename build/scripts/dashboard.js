/**
 * Shadow Syndicate — Command Deck
 * Real-time wallet, leaderboard, deposit history, game activity.
 */
class Dashboard {
    constructor() {
        this.stats = { totalWagers: 0, totalProfit: 0, biggestWin: 0 };
        this.init();
    }

    init() {
        this.loadStats();
        this.bindEvents();
        this.updateUI();
        this.loadDepositHistory();
        window.addEventListener('wallet:balanceUpdated', () => this.updateUI());
        window.addEventListener('wallet:connected', () => {
            this.updateWalletDisplay();
            this.updateLeaderboard();
            this.loadDepositHistory();
            this.logActivity('Wallet connected', 'success');
        });
        window.addEventListener('wallet:disconnected', () => {
            document.getElementById('walletAddressDisplay').textContent = 'Not Connected';
            this.updateLeaderboard();
        });
    }

    loadStats() {
        const saved = localStorage.getItem('shadowSyndicate_stats');
        if (saved) this.stats = JSON.parse(saved);
        this.updateStatsDisplay();
    }

    saveStats() {
        localStorage.setItem('shadowSyndicate_stats', JSON.stringify(this.stats));
    }

    updateStatsDisplay() {
        const tw = document.getElementById('totalWagers');
        if (tw) tw.textContent = this.stats.totalWagers.toLocaleString();
        const tp = document.getElementById('totalProfit');
        if (tp) {
            const p = this.stats.totalProfit;
            tp.textContent = (p >= 0 ? '+' : '') + p.toLocaleString();
            tp.style.color = p >= 0 ? 'var(--state-success)' : 'var(--state-error)';
        }
        const bw = document.getElementById('biggestWin');
        if (bw) bw.textContent = this.stats.biggestWin.toLocaleString();
    }

    async loadDepositHistory() {
        const wallet = window.ShadowSyndicate?.wallet();
        const logEl = document.getElementById('depositLog');
        if (!logEl) return;
        if (!wallet?.connected) {
            logEl.innerHTML = '<div class="terminal-log__line"><span class="terminal-log__message">Connect wallet to see deposit history.</span></div>';
            return;
        }
        try {
            const r = await fetch(`${SYNDICATE_API}/deposit/history/${encodeURIComponent(wallet.address)}`, {headers: {'ngrok-skip-browser-warning': '1'}});
            const d = await r.json();
            // Filter to real blockchain deposits only (exclude game_ and demo_ records)
            const realDeposits = (d.deposits || []).filter(dep =>
                !dep.tx_hash.startsWith('game_') && !dep.tx_hash.startsWith('demo_') && dep.shade_amount > 0
            );
            const total = realDeposits.reduce((s, dep) => s + dep.shade_amount, 0);
            const td = document.getElementById('totalDeposited');
            if (td) td.textContent = total.toLocaleString();
            if (!d.deposits?.length) {
                logEl.innerHTML = '<div class="terminal-log__line"><span class="terminal-log__message">No deposits yet. <a href="deposit.html" style="color:var(--holo-teal);">Deposit $SHADE</a></span></div>';
                return;
            }
            logEl.innerHTML = d.deposits.slice().reverse().slice(0, 20).map(dep => {
                const isGame = dep.tx_hash.startsWith('game_');
                const label = isGame ? (dep.shade_amount >= 0 ? 'WIN' : 'BET') : 'DEPOSIT';
                const color = dep.shade_amount >= 0 ? 'var(--state-success)' : 'var(--state-error)';
                return `<div class="terminal-log__line">
                    <span class="terminal-log__timestamp">${dep.timestamp?.substring(11,19) || '--:--:--'}</span>
                    <span class="terminal-log__prefix" style="color:${color};">[${label}]</span>
                    <span class="terminal-log__message">${dep.shade_amount >= 0 ? '+' : ''}${dep.shade_display} $SHADE</span>
                </div>`;
            }).join('');
        } catch(e) {
            logEl.innerHTML = '<div class="terminal-log__line"><span class="terminal-log__message">Server offline</span></div>';
        }
    }

    updateWalletDisplay() {
        const wallet = window.ShadowSyndicate?.wallet();
        const addrEl = document.getElementById('walletAddressDisplay');
        if (wallet?.connected && wallet.address) {
            if (addrEl) {
                addrEl.textContent = wallet.shortenAddress(wallet.address);
                addrEl.title = wallet.address;
                addrEl.style.color = 'var(--state-success)';
            }
            this.logActivity(`Wallet: ${wallet.walletName?.toUpperCase() || 'CONNECTED'}`, 'info');
            this.logActivity(`Balance: ${wallet.getBalance().toLocaleString()} $SHADE`, 'info');
        } else {
            if (addrEl) {
                addrEl.textContent = 'Not Connected';
                addrEl.style.color = 'var(--text-muted)';
            }
        }
    }

    logActivity(msg, type) {
        const logEl = document.getElementById('activityLog');
        if (!logEl) return;
        const now = new Date();
        const ts = now.toTimeString().substring(0, 8);
        const colors = { success: 'var(--state-success)', error: 'var(--state-error)', warning: 'var(--holo-gold)', info: 'var(--holo-teal)' };
        const line = document.createElement('div');
        line.className = 'terminal-log__line';
        line.innerHTML = `<span class="terminal-log__timestamp">${ts}</span><span class="terminal-log__message" style="color:${colors[type] || 'var(--text-secondary)'};">${msg}</span>`;
        logEl.appendChild(line);
        logEl.scrollTop = logEl.scrollHeight;
    }

    bindEvents() {
        document.getElementById('clearLogsBtn')?.addEventListener('click', () => {
            const log = document.getElementById('activityLog');
            if (log) log.innerHTML = '';
            this.logActivity('Logs cleared', 'info');
        });
    }

    updateUI() {
        const wallet = window.ShadowSyndicate?.wallet();
        if (wallet?.connected && wallet.address) {
            this.updateWalletDisplay();
        }
        this.updateLeaderboard();
    }

    updateLeaderboard() {
        const tbody = document.getElementById('leaderboardBody');
        if (!tbody) return;
        const wallet = window.ShadowSyndicate?.wallet();
        const userBalance = wallet?.getBalance() || 0;
        const mockData = [
            { name: 'Whale_01', balance: 450200 },
            { name: 'GhostVal0r', balance: 320150 },
            { name: 'NullPtr_Ex', balance: 180900 },
            { name: 'Satoshi_Legacy', balance: 145000 },
        ];
        if (wallet?.connected) {
            mockData.push({ name: 'YOU', balance: userBalance, isUser: true });
        }
        mockData.sort((a, b) => b.balance - a.balance);
        mockData.forEach((item, i) => item.rank = i + 1);
        tbody.innerHTML = mockData.slice(0, 5).map(item => `
            <tr style="border-bottom:1px solid var(--void-border);${item.isUser ? 'background:rgba(0,240,255,0.05);border-left:2px solid var(--holo-teal);' : ''}">
                <td style="padding:var(--space-4);color:${item.rank <= 3 ? 'var(--holo-teal)' : 'var(--text-secondary)'};font-family:var(--font-mono);">${item.rank}</td>
                <td style="padding:var(--space-4);color:${item.isUser ? 'var(--holo-teal)' : 'var(--text-primary)'};font-weight:${item.isUser ? '600' : '400'};">${item.name}</td>
                <td style="padding:var(--space-4);text-align:right;font-family:var(--font-mono);color:var(--text-secondary);">${item.balance.toLocaleString()}</td>
            </tr>
        `).join('');
    }

    /** Called by games after each round */
    recordWager(game, betAmount, won, payout) {
        const profit = won ? (payout - betAmount) : -betAmount;
        this.stats.totalWagers++;
        this.stats.totalProfit += profit;
        if (won && profit > this.stats.biggestWin) this.stats.biggestWin = profit;
        this.saveStats();
        this.updateStatsDisplay();
        this.loadDepositHistory();
        const label = won ? 'WIN' : 'LOSS';
        const color = won ? 'success' : 'error';
        this.logActivity(`[${game}] ${label}: ${(profit >= 0 ? '+' : '') + profit.toLocaleString()} $SHADE`, color);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => { window.dashboard = new Dashboard(); }, 200);
});
