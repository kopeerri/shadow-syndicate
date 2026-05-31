/* =====================================================
   THE SHADOW SYNDICATE - Mines (Grid Breach)
   ZK-Verified Mines Game Logic
   ===================================================== */

class MinesGame {
    constructor() {
        this.gridSize = 25; // 5x5
        this.mineCount = 3;
        this.betAmount = 1000;
        // Sync with HTML input if present
        const input = document.getElementById('betAmountInput');
        if (input) this.betAmount = parseInt(input.value) || 1000;
        this.revealedCount = 0;
        this.gameActive = false;
        this.minePositions = [];
        this.revealedPositions = [];
        this.nonce = 0;

        this.init();
    }

    init() {
        this.createGrid();
        this.updateMultiplierTable();
        this.bindEvents();

        // Listen for balance updates from WalletManager
        window.addEventListener('wallet:balanceUpdated', (e) => {
            const balanceDisplay = document.getElementById('balanceDisplay');
            if (balanceDisplay) balanceDisplay.textContent = e.detail.balance.toLocaleString() + ' SHADE';
        });

        // Sync nonce
        this.nonce = parseInt(localStorage.getItem('mines_nonce') || '0');
    }

    createGrid() {
        const grid = document.getElementById('minesGrid');
        if (!grid) return;

        grid.innerHTML = '';

        for (let i = 0; i < this.gridSize; i++) {
            const cell = document.createElement('div');
            cell.className = 'mine-cell';
            cell.dataset.index = i;
            grid.appendChild(cell);
        }
    }

    bindEvents() {
        // Grid cells
        const grid = document.getElementById('minesGrid');
        if (grid) {
            grid.addEventListener('click', (e) => {
                const cell = e.target.closest('.mine-cell');
                if (cell && this.gameActive && !cell.classList.contains('revealed')) {
                    this.revealCell(parseInt(cell.dataset.index));
                }
            });
        }

        // Mine count selector
        const mineSelect = document.getElementById('mineCount');
        if (mineSelect) {
            mineSelect.addEventListener('change', (e) => {
                this.mineCount = parseInt(e.target.value);
                this.updateMultiplierTable();
            });
        }

        // Bet input
        const betInput = document.getElementById('betAmountInput');
        if (betInput) {
            betInput.addEventListener('change', (e) => {
                let value = parseInt(e.target.value);
                if (value < 100) value = 100;
                if (value > 50000) value = 50000;
                this.betAmount = value;
                e.target.value = value;
            });
        }

        // Start button
        const startBtn = document.getElementById('startGameBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startGame());
        }

        // Cashout button
        const cashoutBtn = document.getElementById('cashoutBtn');
        if (cashoutBtn) {
            cashoutBtn.addEventListener('click', () => this.cashOut());
        }
    }

    async startGame() {
        if (this.gameActive) return;

        const wallet = window.ShadowSyndicate?.wallet();
        if (!wallet?.connected) {
            window.ShadowSyndicate?.modal()?.open('walletModal');
            return;
        }

        if (wallet.getBalance() < this.betAmount) {
            alert('Insufficient balance');
            return;
        }

        // Deduct bet
        wallet.updateBalance(-this.betAmount);

        // Reset game state
        this.gameActive = true;
        this.revealedCount = 0;
        this.revealedPositions = [];

        // Generate mines using PROVABLY FAIR Logic
        this.minePositions = await this.generateMines();

        // Store proof data NOW (before nonce increments) but DON'T record to history yet
        // This prevents cheating by opening another tab to see mine positions
        const fairness = window.ShadowSyndicate.Fairness;
        this.currentGameProof = {
            clientSeed: fairness.clientSeed,
            serverSeed: fairness.serverSeed,
            nonce: fairness.nonce,
            mineCount: this.mineCount,
            minePositions: this.minePositions
        };

        // Increment nonce immediately (proof data already captured)
        fairness.incrementNonce();

        // Update UI
        this.resetGridUI();

        const startBtn = document.getElementById('startGameBtn');
        const playControls = document.getElementById('playControls');
        const settingsControls = document.getElementById('settingsControls');

        if (startBtn) startBtn.classList.add('hidden');
        if (settingsControls) settingsControls.classList.add('hidden');
        if (playControls) playControls.classList.remove('hidden');

        // Update stats
        this.updateStatsUI();

        const elMulti = document.getElementById('currentMultiplier');
        if (elMulti) elMulti.textContent = '1.00x';

        this.updatePotentialWin();
    }

    async generateMines() {
        const fairness = window.ShadowSyndicate.Fairness;
        return await fairness.generateMines(
            fairness.clientSeed,
            fairness.serverSeed,
            fairness.nonce,
            this.gridSize,
            this.mineCount
        );
    }

    resetGridUI() {
        document.querySelectorAll('.mine-cell').forEach(cell => {
            cell.classList.remove('revealed', 'mine', 'gem');
            cell.innerHTML = '';
            cell.style.cursor = 'pointer';
        });
    }

    revealCell(index) {
        if (!this.gameActive) return;
        if (this.revealedPositions.includes(index)) return;

        const cell = document.querySelector(`.mine-cell[data-index="${index}"]`);
        if (!cell) return;

        cell.classList.add('revealed');
        this.revealedPositions.push(index);

        if (this.minePositions.includes(index)) {
            // Hit a mine - Game Over
            cell.classList.add('mine');
            cell.innerHTML = '<img src="../assets/mine.png" alt="Mine" class="cell-icon">';
            this.revealAllMines();
            this.endGame(false);
        } else {
            // Safe cell - Gem found
            cell.classList.add('gem');
            cell.innerHTML = '<img src="../assets/gem.png" alt="Gem" class="cell-icon">';
            this.revealedCount++;
            this.updateMultiplier();
            this.updatePotentialWin();
            this.updateStatsUI();

            // Check for win condition (all safe cells revealed)
            const safeCells = this.gridSize - this.mineCount;
            if (this.revealedCount >= safeCells) {
                this.cashOut();
            }
        }
    }

    revealAllMines() {
        this.minePositions.forEach(pos => {
            const cell = document.querySelector(`.mine-cell[data-index="${pos}"]`);
            if (cell && !cell.classList.contains('revealed')) {
                cell.classList.add('revealed', 'mine');
                cell.innerHTML = '<img src="../assets/mine.png" alt="Mine" class="cell-icon">';
            }
        });
    }

    updateMultiplier() {
        const multi = this.getMultiplier();
        const elMulti = document.getElementById('currentMultiplier');
        if (elMulti) {
            elMulti.textContent = multi.toFixed(2) + 'x';
        }
    }

    getMultiplier() {
        if (this.revealedCount === 0) return 1;

        // Proper probability-based multiplier:
        // Each safe reveal: (remaining cells) / (remaining safe cells)
        // More mines = fewer safe cells = higher multiplier per reveal
        const totalCells = this.gridSize;
        const mines = this.mineCount;
        let multiplier = 1;

        for (let i = 0; i < this.revealedCount; i++) {
            const cellsLeft = totalCells - i;
            const safeCellsLeft = totalCells - mines - i;
            multiplier *= cellsLeft / safeCellsLeft;
        }

        // Apply house edge (2%)
        multiplier *= 0.98;
        return Math.max(1, multiplier);
    }

    updateMultiplierTable() {
        const table = document.getElementById('multiplierTable');
        if (!table) return;

        const totalCells = this.gridSize;
        const mines = this.mineCount;
        const safeCells = totalCells - mines;
        let html = '';

        for (let gems = 1; gems <= Math.min(5, safeCells); gems++) {
            let multi = 1;
            for (let i = 0; i < gems; i++) {
                const cellsLeft = totalCells - i;
                const safeCellsLeft = totalCells - mines - i;
                multi *= cellsLeft / safeCellsLeft;
            }
            multi *= 0.98; // 2% house edge
            html += `<div class="multiplier-row">
                <span>${gems} gem${gems > 1 ? 's' : ''}</span>
                <span>${multi.toFixed(2)}x</span>
            </div>`;
        }

        table.innerHTML = html;
    }

    updateStatsUI() {
        const elRevealed = document.getElementById('revealedCount');
        const elSafeLeft = document.getElementById('safeLeft');

        if (elRevealed) elRevealed.textContent = this.revealedCount;
        if (elSafeLeft) elSafeLeft.textContent = this.gridSize - this.mineCount - this.revealedCount;
    }

    updatePotentialWin() {
        const elWin = document.getElementById('potentialWin');
        if (elWin) {
            const potentialWin = Math.floor(this.betAmount * this.getMultiplier());
            elWin.textContent = potentialWin.toLocaleString();
        }
    }

    cashOut() {
        if (!this.gameActive) return;

        const winAmount = Math.floor(this.betAmount * this.getMultiplier());
        const wallet = window.ShadowSyndicate?.wallet();
        if (wallet) {
            wallet.updateBalance(winAmount);
        }

        // Reveal mines on cashout so player sees where they were
        this.revealAllMines();

        this.endGame(true, winAmount);
    }

    endGame(won, winAmount = 0) {
        this.gameActive = false;

        // Report to shared stats
        window.ShadowSyndicate?.recordGameResult('Mines', this.betAmount, won, won ? winAmount : 0);
        if (window.dashboard) {
            window.dashboard.recordWager('Mines', this.betAmount, won, won ? winAmount : 0);
        }

        // NOW record game to history
        if (this.currentGameProof) {
            window.ShadowSyndicate.Fairness.recordGameWithProof(
                'mines',
                this.currentGameProof.minePositions,
                this.currentGameProof.mineCount,
                this.currentGameProof
            );
            this.currentGameProof = null;
        }

        // Disable all cells
        document.querySelectorAll('.mine-cell').forEach(cell => {
            cell.style.cursor = 'default';
        });

        // Update UI logic to switch back to settings
        const startBtn = document.getElementById('startGameBtn');
        const playControls = document.getElementById('playControls');
        const settingsControls = document.getElementById('settingsControls');

        if (startBtn) startBtn.classList.remove('hidden');
        if (settingsControls) settingsControls.classList.remove('hidden');
        if (playControls) playControls.classList.add('hidden');

        if (won) {
            const elMulti = document.getElementById('currentMultiplier');
            if (elMulti) {
                elMulti.style.color = 'var(--holo-teal)';
                elMulti.style.textShadow = '0 0 20px var(--holo-teal)';
            }
        } else {
            document.querySelector('.mines-layout')?.classList.add('screen-shake');
            setTimeout(() => {
                document.querySelector('.mines-layout')?.classList.remove('screen-shake');
            }, 500);

            const elMulti = document.getElementById('currentMultiplier');
            if (elMulti) {
                elMulti.textContent = '0.00x';
                elMulti.style.color = 'var(--holo-pink)';
            }
        }

        // Reset UI after delay
        setTimeout(() => {
            const elMulti = document.getElementById('currentMultiplier');
            if (elMulti) {
                elMulti.style.color = '';
                elMulti.style.textShadow = '';
                elMulti.textContent = '1.00x';
            }

            const elWin = document.getElementById('potentialWin');
            if (elWin) elWin.style.display = '';

        }, 3000);
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.minesGame = new MinesGame();
});
