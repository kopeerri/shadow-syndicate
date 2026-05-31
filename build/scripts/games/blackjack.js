/**
 * SHADOW SYNDICATE - HOLO-BLACKJACK
 * Core Game Logic + Dealer Persona System
 */

class BlackjackGame {
    constructor() {
        this.deck = [];
        this.playerHand = [];
        this.dealerHand = [];
        this.betAmount = 0;  // in lovelace
        this.balance = 0;    // in lovelace, loaded from wallet
        this.gameState = 'betting';
        this.dealers = [];
        this.currentDealer = null;

        this.init();
    }

    init() {
        this.cacheDOM();
        this.initDealers();
        this.bindEvents();
        this.loadBalanceFromWallet();
        this.updateUI();
        // Listen for balance updates from WalletManager
        window.addEventListener('wallet:balanceUpdated', (e) => {
            this.balance = e.detail.balance;
            this.updateUI();
        });
    }

    loadBalanceFromWallet() {
        if (window.ShadowSyndicate) {
            const wm = window.ShadowSyndicate.wallet();
            if (wm && wm.connected) {
                this.balance = wm.balance;
                return;
            }
        }
        const key = `shadowSyndicate_balance_${localStorage.getItem('shadowSyndicate_wallet_addr') || 'default'}`;
        const stored = localStorage.getItem(key);
        this.balance = stored ? parseFloat(stored) : 0;
    }

    syncBalance() {
        // Sync back to WalletManager and localStorage
        this.loadBalanceFromWallet();
        this.updateUI();
    }

    cacheDOM() {
        this.bettingControls = document.getElementById('bettingControls');
        this.playControls = document.getElementById('playControls');
        this.resultPanel = document.getElementById('resultPanel');
        this.balanceDisplay = document.getElementById('balanceDisplay');
        this.currentBetDisplay = document.getElementById('currentBet');
        this.playerScoreDisplay = document.getElementById('playerScore');
        this.dealerScoreDisplay = document.getElementById('dealerScore');
        this.dealerScoreContainer = document.getElementById('dealerScoreDisplay');
        this.dealerSpeech = document.getElementById('dealerSpeech');
        this.dealerNameDisplay = document.getElementById('dealerName');
        this.playerContainer = document.getElementById('playerCards');
        this.dealerContainer = document.getElementById('dealerCards');
        this.dealBtn = document.getElementById('dealBtn');
        this.hitBtn = document.getElementById('hitBtn');
        this.standBtn = document.getElementById('standBtn');
        this.doubleBtn = document.getElementById('doubleBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.newGameBtn = document.getElementById('newGameBtn');
        this.chips = document.querySelectorAll('.chip');
    }

    // ========== DEALER SYSTEM ==========

    initDealers() {
        this.dealers = [
            {
                name: "NOVA",
                id: "nova",
                emoji: "✨",
                desc: "Warm & Supportive",
                color: "#2DD4BF",
                image: "../assets/Dealers/Nova.png",
                lines: {
                    greeting: [
                        "Hey there! Ready to have some fun?",
                        "Welcome back, friend! Let's play!",
                        "Oh, I was hoping you'd show up!",
                        "Good to see you! Feeling lucky today?"
                    ],
                    win: [
                        "Yes! That's what I'm talking about!",
                        "Amazing play! You earned that one!",
                        "I'm so happy for you, honestly!",
                        "Look at you go! Keep it up!"
                    ],
                    lose: [
                        "Aw, don't worry. Next hand could be yours!",
                        "Hey, it happens to everyone. Shake it off!",
                        "Tough break, but I believe in you!",
                        "The cards weren't kind, but you're still in this!"
                    ],
                    bust: [
                        "Ooh, a little too ambitious! It's okay!",
                        "Aw, you got excited! Happens to the best of us.",
                        "Bust! But hey, bold moves are fun!"
                    ],
                    dealer_bust: [
                        "Whoops! I busted! Congrats, that's all you!",
                        "Well, that's embarrassing for me. You win!",
                        "I got too greedy! Your victory!"
                    ],
                    blackjack: [
                        "BLACKJACK! Oh my gosh, that's perfect!",
                        "21! You absolute legend!",
                        "Natural blackjack! I'm genuinely impressed!"
                    ],
                    push: [
                        "A tie! We both played well!",
                        "Push! Great minds think alike, huh?",
                        "Even steven! Let's go again!"
                    ]
                }
            },
            {
                name: "VEXIS",
                id: "vexis",
                emoji: "🔥",
                desc: "Dark Provocateur",
                color: "#F472B6",
                image: "../assets/Dealers/VEXIS.png",
                lines: {
                    greeting: [
                        "Oh great, another one. Let's get this over with.",
                        "You again? Your money's as good as mine.",
                        "Sit down, shut up, and lose already.",
                        "Try not to bore me to death, alright?"
                    ],
                    win: [
                        "Whatever. Enjoy it while it lasts.",
                        "Hmph. Even a broken clock is right twice a day.",
                        "Lucky. Don't let it go to your head.",
                        "Fine, take it. You'll give it back soon enough."
                    ],
                    lose: [
                        "Ha! Called it. Thanks for the donation.",
                        "Pathetic. Absolutely pathetic.",
                        "Did you even try? That was embarrassing.",
                        "Another sucker cleaned out. Next!"
                    ],
                    bust: [
                        "BUST! Greedy little thing, aren't you?",
                        "Over 21? Shocker. Learn to count.",
                        "Hahaha! Crashed and burned!"
                    ],
                    dealer_bust: [
                        "...Shut up. Don't say a word.",
                        "This never happened. Got it?",
                        "A glitch. That's all. A GLITCH."
                    ],
                    blackjack: [
                        "Tch. Whatever. Take your stupid money.",
                        "Blackjack? Are you cheating? You're cheating.",
                        "I hate you. I genuinely hate you."
                    ],
                    push: [
                        "A tie? Waste of my time.",
                        "Push. How incredibly boring.",
                        "We're even? Ugh. Unsatisfying."
                    ]
                }
            },
            {
                name: "ZYX-9",
                id: "zyx9",
                emoji: "👽",
                desc: "Curious Alien",
                color: "#A78BFA",
                image: "../assets/Dealers/ZYX-9.png",
                lines: {
                    greeting: [
                        "Greetings, Earth-player! Ready for card ritual?",
                        "Ah! Human has arrived! Let us exchange rectangles!",
                        "ZYX-9 is pleased! Begin the gambling ceremony!",
                        "Welcome! I have studied your '21' mathematics."
                    ],
                    win: [
                        "You achieved victory! Is this when humans 'celebrate'?",
                        "Impressive calculation! Your neurons fire well!",
                        "You win credits! Do these bring you joy-chemicals?",
                        "Success! I shall record this in my research notes!"
                    ],
                    lose: [
                        "Unfortunate outcome. Your species values resilience, yes?",
                        "I have claimed your credits. Is this upsetting? Curious.",
                        "Loss detected. Do not malfunction, human.",
                        "Your rectangles were insufficient. Try again?"
                    ],
                    bust: [
                        "Over 21! You have exceeded optimal parameters!",
                        "Bust! Too many numbers! Math is unforgiving.",
                        "Your greed-instinct has betrayed you. Interesting."
                    ],
                    dealer_bust: [
                        "I have... busted? This was not in my calculations!",
                        "Error in my probability matrix! You win by default!",
                        "Unacceptable variance! I must recalibrate!"
                    ],
                    blackjack: [
                        "BLACKJACK! The sacred 21! Extraordinary!",
                        "Perfect score! I must study your technique!",
                        "21 on first draw! Are you also non-human?"
                    ],
                    push: [
                        "A tie! Our minds have synchronized!",
                        "Push result! We are equals in this moment!",
                        "Same number! Probability finds this... poetic."
                    ]
                }
            },
            {
                name: "CIPHER",
                id: "cipher",
                emoji: "🧊",
                desc: "Cold Professional",
                color: "#60A5FA",
                image: "../assets/Dealers/CIPHER.png",
                lines: {
                    greeting: [
                        "Player detected. Session initialized.",
                        "Welcome. Your odds have been calculated.",
                        "Shall we proceed? Time is a finite resource.",
                        "Good evening. I trust you've come prepared."
                    ],
                    win: [
                        "Outcome: favorable. Your edge was 2.3%.",
                        "Victory confirmed. Statistically within expectations.",
                        "You've won. Don't let emotion cloud judgment.",
                        "Credits transferred. Optimal play."
                    ],
                    lose: [
                        "Outcome: unfavorable. The house edge applies.",
                        "Loss recorded. This was... predictable.",
                        "Variance works both ways. Next hand.",
                        "Your strategy had flaws. Learn from this."
                    ],
                    bust: [
                        "Bust. Risk management failure detected.",
                        "Over 21. The mathematics were against you.",
                        "You exceeded optimal thresholds. Expected."
                    ],
                    dealer_bust: [
                        "I have exceeded 21. Improbable, but possible.",
                        "Dealer bust. Congratulations are... appropriate.",
                        "Variance favored you this time. It won't last."
                    ],
                    blackjack: [
                        "Natural 21. Probability: 4.83%. Impressive.",
                        "Blackjack. Optimal outcome achieved.",
                        "Perfect hand. Enjoy the 3:2 payout."
                    ],
                    push: [
                        "Push. Neither party gains advantage.",
                        "A tie. Statistically neutral outcome.",
                        "Equal hands. Bet returned. Proceed?"
                    ]
                }
            },
            {
                name: "GLITCH",
                id: "glitch",
                emoji: "⚡",
                desc: "Chaotic Trickster",
                color: "#FBBF24",
                image: "../assets/Dealers/GLITCH.png",
                lines: {
                    greeting: [
                        "HEYYY you're here! This is gonna be WILD!",
                        "Ooooh fresh meat! I mean... fresh friend!",
                        "Let's GO! Chaos awaits! WHEEE!",
                        "Finally! Someone to play with! *vibrates excitedly*"
                    ],
                    win: [
                        "AHAHA you actually won?! I love it!",
                        "Look at you GO! The cards went brrrrr!",
                        "Winner winner chicken dinner! Or whatever!",
                        "YESSS! Chaos favors the bold today!"
                    ],
                    lose: [
                        "Oooof! That was SPICY! Try again?!",
                        "Hehehehe the cards said NOPE!",
                        "Awww you broke! That's hilarious! Wait, no, sad!",
                        "The void claims another! WHOOPSIE!"
                    ],
                    bust: [
                        "KABOOM! You went full send! Respect!",
                        "Bust?! MORE LIKE TRUST THE CHAOS!",
                        "Over 21! You beautiful disaster!"
                    ],
                    dealer_bust: [
                        "I BUSTED?! This is the BEST timeline!",
                        "WAIT I LOST?! AHAHA this is fine!",
                        "Chaos cares not for sides! You win!"
                    ],
                    blackjack: [
                        "BLACK! JACK! THE UNIVERSE SPEAKS!",
                        "21?! On the FIRST TRY?! *explodes*",
                        "PERFECTION! You've hacked reality!"
                    ],
                    push: [
                        "A TIE?! The universe is undecided!",
                        "We're TWINNING! How chaotic!",
                        "Push! The void says 'try again' lol"
                    ]
                }
            }
        ];

        // Start with random dealer
        this.currentDealer = this.dealers[Math.floor(Math.random() * this.dealers.length)];

        // Create dealer selector bar
        this.createDealerBar();
        this.updateDealerUI();

        // Initial Greeting
        setTimeout(() => this.dealerSpeak('greeting'), 500);
    }

    createDealerBar() {
        // Create portrait sidebar
        const portraitsContainer = document.getElementById('dealerPortraits');
        if (!portraitsContainer) return;

        portraitsContainer.innerHTML = this.dealers.map(d => `
            <div class="dealer-portrait" data-id="${d.id}" style="--dealer-color: ${d.color}" title="${d.name} - ${d.desc}">
                <div class="dealer-portrait__frame">
                    <img src="${d.image}" alt="${d.name}" class="dealer-portrait__img">
                </div>
                <span class="dealer-portrait__name">${d.name}</span>
            </div>
        `).join('');

        // Bind click events
        portraitsContainer.querySelectorAll('.dealer-portrait').forEach(portrait => {
            portrait.addEventListener('click', () => {
                if (this.gameState !== 'betting') {
                    this.dealerSpeak('greeting');
                    return;
                }
                this.selectDealer(portrait.dataset.id);
            });
        });
    }

    updateDealerUI() {
        const color = this.currentDealer.color;
        const glowColor = color + '40';

        // Update dealer name displays
        if (this.dealerNameDisplay) {
            this.dealerNameDisplay.textContent = this.currentDealer.name;
            this.dealerNameDisplay.style.color = color;
        }

        // Update showcase name
        const showcaseName = document.getElementById('dealerShowcaseName');
        if (showcaseName) {
            showcaseName.textContent = this.currentDealer.name;
            showcaseName.style.color = color;
        }

        // Update dealer showcase image
        const showcaseImg = document.getElementById('dealerShowcaseImg');
        if (showcaseImg && this.currentDealer.image) {
            showcaseImg.src = this.currentDealer.image;
        }

        // Update showcase styling with dealer color
        const showcase = document.getElementById('dealerShowcase');
        if (showcase) {
            showcase.style.setProperty('--dealer-color', color);
            showcase.style.setProperty('--dealer-glow', glowColor);
        }

        // Update speech panel styling
        const speechPanel = document.getElementById('dealerSpeechPanel');
        if (speechPanel) {
            speechPanel.style.setProperty('--dealer-color', color);
            speechPanel.style.setProperty('--dealer-glow', glowColor);
        }

        // Update portrait sidebar highlight
        document.querySelectorAll('.dealer-portrait').forEach(portrait => {
            portrait.classList.toggle('active', portrait.dataset.id === this.currentDealer.id);
        });

        // Show/hide sidebar based on game state
        const sidebar = document.getElementById('dealerSidebar');
        if (sidebar) {
            sidebar.style.opacity = this.gameState === 'betting' ? '1' : '0.5';
            sidebar.style.pointerEvents = this.gameState === 'betting' ? 'auto' : 'none';
        }
    }

    selectDealer(id) {
        const dealer = this.dealers.find(d => d.id === id);
        if (dealer && dealer.id !== this.currentDealer.id) {
            this.currentDealer = dealer;
            this.updateDealerUI();
            setTimeout(() => this.dealerSpeak('greeting'), 300);
        }
    }

    dealerSpeak(category) {
        const lines = this.currentDealer.lines[category];
        if (!lines || !this.dealerSpeech) return;
        const line = lines[Math.floor(Math.random() * lines.length)];

        this.dealerSpeech.classList.remove('visible');
        setTimeout(() => {
            this.dealerSpeech.textContent = `"${line}"`;
            this.dealerSpeech.classList.add('visible');
        }, 100);
    }

    bindEvents() {
        this.chips.forEach(chip => {
            chip.addEventListener('click', () => {
                const val = chip.dataset.value;
                this.placeBet(val);
            });
        });

        this.dealBtn.addEventListener('click', () => this.deal());
        this.hitBtn.addEventListener('click', () => this.hit());
        this.standBtn.addEventListener('click', () => this.stand());
        this.doubleBtn.addEventListener('click', () => this.double());
        this.clearBtn.addEventListener('click', () => this.clearBet());
        this.newGameBtn.addEventListener('click', () => this.resetGame());

        // Deposit link — handled by anchor href
    }

    placeBet(amount) {
        if (this.gameState !== 'betting') return;

        if (amount === 'max') {
            const MAX_BET = 50000;
            const maxAdd = Math.min(this.balance - this.betAmount, MAX_BET - this.betAmount);
            if (maxAdd > 0) this.betAmount += maxAdd;
        } else {
            const val = parseInt(amount);
            const MAX_BET = 50000;
            const newBet = Math.min(this.betAmount + val, this.balance, MAX_BET);
            this.betAmount = newBet;
        }
        this.updateUI();
    }

    clearBet() {
        if (this.gameState !== 'betting') return;
        this.betAmount = 0;
        this.updateUI();
    }

    async createDeck() {
        const suits = ['hearts', 'diamonds', 'clubs', 'spades'];
        const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
        let rawDeck = [];

        for (let suit of suits) {
            for (let value of values) {
                rawDeck.push({ suit, value });
            }
        }

        // PROVABLY FAIR SHUFFLE
        const fairness = window.ShadowSyndicate.Fairness;
        this.deck = await fairness.generateShuffle(
            fairness.clientSeed,
            fairness.serverSeed,
            fairness.nonce,
            rawDeck
        );
    }

    getCardValue(card) {
        if (['J', 'Q', 'K'].includes(card.value)) return 10;
        if (card.value === 'A') return 11;
        return parseInt(card.value);
    }

    getHandValue(hand) {
        let value = 0;
        let aces = 0;

        hand.forEach(card => {
            if (card.hidden) return;
            value += this.getCardValue(card);
            if (card.value === 'A') aces++;
        });

        while (value > 21 && aces > 0) {
            value -= 10;
            aces--;
        }
        return value;
    }

    async deal() {
        if (this.betAmount === 0) return;

        // Create deck with current nonce
        await this.createDeck();

        // Record game BEFORE incrementing nonce (captures exact deck order)
        window.ShadowSyndicate.Fairness.recordGame('blackjack', this.deck.map(c => `${c.value}${c.suit}`));

        // Increment nonce for next game (after using it for this deck)
        window.ShadowSyndicate.Fairness.incrementNonce();

        this.playerHand = [];
        this.dealerHand = [];
        this.gameState = 'playing';
        this.balance -= this.betAmount;

        this.playerHand.push(this.drawCard());
        this.dealerHand.push(this.drawCard());
        this.playerHand.push(this.drawCard());
        this.dealerHand.push({ ...this.drawCard(), hidden: true });

        if (this.dealerSpeech) {
            this.dealerSpeech.classList.remove('visible');
            this.dealerSpeech.textContent = '';
        }

        this.renderCards();
        this.updateUI();
        this.checkForBlackjack();
    }

    drawCard() {
        return this.deck.pop();
    }

    hit() {
        if (this.gameState !== 'playing') return;
        this.playerHand.push(this.drawCard());
        this.renderCards();

        if (this.getHandValue(this.playerHand) > 21) {
            this.endGame('lose', 'BUSTED');
        } else {
            this.updateUI();
        }
    }

    stand() {
        if (this.gameState !== 'playing') return;
        this.dealerTurn();
    }

    double() {
        if (this.gameState !== 'playing') return;
        if (this.balance >= this.betAmount) {
            this.balance -= this.betAmount;
            this.betAmount *= 2;
            this.playerHand.push(this.drawCard());
            this.renderCards();

            if (this.getHandValue(this.playerHand) > 21) {
                this.endGame('lose', 'BUSTED');
            } else {
                this.dealerTurn();
            }
        }
    }

    dealerTurn() {
        this.gameState = 'dealerTurn';
        this.dealerHand[1].hidden = false;
        this.renderCards();

        const playDealer = () => {
            const dValue = this.getHandValue(this.dealerHand);
            if (dValue < 17) {
                setTimeout(() => {
                    this.dealerHand.push(this.drawCard());
                    this.renderCards();
                    playDealer();
                }, 800);
            } else {
                this.determineWinner();
            }
        };

        playDealer();
    }

    determineWinner() {
        const pValue = this.getHandValue(this.playerHand);
        const dValue = this.getHandValue(this.dealerHand);

        if (dValue > 21) {
            this.endGame('win', 'DEALER BUST');
        } else if (pValue > dValue) {
            this.endGame('win', 'YOU WIN');
        } else if (pValue < dValue) {
            this.endGame('lose', 'DEALER WINS');
        } else {
            this.endGame('push', 'PUSH');
        }
    }

    checkForBlackjack() {
        if (this.getHandValue(this.playerHand) === 21) {
            this.endGame('win', 'BLACKJACK!');
        }
    }

    endGame(result, text) {
        this.gameState = 'ended';
        let payout = 0;
        let dealerCategory = result;

        if (result === 'win') {
            payout = text === 'BLACKJACK!' ? this.betAmount * 2.5 : this.betAmount * 2;
            if (text === 'DEALER BUST') dealerCategory = 'dealer_bust';
            if (text === 'BLACKJACK!') dealerCategory = 'blackjack';
        } else if (result === 'push') {
            payout = this.betAmount;
        } else if (result === 'lose') {
            if (text === 'BUSTED') dealerCategory = 'bust';
        }

        this.balance += payout;
        this.dealerSpeak(dealerCategory);

        // Sync net result to server (payout - bet = what was gained/lost)
        const netDelta = payout - this.betAmount;
        const wallet = window.ShadowSyndicate?.wallet();
        if (wallet && netDelta !== 0) {
            wallet.updateBalance(netDelta);
        }

        // Report to shared stats (works across all pages)
        const won = result === 'win' || result === 'push';
        window.ShadowSyndicate?.recordGameResult('Blackjack', this.betAmount, won, payout);
        // Also update dashboard if open in another tab
        if (window.dashboard) {
            window.dashboard.recordWager('Blackjack', this.betAmount, won, payout);
        }

        setTimeout(() => {
            this.showResultModal(result, text, payout - this.betAmount);
        }, 1500);

        this.updateUI();
    }

    resetGame() {
        this.gameState = 'betting';
        this.betAmount = 0;
        this.playerHand = [];
        this.dealerHand = [];
        this.resultPanel.classList.add('hidden');
        this.renderCards();
        this.updateUI();
    }

    updateUI() {
        this.balanceDisplay.textContent = `${this.balance.toLocaleString()} $SHADE`;
        this.currentBetDisplay.textContent = `${this.betAmount.toLocaleString()} $SHADE`;

        if (this.gameState === 'betting') {
            this.bettingControls.classList.remove('hidden');
            this.playControls.classList.add('hidden');
            this.dealBtn.disabled = this.betAmount === 0;
            this.clearBtn.disabled = this.betAmount === 0;
        } else if (this.gameState === 'playing') {
            this.bettingControls.classList.add('hidden');
            this.playControls.classList.remove('hidden');
        } else {
            this.playControls.classList.add('hidden');
        }

        if (this.playerHand.length > 0) {
            this.playerScoreDisplay.textContent = this.getHandValue(this.playerHand);
            this.dealerScoreDisplay.textContent = this.getHandValue(this.dealerHand);
            this.dealerScoreContainer.classList.remove('hidden');
        } else {
            this.playerScoreDisplay.textContent = '--';
            this.dealerScoreContainer.classList.add('hidden');
        }
    }

    renderCards() {
        this.playerContainer.innerHTML = '';
        this.dealerContainer.innerHTML = '';

        this.playerHand.forEach((card, i) => {
            const el = this.createCardEl(card);
            el.style.animationDelay = `${i * 0.1}s`;
            this.playerContainer.appendChild(el);
        });

        this.dealerHand.forEach((card, i) => {
            const el = this.createCardEl(card);
            el.style.animationDelay = `${i * 0.1}s`;
            this.dealerContainer.appendChild(el);
        });
    }

    createCardEl(card) {
        const div = document.createElement('div');
        div.className = `holo-card suit-${card.suit} animate-deal`;

        if (card.hidden) {
            div.classList.add('hidden');
        } else {
            const suitIcons = { hearts: '♥', diamonds: '♦', clubs: '♣', spades: '♠' };
            div.textContent = `${card.value}${suitIcons[card.suit]}`;
        }
        return div;
    }

    showResultModal(result, title, profit) {
        const titleEl = document.getElementById('resultTitle');
        const amountEl = document.getElementById('resultAmount');

        titleEl.textContent = title;
        amountEl.textContent = profit >= 0 ? `+${profit}` : profit;

        if (result === 'win') titleEl.style.color = 'var(--holo-teal)';
        else if (result === 'lose') titleEl.style.color = 'var(--holo-pink)';

        this.resultPanel.classList.remove('hidden');
    }
}

window.addEventListener('load', () => {
    new BlackjackGame();
});
