# Little Go AI Agent

## Overview
This project implements an AI agent to play Little-Go (5x5 Go) using advanced game-playing algorithms including Alpha-Beta pruning with minimax search. The agent competes against various AI opponents in a tournament-style grading system.

## Game Description
Little-Go is a simplified version of the traditional Go game played on a 5×5 board instead of the standard 19×19. The objective is to surround more territory than the opponent by strategically placing stones while following specific game rules.

### Key Rules
- **Liberty Rule**: Every stone must have at least one adjacent empty space (liberty) or be part of a connected group with liberties
- **KO Rule**: Prevents immediate recapture that would return the board to a previous state
- **Scoring**: Partial area scoring - count of stones on board plus Komi compensation for White (2.5 points)
