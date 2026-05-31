"""Dice engine — roll under to win."""

class DiceEngine:
    def __init__(self, rng, client_seed: str):
        self.rng = rng
        self.client_seed = client_seed

    def roll(self, bet_amount: int, target: int) -> dict:
        """
        Roll 0-99. If result < target, player wins.
        Payout = bet * (99 / target) adjusted for 1% house edge.
        """
        result = self.rng.roll_int(self.client_seed, 0, 99)
        won = result < target
        
        if won:
            # 1% house edge: multiply by 0.99
            multiplier = (99 / target) * 0.99
            payout = int(bet_amount * multiplier)
            if payout < bet_amount:
                payout = bet_amount  # minimum is money back
        else:
            payout = 0
        
        return {
            "roll": result,
            "target": target,
            "won": won,
            "payout": payout,
            "multiplier": round(payout / bet_amount, 2) if payout > 0 else 0,
            "bet_amount": bet_amount,
        }
