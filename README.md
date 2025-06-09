# Distributed Tetris Game with AI Heuristic Bot 🎮🧠

This project was developed as part of the final assignment for my Computer Systems Class.
While the core structure was provided, this repository contains my logic and implementation, including a custom Tetris-playing **AI bot powered by a heuristic scoring function**.

## 🧠 Overview

A real-time multiplayer Tetris game server built using Python’s `aiohttp` and WebSockets. It features:
- Player-controlled gameplay and board logic
- Observer mode to watch live games
- An AI bot that autonomously plays Tetris by simulating and evaluating possible moves using heuristics

## 🚀 Features

- ✅ Asynchronous multiplayer Tetris server with WebSocket support
- ✅ AI heuristic bot (`bot.py`) that simulates and scores potential placements in real time
- ✅ Observer functionality via `/snoop` and `/watch`
- ✅ Drop distance prediction, line clearing, and collision detection
- ✅ Graceful shutdown of all WebSocket connections

## 📁 Project Structure

| File       | Description |
|------------|-------------|
| `tetris.py` | Core server logic for game state, tile spawning, and player input |
| `bot.py`    | Autonomous AI bot using a heuristic evaluation strategy |
| `index.html` | (Optional) Web-based player interface |
| `watch.html` | (Optional) Observer interface |

## 🤖 AI Bot Logic

The AI bot connects as a WebSocket client and performs the following:
- Simulates every rotation and column position for the current tile
- Evaluates each move based on a heuristic score, factoring in:
  - Number of lines cleared
  - Number of holes introduced
  - Height of the resulting stack
- Sends the best move to the game server in real time

This approach mimics intelligent decision-making without using machine learning.

## 🛠 Technologies Used

- Python 3
- `aiohttp` for async web and socket communication
- `asyncio` for task scheduling
- Custom tile handling via `tilestub`

## 🧪 How to Run

You can run this project locally using Python 3. The setup is simple and works across platforms.

### ✅ Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/allisonprabakar12/tetris-game.git
   cd tetris-game
   ```
2. Install dependencies
   ```bash
   pip install aiohttp
   ```
3. Start the server
  ```bash
   python3 tetris.py
```
4. (Optional) Start the AI bot
  ```bash
   python3 bot.py
```
🧑‍🏫 Original University VM Deployment (No Longer Active)
This project was originally deployed on a UIUC-managed virtual machine (VM) as part of CS 340: Introduction to Computer Systems. Each student had a dedicated server instance to test their multiplayer Tetris implementation in a distributed environment.

⚠️ Note: That VM infrastructure is no longer active after the semester concluded. This GitHub version contains all code needed to run the game server and bot locally or deploy it independently.


💡 What I Learned

Asynchronous programming and WebSocket management in Python

Game server architecture and real-time state synchronization

Designing and implementing AI-like behavior using heuristics

Clean task shutdown and observer synchronization
