# RogueTD - Procedural Roguelike Tower Defense Game

A procedural roguelike tower defense puzzle game built with Python and Pygame.

## Features

- **Procedural Room Generation**: Generates connected room layouts with guaranteed connectivity
- **Multiple Room Types**: Spawn, normal, boss, shop, and chest rooms
- **Fog of War System**: Explore rooms to reveal the map
- **Player Combat**: Shoot bullets at enemies with mouse controls
- **Enemy AI**: Multiple enemy types with different behaviors
- **Special Rooms**: 
  - Boss rooms (dead ends)
  - Shop rooms (dead ends)  
  - Chest rooms - unlocked and locked variants (dead ends)
  - Hole rooms (special puzzle areas)

## Requirements

- Python 3.7+
- Pygame 2.0+

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Controls

- **WASD** or **Arrow Keys**: Move player
- **Mouse**: Aim and shoot (left click)
- **ESC**: Exit game

## Game Mechanics

- **Room Discovery**: Enter rooms to reveal them on the map
- **Dead End Special Rooms**: Boss, shop, and chest rooms are always dead ends for strategic gameplay
- **Connectivity Validation**: All rooms are guaranteed to be reachable from spawn
- **Hole Rooms**: Special challenge areas accessed by stepping on hole tiles

## Project Structure

- `main.py` - Main game loop and rendering
- `utils/room_generator.py` - Procedural room generation and connectivity
- `entities/` - Game entities (player, enemies, bullets, walls)
- `scenes/hole_room.py` - Special hole room implementation
- `data/room.py` - Room data structure
- `utils/camera.py` - Camera system for following the player

## Development

The game uses a tile-based system with a 16x16 tile grid for rooms and procedural hallway generation to connect them. The world validation system ensures all generated worlds are playable with proper connectivity.
