/* =====================================================
   THE SHADOW SYNDICATE - Provably Fair System
   HMAC-SHA256 Implementation & Verification
   ===================================================== */

class FairnessManager {
    constructor() {
        this.clientSeed = '';
        this.serverSeed = '';
        this.serverSeedHash = '';
        this.nonce = 0;
        this.gameHistory = []; // Stores proof data for each game

        this.init();
    }

    async init() {
        this.injectStyles();
        this.injectUI();

        // Load or create fairness data
        this.clientSeed = localStorage.getItem('fairness_clientSeed') || this.generateRandomString(32);
        this.nonce = parseInt(localStorage.getItem('fairness_nonce') || '0');

        // Load game history
        try {
            this.gameHistory = JSON.parse(localStorage.getItem('fairness_gameHistory') || '[]');
        } catch (e) {
            this.gameHistory = [];
        }

        if (!localStorage.getItem('fairness_serverSeed')) {
            await this.rotateServerSeed();
        } else {
            this.serverSeed = localStorage.getItem('fairness_serverSeed');
            this.serverSeedHash = localStorage.getItem('fairness_serverSeedHash');
        }

        this.updateUI();
    }

    injectStyles() {
        if (!document.querySelector('link[href*="fairness.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            // Detect if we're in a subdirectory (games/) or root
            const inSubdir = window.location.pathname.includes('/games/');
            link.href = inSubdir ? '../styles/fairness.css' : 'styles/fairness.css';
            document.head.appendChild(link);
        }
    }

    injectUI() {
        if (!document.getElementById('fairnessToggle')) {
            const header = document.querySelector('.table-header .system-status');
            if (header) {
                const btn = document.createElement('button');
                btn.id = 'fairnessToggle';
                btn.className = 'fairness-toggle';
                btn.innerHTML = '<span>🔒</span> FAIRNESS';
                btn.addEventListener('click', () => this.openModal());
                header.insertBefore(btn, header.firstChild);
            }
        }

        if (document.getElementById('zkModal')) return;

        // Detect Game Type for default selection
        const path = window.location.pathname;
        let defaultGame = 'dice';
        if (path.includes('blackjack')) defaultGame = 'blackjack';
        if (path.includes('mines')) defaultGame = 'mines';

        const modal = document.createElement('div');
        modal.id = 'zkModal';
        modal.className = 'zk-modal';
        modal.innerHTML = `
            <div class="zk-header">
                <div class="zk-title"><span>🛡️</span> PROVABLY FAIR</div>
                <button class="zk-close" id="zkClose">&times;</button>
            </div>
            <div class="zk-body">
                <div class="zk-tabs">
                    <button class="zk-tab active" data-tab="live">LIVE STATUS</button>
                    <button class="zk-tab" data-tab="history">GAME HISTORY</button>
                </div>

                <!-- TAB: LIVE STATUS -->
                <div class="zk-view active" id="view-live">
                    <div class="zk-circuit" id="zkCircuit">
                        <div class="circuit-path">
                            <div class="circuit-node" title="Server Seed">S</div>
                            <div class="circuit-line" id="line1"></div>
                            <div class="circuit-node hashing" title="HMAC Function">ƒ</div>
                            <div class="circuit-line" id="line2"></div>
                            <div class="circuit-node" title="Result">R</div>
                        </div>
                    </div>

                    <div class="seed-group">
                        <label class="seed-label">Client Seed (Public)</label>
                        <div class="seed-input-wrapper">
                            <input type="text" class="seed-input" id="clientSeedInput">
                            <button class="seed-btn" id="rotateClientBtn" title="Rotate Seed">↻</button>
                        </div>
                    </div>

                    <div class="seed-group">
                        <label class="seed-label">Server Seed Hash (Hidden)</label>
                        <div class="seed-input-wrapper">
                            <input type="text" class="seed-input" id="serverHashInput" readonly>
                        </div>
                    </div>

                    <div class="seed-group">
                        <label class="seed-label">Nonce (Game Count)</label>
                        <div class="seed-input-wrapper">
                            <input type="text" class="seed-input" id="nonceInput" readonly>
                        </div>
                    </div>
                    
                    <div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8rem; font-family: monospace; margin-top: 10px;">
                        VERIFIED BY ZK-SNARK MOCK PROOF
                    </div>
                </div>

                <!-- TAB: GAME HISTORY -->
                <div class="zk-view" id="view-history">
                    <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 15px;">
                        Click any game to <strong>verify it was fair</strong>. Each game stores its exact seeds and result.
                    </div>

                    <div id="gameHistoryList" style="max-height: 300px; overflow-y: auto;">
                        <!-- Game history items injected here -->
                    </div>

                    <div id="verifyResultContainer" class="hidden" style="margin-top: 15px;">
                        <!-- Verification result injected here -->
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        this.bindModalEvents();
    }

    bindModalEvents() {
        // Close
        document.getElementById('zkClose').addEventListener('click', () => this.closeModal());

        // Tabs
        document.querySelectorAll('.zk-tab').forEach(t => {
            t.addEventListener('click', () => {
                document.querySelectorAll('.zk-tab').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.zk-view').forEach(v => v.classList.remove('active'));

                t.classList.add('active');
                document.getElementById(`view-${t.dataset.tab}`).classList.add('active');

                // Render history when switching to that tab
                if (t.dataset.tab === 'history') {
                    this.renderGameHistory();
                }
            });
        });

        // Live Actions
        document.getElementById('rotateClientBtn').addEventListener('click', () => this.rotateClientSeed());
        document.getElementById('clientSeedInput').addEventListener('change', (e) => {
            this.clientSeed = e.target.value;
            localStorage.setItem('fairness_clientSeed', this.clientSeed);
        });
    }

    renderGameHistory() {
        const container = document.getElementById('gameHistoryList');
        const verifyContainer = document.getElementById('verifyResultContainer');
        verifyContainer.classList.add('hidden');

        if (this.gameHistory.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 30px; color: rgba(255,255,255,0.4);">
                    No games played yet. Play a game and it will appear here!
                </div>
            `;
            return;
        }

        // Show most recent games first (limit to last 20)
        const recentGames = this.gameHistory.slice(-20).reverse();

        container.innerHTML = recentGames.map((game, idx) => {
            const gameIcon = game.gameType === 'dice' ? '🎲' :
                game.gameType === 'blackjack' ? '🃏' : '💣';
            const resultDisplay = game.gameType === 'dice' ? game.result.toFixed(2) :
                game.gameType === 'blackjack' ? `${game.result.length} cards` :
                    `Mines: ${game.result.map(p => p + 1).join(', ')}`;

            return `
                <div class="history-item" data-index="${this.gameHistory.length - 1 - idx}" style="
                    background: rgba(45, 212, 191, 0.05);
                    border: 1px solid rgba(45, 212, 191, 0.2);
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 10px;
                    cursor: pointer;
                    transition: all 0.2s;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.2rem;">${gameIcon}</span>
                            <span style="font-weight: bold; margin-left: 8px;">Game #${game.nonce}</span>
                            <span style="color: rgba(255,255,255,0.5); margin-left: 10px; font-size: 0.8rem;">
                                ${new Date(game.timestamp).toLocaleTimeString()}
                            </span>
                        </div>
                        <div style="color: var(--phosphor-green); font-family: 'Share Tech Mono', monospace;">
                            ${resultDisplay}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Bind click events
        container.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                const idx = parseInt(item.dataset.index);
                this.verifyHistoricalGame(idx);
            });
            item.addEventListener('mouseenter', () => {
                item.style.background = 'rgba(45, 212, 191, 0.15)';
                item.style.borderColor = 'var(--phosphor-green)';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = 'rgba(45, 212, 191, 0.05)';
                item.style.borderColor = 'rgba(45, 212, 191, 0.2)';
            });
        });
    }

    async verifyHistoricalGame(index) {
        const game = this.gameHistory[index];
        if (!game) return;

        const container = document.getElementById('verifyResultContainer');

        // Re-calculate the result using stored seeds
        let recalculatedResult;
        let resultDisplay;

        if (game.gameType === 'dice') {
            recalculatedResult = await this.generateFloat(game.clientSeed, game.serverSeed, game.nonce, 0, 100);
            resultDisplay = recalculatedResult.toFixed(2);
        } else if (game.gameType === 'blackjack') {
            // Create same deck format as blackjack.js
            const suits = ['hearts', 'diamonds', 'clubs', 'spades'];
            const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
            let rawDeck = [];
            for (let suit of suits) {
                for (let value of values) {
                    rawDeck.push({ suit, value });
                }
            }
            const shuffledDeck = await this.generateShuffle(game.clientSeed, game.serverSeed, game.nonce, rawDeck);
            // Convert to same string format as stored
            recalculatedResult = shuffledDeck.map(c => `${c.value}${c.suit}`);
            resultDisplay = recalculatedResult.slice(0, 4).join(', ') + '...';
        } else if (game.gameType === 'mines') {
            recalculatedResult = await this.generateMines(game.clientSeed, game.serverSeed, game.nonce, 25, game.mineCount || 3);
            resultDisplay = recalculatedResult.join(', ');
        }

        // Check if recalculated matches stored
        let isMatch = false;
        if (game.gameType === 'dice') {
            isMatch = Math.abs(recalculatedResult - game.result) < 0.01;
        } else if (game.gameType === 'blackjack') {
            isMatch = JSON.stringify(recalculatedResult) === JSON.stringify(game.result);
        } else if (game.gameType === 'mines') {
            isMatch = JSON.stringify(recalculatedResult) === JSON.stringify(game.result);
        }

        const matchLabel = isMatch ?
            '<span style="color: var(--phosphor-green); font-size: 1.2rem; font-weight: bold;">✅ VERIFIED FAIR!</span>' :
            '<span style="color: #ef4444; font-size: 1.2rem; font-weight: bold;">❌ MISMATCH (ERROR)</span>';

        // Generate external verification data
        const hmacMessage = `${game.clientSeed}:${game.nonce}`;
        const hmacHash = await this.hmacSha256(game.serverSeed, hmacMessage);

        // Build proof object for copying
        const proofData = {
            game: game.gameType.toUpperCase(),
            serverSeed: game.serverSeed,
            clientSeed: game.clientSeed,
            nonce: game.nonce,
            hmacMessage: hmacMessage,
            hmacResult: hmacHash,
            result: game.gameType === 'dice' ? game.result.toFixed(2) : game.result,
            formula: `HMAC-SHA256(serverSeed, "${hmacMessage}") = ${hmacHash}`,
            diceConversion: game.gameType === 'dice' ? `parseInt("${hmacHash.substring(0, 8)}", 16) / 4294967296 * 100 = ${(parseInt(hmacHash.substring(0, 8), 16) / 4294967296 * 100).toFixed(2)}` : null
        };

        container.innerHTML = `
            <div class="verify-result-card" style="
                background: rgba(45, 212, 191, 0.05);
                border: 1px dashed var(--phosphor-green);
                padding: 15px;
                border-radius: 8px;
            ">
                <div style="text-align: center; margin-bottom: 15px;">${matchLabel}</div>
                
                <!-- FULL SEED DISPLAY -->
                <div style="font-size: 0.7rem; color: rgba(255,255,255,0.8); font-family: monospace; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                    <div style="margin-bottom: 8px;">
                        <strong style="color: var(--phosphor-green);">Server Seed:</strong><br>
                        <span style="word-break: break-all; user-select: all;">${game.serverSeed}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong style="color: var(--phosphor-green);">Client Seed:</strong><br>
                        <span style="word-break: break-all; user-select: all;">${game.clientSeed}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong style="color: var(--phosphor-green);">Nonce:</strong> ${game.nonce}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong style="color: var(--phosphor-green);">HMAC Message:</strong><br>
                        <span style="user-select: all;">${hmacMessage}</span>
                    </div>
                    <div>
                        <strong style="color: var(--phosphor-green);">HMAC Result:</strong><br>
                        <span style="word-break: break-all; user-select: all;">${hmacHash}</span>
                    </div>
                </div>

                <!-- FORMULA -->
                <div style="font-size: 0.65rem; color: rgba(255,255,255,0.5); text-align: center; margin-bottom: 10px;">
                    ${game.gameType === 'dice' ?
                `Dice: parseInt(hash[0:8], 16) / 2³² × 100 = <strong>${resultDisplay}</strong>` :
                `Result generated via seeded Fisher-Yates / LCG`
            }
                </div>

                <!-- COPY BUTTON -->
                <button id="copyProofBtn" style="
                    width: 100%;
                    background: var(--phosphor-green);
                    color: black;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-family: 'Orbitron', sans-serif;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.2s;
                ">
                    📋 COPY PROOF FOR EXTERNAL VERIFICATION
                </button>

                <div style="font-size: 0.6rem; color: rgba(255,255,255,0.4); text-align: center; margin-top: 10px;">
                    Use any online HMAC-SHA256 calculator to verify independently
                </div>
            </div>
        `;
        container.classList.remove('hidden');

        // Bind copy button
        document.getElementById('copyProofBtn').addEventListener('click', () => {
            const text = `=== SHADOW SYNDICATE PROVABLY FAIR PROOF ===
Game: ${proofData.game}
Timestamp: ${new Date(game.timestamp).toISOString()}

--- SEEDS ---
Server Seed: ${proofData.serverSeed}
Client Seed: ${proofData.clientSeed}
Nonce: ${proofData.nonce}

--- VERIFICATION ---
HMAC-SHA256 Key: ${proofData.serverSeed}
HMAC-SHA256 Message: ${proofData.hmacMessage}
HMAC-SHA256 Result: ${proofData.hmacResult}

--- RESULT ---
${proofData.game === 'DICE' ? `Dice Roll: ${proofData.result}
Formula: parseInt(hmac[0:8], 16) / 4294967296 * 100
${proofData.diceConversion}` : `Result: ${JSON.stringify(proofData.result)}`}

--- MANUAL VERIFICATION ---
1. Go to any HMAC-SHA256 calculator (e.g., https://www.freeformatter.com/hmac-generator.html)
2. Enter Server Seed as the Key
3. Enter "${proofData.hmacMessage}" as the Message
4. Select SHA-256
5. Compare the output hash with: ${proofData.hmacResult}
`;
            navigator.clipboard.writeText(text).then(() => {
                const btn = document.getElementById('copyProofBtn');
                btn.textContent = '✅ COPIED!';
                btn.style.background = '#22c55e';
                setTimeout(() => {
                    btn.textContent = '📋 COPY PROOF FOR EXTERNAL VERIFICATION';
                    btn.style.background = 'var(--phosphor-green)';
                }, 2000);
            });
        });
    }

    // Record a game to history - called by game scripts after each game
    recordGame(gameType, result, mineCount = null) {
        const record = {
            gameType,
            result,
            clientSeed: this.clientSeed,
            serverSeed: this.serverSeed,
            serverSeedHash: this.serverSeedHash,
            nonce: this.nonce,
            mineCount,
            timestamp: Date.now()
        };

        this.gameHistory.push(record);

        // Keep only last 50 games
        if (this.gameHistory.length > 50) {
            this.gameHistory = this.gameHistory.slice(-50);
        }

        localStorage.setItem('fairness_gameHistory', JSON.stringify(this.gameHistory));

        return record;
    }

    // Record game using pre-captured proof data (for delayed recording)
    // This allows capturing seeds at game start but recording after game ends
    recordGameWithProof(gameType, result, mineCount, proof) {
        const record = {
            gameType,
            result,
            clientSeed: proof.clientSeed,
            serverSeed: proof.serverSeed,
            serverSeedHash: proof.serverSeedHash || '',
            nonce: proof.nonce,
            mineCount,
            timestamp: Date.now()
        };

        this.gameHistory.push(record);

        // Keep only last 50 games
        if (this.gameHistory.length > 50) {
            this.gameHistory = this.gameHistory.slice(-50);
        }

        localStorage.setItem('fairness_gameHistory', JSON.stringify(this.gameHistory));

        return record;
    }

    openModal() {
        document.getElementById('zkModal').classList.add('visible');
        this.updateUI();
        this.runCircuitAnimation();
    }

    closeModal() {
        document.getElementById('zkModal').classList.remove('visible');
    }

    runCircuitAnimation() {
        const line1 = document.getElementById('line1');
        const line2 = document.getElementById('line2');
        if (!line1 || !line2) return;

        line1.classList.remove('active');
        line2.classList.remove('active');

        void line1.offsetWidth;

        line1.classList.add('active');
        setTimeout(() => {
            line2.classList.add('active');
        }, 500);
    }

    async rotateServerSeed() {
        this.serverSeed = this.generateRandomString(64);
        this.serverSeedHash = await this.sha256(this.serverSeed);

        localStorage.setItem('fairness_serverSeed', this.serverSeed);
        localStorage.setItem('fairness_serverSeedHash', this.serverSeedHash);

        this.updateUI();
    }

    rotateClientSeed() {
        this.clientSeed = this.generateRandomString(32);
        localStorage.setItem('fairness_clientSeed', this.clientSeed);
        this.updateUI();
        return this.clientSeed;
    }

    incrementNonce() {
        this.nonce++;
        localStorage.setItem('fairness_nonce', this.nonce.toString());
        this.updateUI();
        return this.nonce;
    }

    updateUI() {
        // Legacy/Sidebar elements
        const elClient = document.getElementById('clientSeed');
        const elServerHash = document.getElementById('serverSeedHash');
        const elNonce = document.getElementById('nonce');

        if (this.clientSeed && elClient) {
            if (elClient.tagName === 'INPUT') elClient.value = this.clientSeed;
            else elClient.textContent = this.clientSeed.substring(0, 12) + '...';
        }
        if (this.serverSeedHash && elServerHash) elServerHash.textContent = this.serverSeedHash.substring(0, 16) + '...';
        if (elNonce) elNonce.textContent = this.nonce;

        // CANONICAL ZK MODAL ELEMENTS
        const modClient = document.getElementById('clientSeedInput');
        const modServer = document.getElementById('serverHashInput');
        const modNonce = document.getElementById('nonceInput');

        if (modClient) modClient.value = this.clientSeed;
        if (modServer) modServer.value = this.serverSeedHash;
        if (modNonce) modNonce.value = this.nonce;
    }

    // --- UTILS ---

    generateRandomString(length) {
        const chars = 'abcdef0123456789';
        let result = '';
        const randomValues = new Uint32Array(length);
        window.crypto.getRandomValues(randomValues);
        for (let i = 0; i < length; i++) {
            result += chars[randomValues[i] % chars.length];
        }
        return result;
    }

    async sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    }

    async hmacSha256(key, message) {
        const enc = new TextEncoder();
        const keyData = await crypto.subtle.importKey(
            "raw",
            enc.encode(key),
            { name: "HMAC", hash: "SHA-256" },
            false,
            ["sign"]
        );
        const signature = await crypto.subtle.sign(
            "HMAC",
            keyData,
            enc.encode(message)
        );

        return Array.from(new Uint8Array(signature))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    // --- GAME RESULT GENERATORS ---

    async generateFloat(clientSeed, serverSeed, nonce, min, max) {
        const message = `${clientSeed}:${nonce}`;
        const hash = await this.hmacSha256(serverSeed, message);
        const subHash = hash.substring(0, 8);
        const value = parseInt(subHash, 16);
        const floatVal = value / 4294967296;
        return min + (floatVal * (max - min));
    }

    async generateShuffle(clientSeed, serverSeed, nonce, deck) {
        const message = `${clientSeed}:${nonce}`;
        const hash = await this.hmacSha256(serverSeed, message);
        const rng = new SeededRNG(hash);
        const shuffled = [...deck];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(rng.nextFloat() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    async generateMines(clientSeed, serverSeed, nonce, gridSize, mineCount) {
        const message = `${clientSeed}:${nonce}`;
        const hash = await this.hmacSha256(serverSeed, message);
        const rng = new SeededRNG(hash);
        const positions = new Set();
        let safety = 0;
        while (positions.size < mineCount && safety < 1000) {
            const pos = Math.floor(rng.nextFloat() * gridSize);
            positions.add(pos);
            safety++;
        }
        return Array.from(positions).sort((a, b) => a - b);
    }
}

// Simple Seeded RNG
class SeededRNG {
    constructor(seedHex) {
        this.state = parseInt(seedHex.substring(0, 8), 16);
    }
    nextFloat() {
        this.state = (this.state * 1664525 + 1013904223) % 4294967296;
        return this.state / 4294967296;
    }
}

window.ShadowSyndicate = window.ShadowSyndicate || {};
window.ShadowSyndicate.Fairness = new FairnessManager();
