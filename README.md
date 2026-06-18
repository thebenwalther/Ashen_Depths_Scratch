# Ashen Depths

A roguelike dungeon crawler played entirely in the terminal. Descend into the Ashen Depths, fight monsters, collect loot, and escape with the Amulet.

```
    _         _                 ____             _   _
   / \   ___ | |__   ___ _ __  |  _ \  ___ _ __ | |_| |__  ___
  / _ \ / __|| '_ \ / _ \ '_ \ | | | |/ _ \ '_ \| __| '_ \/ __|
 / ___ \\__ \| | | |  __/ | | || |_| |  __/ |_) | |_| | | \__ \
/_/   \_\___/|_| |_|\___|_| |_||____/ \___| .__/ \__|_| |_|___/
                                           |_|
```

## Features

- **Procedurally generated dungeons** — 10 floors of rooms and corridors, different every run
- **Fog of war** — explore the unknown; only lit tiles are fully visible, explored tiles stay dimly visible
- **Turn-based combat** — bump into enemies to attack; every move counts
- **3 playable classes** — Warrior, Rogue, and Mage, each with different stats and starting gear
- **12 enemy types** — from weak Ash Rats on floor 1 to the Ashen Lord boss on floor 10
- **Equipment system** — find and equip weapons and armor to grow stronger as you descend
- **Consumables** — health potions, scrolls of fire, lightning, freeze, and teleport
- **XP and leveling** — defeat enemies to level up and gain stat bonuses
- **Pure terminal TUI** — built with Python's standard `curses` library, no dependencies

## Requirements

- Python 3.8+
- A terminal at least 80×24 (larger is better)

No external packages required.

## Installation

```bash
git clone https://github.com/thebenwalther/Ashen_Depths_Scratch.git
cd Ashen_Depths_Scratch
python3 main.py
```

## How to Play

### Goal

Descend to **floor 10**, defeat the Ashen Lord, pick up the **Amulet of Depths**, then climb back up and escape through floor 1.

### Controls

| Key | Action |
|-----|--------|
| `h` / `←` | Move left |
| `l` / `→` | Move right |
| `k` / `↑` | Move up |
| `j` / `↓` | Move down |
| `y` `u` `b` `n` | Move diagonally |
| `.` or `Space` | Wait (pass turn) |
| `g` or `,` | Pick up item |
| `i` | Open inventory |
| `>` | Descend stairs |
| `<` | Ascend stairs |
| `q` | Quit (with confirmation) |

**In the inventory screen:**

| Key | Action |
|-----|--------|
| `↑` / `k` | Move selection up |
| `↓` / `j` | Move selection down |
| `e` / `Enter` | Equip (weapon/armor) or Use (consumable) |
| `d` | Drop item |
| `Esc` / `i` | Close inventory |

### Combat

Walk into an enemy to attack. Enemies attack back on their turn. Damage is based on your attack stat minus their defense (and vice versa). Offensive scrolls (fire, lightning, freeze) automatically target the nearest visible enemy.

### Classes

| Class | HP | ATK | DEF | Playstyle |
|-------|----|-----|-----|-----------|
| **Warrior** | 70 | 10 | 8 | Resilient tank. Forgiving for new players. |
| **Rogue** | 50 | 14 | 5 | High damage, lower survivability. |
| **Mage** | 42 | 8 | 4 | Starts with 2 offensive scrolls. Fragile but powerful. |

### Enemies by Floor

| Floors | Enemies |
|--------|---------|
| 1–4 | Ash Rats, Cinder Bats, Cave Spiders, Skeletons |
| 3–7 | Ember Hounds, Ashen Ghosts, Shadow Stalkers |
| 5–8 | Bone Knights |
| 6–10 | Infernal Wraiths, Lava Golems, Crypt Liches |
| 8–10 | Ashen Drakes |
| 10 only | **The Ashen Lord** (boss) |

## Project Structure

```
Ashen_Depths_Scratch/
├── main.py                  # Entry point
└── ashen_depths/
    ├── constants.py         # Tuning constants and color pair IDs
    ├── data.py              # Monster, weapon, armor, and consumable tables
    ├── entities.py          # Player, Monster, and Item classes
    ├── dungeon.py           # Procedural map generation and FOV
    ├── renderer.py          # Curses TUI rendering
    └── engine.py            # Game loop and state machine
```

## Screenshot

```
                   ########   #########                    |ASHEN DEPTHS
                   #......#   #.......#                    |────────────────────
                   #......#   #...r...#                    |Thorin
                   #......##### .......                    |Warrior Lv.3
                   #......#   #.......#                    |────────────────────
                   ##.##.##   #########                    |HP  45/82
                      #                                    |[████████████░░░░░░]
                   ##.##.#######                           |[▓▓▓▓▓▓░░░░░░░░░░░]
                   #...........@#                          |XP 45/320
                   ##############                          |────────────────────
                                                           |ATK: 17   DEF: 14
                                                           |GOLD: 34
                                                           |────────────────────
                                                           |Floor  3/10
──────────────────────────────────────────────────────────────────────────────
 You strike the Ash Rat for 11 damage! (0/12 HP)
 The Ash Rat is slain!
 +5 XP, +3 gold.
```

## License

MIT
