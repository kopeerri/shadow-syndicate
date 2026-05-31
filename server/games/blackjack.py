"""Blackjack game engine — provably fair."""

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

class BlackjackEngine:
    def __init__(self, rng, client_seed: str, bet_amount: int):
        self.rng = rng
        self.client_seed = client_seed
        self.bet_amount = bet_amount
        self.player_hand = []
        self.dealer_hand = []
        self.player_score = 0
        self.dealer_score = 0
        self.game_over = False
        self.result = None
        self.payout = 0
        self.can_double = True
        self._deck = []
        self._build_deck()

    def _build_deck(self):
        deck = [f"{r}{s}" for s in SUITS for r in RANKS] * 6  # 6 decks
        self._deck = self.rng.shuffle(self.client_seed, deck)
        self._deck_index = 0

    def _draw(self):
        card = self._deck[self._deck_index]
        self._deck_index += 1
        return card

    def _card_value(self, card: str) -> int:
        rank = card[:-1]
        if rank == "A":
            return 11
        if rank in ("J", "Q", "K"):
            return 10
        return int(rank)

    def _hand_value(self, hand: list) -> int:
        total = sum(self._card_value(c) for c in hand)
        aces = sum(1 for c in hand if c[:-1] == "A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def deal(self):
        self.player_hand = [self._draw(), self._draw()]
        self.dealer_hand = [self._draw(), self._draw()]
        self.player_score = self._hand_value(self.player_hand)
        self.dealer_score = self._hand_value(self.dealer_hand)
        
        if self.player_score == 21:
            self._resolve()

    def hit(self):
        self.player_hand.append(self._draw())
        self.player_score = self._hand_value(self.player_hand)
        self.can_double = False
        if self.player_score >= 21:
            self._resolve()

    def stand(self):
        self.can_double = False
        while self._hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self._draw())
        self.dealer_score = self._hand_value(self.dealer_hand)
        self._resolve()

    def double_down(self):
        self.bet_amount *= 2
        self.player_hand.append(self._draw())
        self.player_score = self._hand_value(self.player_hand)
        self.can_double = False
        if self.player_score > 21:
            self._resolve()
        else:
            self.stand()

    def _resolve(self):
        self.game_over = True
        p = self.player_score
        d = self.dealer_score
        
        if p > 21:
            self.result = "bust"
            self.payout = 0
        elif d > 21:
            self.result = "dealer_bust"
            self.payout = self.bet_amount * 2
        elif p == 21 and len(self.player_hand) == 2:
            self.result = "blackjack"
            self.payout = int(self.bet_amount * 2.5)
        elif p > d:
            self.result = "win"
            self.payout = self.bet_amount * 2
        elif p == d:
            self.result = "push"
            self.payout = self.bet_amount
        else:
            self.result = "lose"
            self.payout = 0

    def get_state(self) -> dict:
        state = {
            "player_hand": self.player_hand,
            "dealer_hand": self.dealer_hand if self.game_over else [self.dealer_hand[0], "???"],
            "player_score": self.player_score,
            "dealer_score": self.dealer_score if self.game_over else self._card_value(self.dealer_hand[0]),
            "game_over": self.game_over,
            "can_double": self.can_double,
        }
        if self.game_over:
            state["result"] = self.result
            state["payout"] = self.payout
        return state
