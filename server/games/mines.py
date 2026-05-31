"""Mines engine — 5x5 grid, reveal tiles, cash out before hitting a mine."""

import math

class MinesEngine:
    def __init__(self, rng, client_seed: str, bet_amount: int, mine_count: int):
        self.rng = rng
        self.client_seed = client_seed
        self.bet_amount = bet_amount
        self.mine_count = mine_count
        self.total_tiles = 25
        self.safe_tiles = self.total_tiles - mine_count
        
        # Generate mine positions
        all_positions = list(range(self.total_tiles))
        shuffled = self.rng.shuffle(self.client_seed, all_positions)
        self.mine_positions = set(shuffled[:mine_count])
        self.revealed = []
        self.current_multiplier = 1.0

    def get_board(self) -> list:
        """Return board state: 0=hidden, 1=revealed-safe, -1=mine."""
        board = [0] * self.total_tiles
        for i in self.revealed:
            board[i] = -1 if i in self.mine_positions else 1
        return board

    def get_next_multiplier(self) -> float:
        """Calculate multiplier if next tile is safe."""
        revealed = len(self.revealed)
        if revealed >= self.safe_tiles:
            return self.current_multiplier
        
        remaining_safe = self.safe_tiles - revealed
        remaining_total = self.total_tiles - revealed
        prob = remaining_safe / remaining_total
        house_edge = 0.99
        
        return round(self.current_multiplier / (prob * house_edge), 2)

    def reveal(self, tile_index: int) -> dict:
        if tile_index < 0 or tile_index >= self.total_tiles:
            return {"error": "Invalid tile"}
        if tile_index in self.revealed:
            return {"error": "Tile already revealed"}
        if tile_index in self.mine_positions:
            self.revealed.append(tile_index)
            return {"busted": True, "tile_index": tile_index}
        
        self.revealed.append(tile_index)
        self.current_multiplier = self.get_next_multiplier()
        
        # Recalculate to get the *current* (not next) multiplier
        revealed = len(self.revealed)
        remaining_safe = self.safe_tiles
        remaining_total = self.total_tiles
        
        cum_prob = 1.0
        for i in range(revealed):
            prob = (remaining_safe - i) / (remaining_total - i)
            cum_prob *= prob
        
        self.current_multiplier = round(1.0 / (cum_prob * (0.99 ** revealed)), 2)
        
        return {
            "busted": False,
            "tile_index": tile_index,
            "total_revealed": len(self.revealed),
            "current_multiplier": self.current_multiplier,
        }
