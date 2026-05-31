/* =====================================================
   THE SHADOW SYNDICATE - Dice (Quantum Entropy)
   ZK-Verified Dice Game Logic
   ===================================================== */

class DiceGame {
    constructor() {
        this.target = 50.00;
        this.betAmount = 100;
        this.isRolling = false;
        this.houseEdge = 1.5; // 1.5% House Edge
        this.nonce = 0;

        this.init();
    }

    init() {
        this.bindEvents();
        this.updateStats();
        this.updateSliderUI();

        // Listen for balance updates from WalletManager
        window.addEventListener('wallet:balanceUpdated', (e) => {
            const balanceDisplay = document.getElementById('balanceDisplay');
            if (balanceDisplay) balanceDisplay.textContent = e.detail.balance.toLocaleString() + ' SHADE';
        });

        // Initial UI Sync from centralized manager
        window.ShadowSyndicate.Fairness.updateUI();
    }

    bindEvents() {
        const slider = document.getElementById('targetSlider');
        if (slider) {
            // Update slider attributes for precision
            slider.min = "2.00";
            slider.max = "98.00";
            slider.step = "0.01"; // Allow decimals

            slider.addEventListener('input', (e) => {
                this.target = parseFloat(e.target.value);
                this.updateStats();
                this.updateSliderUI();
            });
        }

        document.querySelectorAll('[data-bet]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleBetClick(e.target.dataset.bet));
        });

        const rollBtn = document.getElementById('rollBtn');
        if (rollBtn) {
            rollBtn.addEventListener('click', () => this.roll());
        }
    }

    // Removed local seed generation methods (now in FairnessManager)

    handleBetClick(action) {
        if (this.isRolling) return;

        const wallet = window.ShadowSyndicate?.wallet();
        const maxBet = wallet?.getBalance() ?? 0;
        if (maxBet <= 0) return;

        switch (action) {
            case 'half':
                this.betAmount = Math.max(100, Math.floor(this.betAmount / 2));
                break;
            case 'double':
                this.betAmount = Math.min(this.betAmount * 2, maxBet, 50000);
                break;
            case 'max':
                this.betAmount = Math.min(maxBet, 50000);
                break;
            default:
                const amount = parseInt(action);
                if (!isNaN(amount)) {
                    this.betAmount = Math.min(this.betAmount + amount, maxBet, 50000);
                }
        }

        this.updateBetDisplay();
        // Update stats as bet amount affects potential profit
        this.updateStats();
    }

    updateBetDisplay() {
        const betDisplay = document.getElementById('betAmount');
        if (betDisplay) {
            // Check formatted string
            const val = this.betAmount >= 1000 ? (this.betAmount / 1000).toFixed(1) + 'k' : this.betAmount;
            betDisplay.textContent = this.betAmount.toLocaleString();
        }
    }

    getWinChance() {
        // Win if result < target. So if target is 50, result 0-49 wins. Chance is target set.
        // E.g. Target 50.00 -> 50% chance.
        return this.target;
    }

    getMultiplier() {
        // Multiplier = (100 - House Edge) / Win Chance
        const winChance = this.getWinChance();
        if (winChance <= 0) return 0;
        return (100 - this.houseEdge) / winChance;
    }

    getProfitOnWin() {
        const totalPayout = this.betAmount * this.getMultiplier();
        return Math.floor(totalPayout - this.betAmount);
    }

    updateStats() {
        const winChance = this.getWinChance();
        const multiplier = this.getMultiplier();
        const profit = this.getProfitOnWin();

        const elWin = document.getElementById('winChance');
        const elMulti = document.getElementById('multiplier');
        const elProfit = document.getElementById('profitOnWin');

        if (elWin) elWin.textContent = `${winChance.toFixed(2)}%`;
        if (elMulti) elMulti.textContent = `${multiplier.toFixed(4)}x`; // 4 decimal precision
        if (elProfit) elProfit.textContent = profit.toLocaleString();
    }

    updateSliderUI() {
        const fill = document.getElementById('sliderFill');
        const thumb = document.getElementById('sliderThumb');
        const value = document.getElementById('sliderValue');

        if (!fill || !thumb || !value) return;

        // Visual position based on percent (0-100)
        const percent = this.target;

        fill.style.width = `${percent}%`;
        thumb.style.left = `${percent}%`;
        value.textContent = this.target.toFixed(2);
    }

    async roll() {
        if (this.isRolling) return;

        const wallet = window.ShadowSyndicate?.wallet();
        if (!wallet?.connected) {
            window.ShadowSyndicate?.modal()?.open('walletModal');
            return;
        }

        if (wallet.getBalance() < this.betAmount) {
            alert('Insufficient balance');
            return;
        }

        this.isRolling = true;
        const rollBtn = document.getElementById('rollBtn');
        if (rollBtn) rollBtn.disabled = true;

        // Deduct bet locally (server sync happens at end)

        // Show rolling animation
        const resultEl = document.getElementById('diceResult');
        resultEl.classList.add('rolling');
        resultEl.classList.remove('win', 'lose');

        // Scramble animation
        const scrambleInterval = setInterval(() => {
            // Show random decimals during roll
            const r = (Math.random() * 100).toFixed(2);
            resultEl.textContent = r;
        }, 50);

        // Simulate proof delay
        await this.delay(600);

        // PROVABLY FAIR GENERATION
        const fairness = window.ShadowSyndicate.Fairness;
        const result = await fairness.generateFloat(
            fairness.clientSeed,
            fairness.serverSeed,
            fairness.nonce,
            0, 100
        );

        // Round to 2 decimals for display/comparison
        const finalResult = Math.round(result * 100) / 100;
        const finalResultStr = finalResult.toFixed(2);

        clearInterval(scrambleInterval);
        resultEl.textContent = finalResultStr;
        resultEl.classList.remove('rolling');

        // Determine win/lose (Win if roll < target)
        // e.g. Target 50.00. Roll 49.99 -> Win. Roll 50.00 -> Loss.
        const isWin = finalResult < this.target;

        if (isWin) {
            resultEl.classList.add('win');
            const totalWin = this.betAmount * this.getMultiplier();
            const profit = Math.floor(totalWin - this.betAmount);
            wallet.updateBalance(profit);  // sync net profit to server

            // Report to shared stats
            window.ShadowSyndicate?.recordGameResult('Dice', this.betAmount, true, totalWin);
            if (window.dashboard) {
                window.dashboard.recordWager('Dice', this.betAmount, true, totalWin);
            }

            // Reflow pulse
            resultEl.style.animation = 'none';
            resultEl.offsetHeight;
            resultEl.style.animation = 'pulse-text 0.5s ease-out';

            const status = document.getElementById('rollStatus');
            if (status) status.textContent = "WINNER";
        } else {
            resultEl.classList.add('lose');
            wallet.updateBalance(-this.betAmount);  // sync loss to server

            // Report to shared stats
            window.ShadowSyndicate?.recordGameResult('Dice', this.betAmount, false, 0);
            if (window.dashboard) {
                window.dashboard.recordWager('Dice', this.betAmount, false, 0);
            }

            document.querySelector('.dice-layout')?.classList.add('screen-shake');
            setTimeout(() => {
                document.querySelector('.dice-layout')?.classList.remove('screen-shake');
            }, 500);

            const status = document.getElementById('rollStatus');
            if (status) status.textContent = "CRITICAL FAIL";
        }

        // Record game BEFORE incrementing nonce (captures exact state used for this roll)
        fairness.recordGame('dice', finalResult);

        // Increment Nonce via Manager
        fairness.incrementNonce();

        this.isRolling = false;
        if (rollBtn) rollBtn.disabled = false;

        setTimeout(() => {
            const status = document.getElementById('rollStatus');
            if (status) status.textContent = "";
            resultEl.classList.remove('win', 'lose');
        }, 2000);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.diceGame = new DiceGame();
});
