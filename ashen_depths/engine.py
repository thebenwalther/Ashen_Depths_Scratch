"""Main game engine: state machine, input handling, game loop."""
from __future__ import annotations
import curses
import sys
from enum import Enum, auto
from .constants import (NUM_FLOORS, T_STAIRS_DOWN, T_STAIRS_UP, FOV_RADIUS,
                         MAX_INVENTORY)
from .data import CLASSES, FLOOR_LORE
from .entities import Player, Item
from .dungeon import DungeonFloor
from .renderer import Renderer, MIN_W, MIN_H


class State(Enum):
    TITLE       = auto()
    CHAR_CREATE = auto()
    EXPLORING   = auto()
    INVENTORY   = auto()
    LEVEL_UP    = auto()
    GAME_OVER   = auto()
    VICTORY     = auto()
    CONFIRM_QUIT = auto()


# Movement keys
MOVE_KEYS = {
    curses.KEY_UP:    (0, -1),
    curses.KEY_DOWN:  (0,  1),
    curses.KEY_LEFT:  (-1, 0),
    curses.KEY_RIGHT: (1,  0),
    ord('k'): (0, -1), ord('j'): (0,  1),
    ord('h'): (-1, 0), ord('l'): (1,  0),
    ord('w'): (0, -1), ord('s'): (0,  1),
    ord('a'): (-1, 0), ord('d'): (1,  0),
    # Diagonals (vim-style)
    ord('y'): (-1, -1), ord('u'): (1, -1),
    ord('b'): (-1,  1), ord('n'): (1,  1),
}


class GameEngine:
    def __init__(self, stdscr):
        self.stdscr   = stdscr
        self.renderer = Renderer(stdscr)
        self.state    = State.TITLE

        # Title menu
        self._title_sel   = 0  # 0=New Game, 1=Quit

        # Character creation
        self._cc_name      = ''
        self._cc_class_sel = 0
        self._cc_classes   = list(CLASSES.keys())

        # Game state
        self.player:  Player | None       = None
        self.dungeon: DungeonFloor | None = None
        self.messages: list[str]          = []
        self._pending_level_up: dict | None = None

        # Inventory screen
        self._inv_sel = 0

        # Confirm dialog
        self._confirm_sel = False  # False = No, True = Yes

        # After-death reason
        self._death_reason = ''

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            h, w = self.stdscr.getmaxyx()
            if h < MIN_H or w < MIN_W:
                self.renderer.render_too_small()
                key = self.stdscr.getch()
                continue

            self._render()
            key = self.stdscr.getch()
            if key == curses.KEY_RESIZE:
                continue
            self._handle_input(key)

    # ------------------------------------------------------------------
    # Rendering dispatch
    # ------------------------------------------------------------------

    def _render(self):
        r = self.renderer
        if self.state == State.TITLE:
            r.render_title(self._title_sel)
        elif self.state == State.CHAR_CREATE:
            r.render_char_create(self._cc_name, self._cc_class_sel,
                                  self._cc_classes, CLASSES)
        elif self.state == State.EXPLORING:
            r.render_game(self.dungeon, self.player, self.messages)
        elif self.state == State.INVENTORY:
            r.render_inventory(self.player, self._inv_sel, 'normal')
        elif self.state == State.LEVEL_UP:
            r.render_level_up(self.player, self._pending_level_up or {})
        elif self.state == State.GAME_OVER:
            r.render_game_over(self.player, self.player.floor, self._death_reason)
        elif self.state == State.VICTORY:
            r.render_victory(self.player)
        elif self.state == State.CONFIRM_QUIT:
            r.render_game(self.dungeon, self.player, self.messages)
            r.render_confirm("Really quit? Progress will be lost.", self._confirm_sel)

    # ------------------------------------------------------------------
    # Input dispatch
    # ------------------------------------------------------------------

    def _handle_input(self, key: int):
        if self.state == State.TITLE:
            self._input_title(key)
        elif self.state == State.CHAR_CREATE:
            self._input_char_create(key)
        elif self.state == State.EXPLORING:
            self._input_exploring(key)
        elif self.state == State.INVENTORY:
            self._input_inventory(key)
        elif self.state == State.LEVEL_UP:
            self.state = State.EXPLORING
        elif self.state == State.GAME_OVER:
            self._reset_to_title()
        elif self.state == State.VICTORY:
            self._reset_to_title()
        elif self.state == State.CONFIRM_QUIT:
            self._input_confirm_quit(key)

    # ------------------------------------------------------------------
    # Title input
    # ------------------------------------------------------------------

    def _input_title(self, key: int):
        if key in (curses.KEY_UP, ord('k'), curses.KEY_DOWN, ord('j')):
            self._title_sel = 1 - self._title_sel
        elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
            if self._title_sel == 0:
                self.state = State.CHAR_CREATE
                self._cc_name = ''
                self._cc_class_sel = 0
            else:
                sys.exit(0)
        elif key == ord('q'):
            sys.exit(0)

    # ------------------------------------------------------------------
    # Character creation input
    # ------------------------------------------------------------------

    def _input_char_create(self, key: int):
        if key in (curses.KEY_ENTER, 10, 13):
            name = self._cc_name.strip() or 'Adventurer'
            cls  = self._cc_classes[self._cc_class_sel]
            self._start_new_game(name, cls)
        elif key in (curses.KEY_DOWN, ord('\t'), curses.KEY_UP):
            n = len(self._cc_classes)
            if key == curses.KEY_UP:
                self._cc_class_sel = (self._cc_class_sel - 1) % n
            else:
                self._cc_class_sel = (self._cc_class_sel + 1) % n
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            self._cc_name = self._cc_name[:-1]
        elif key == 27:  # ESC
            self.state = State.TITLE
        elif 32 <= key <= 126 and len(self._cc_name) < 14:
            self._cc_name += chr(key)

    # ------------------------------------------------------------------
    # Exploring input
    # ------------------------------------------------------------------

    def _input_exploring(self, key: int):
        if key == ord('q'):
            self.state = State.CONFIRM_QUIT
            self._confirm_sel = False
            return

        if key == ord('i'):
            self._inv_sel = 0
            self.state = State.INVENTORY
            return

        if key == ord('.') or key == ord(' '):
            # Wait / rest - monsters still act
            self._do_monsters()
            self._check_death()
            return

        if key == ord('g') or key == ord(','):
            self._try_pickup()
            return

        if key == ord('>'):
            self._try_descend()
            return

        if key == ord('<'):
            self._try_ascend()
            return

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            self._try_move(dx, dy)
            return

    # ------------------------------------------------------------------
    # Inventory input
    # ------------------------------------------------------------------

    def _input_inventory(self, key: int):
        inv = self.player.inventory
        n   = len(inv)

        if key in (curses.KEY_UP, ord('k')) and n > 0:
            self._inv_sel = (self._inv_sel - 1) % n
        elif key in (curses.KEY_DOWN, ord('j')) and n > 0:
            self._inv_sel = (self._inv_sel + 1) % n
        elif key in (curses.KEY_ENTER, 10, 13, ord('e'), ord('u')) and n > 0:
            item = inv[self._inv_sel]
            self._use_item(item)
            self._inv_sel = min(self._inv_sel, max(0, len(self.player.inventory) - 1))
        elif key == ord('d') and n > 0:
            item = inv[self._inv_sel]
            inv.remove(item)
            item.x, item.y = self.player.x, self.player.y
            self.dungeon.items.append(item)
            self._msg(f'You drop the {item.name}.')
            self._inv_sel = min(self._inv_sel, max(0, len(inv) - 1))
        elif key in (27, ord('i'), ord('q')):
            self.state = State.EXPLORING

    def _use_item(self, item: Item):
        if item.kind in ('weapon', 'armor'):
            old = self.player.equip(item)
            if old:
                self._msg(f'You equip the {item.name} (was {old.name}).')
            else:
                self._msg(f'You equip the {item.name}.')
        elif item.kind == 'consumable':
            # Find nearest visible monster for offensive scrolls
            target = None
            if item.effect in ('fire', 'lightning', 'freeze'):
                target = self._nearest_visible_monster()
            msgs = self.player.use_consumable(item, target)
            for m in msgs:
                if m == 'TELEPORT':
                    self.dungeon.teleport_player(self.player)
                    self.dungeon.compute_fov(self.player.x, self.player.y, FOV_RADIUS)
                    self._msg('You vanish in a flash of light!')
                else:
                    self._msg(m)
        # After using, stay in inventory or switch to exploring
        self.state = State.EXPLORING

    # ------------------------------------------------------------------
    # Confirm quit input
    # ------------------------------------------------------------------

    def _input_confirm_quit(self, key: int):
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT, ord('h'), ord('l'),
                   ord('y'), ord('n')):
            self._confirm_sel = not self._confirm_sel
        elif key in (curses.KEY_ENTER, 10, 13):
            if self._confirm_sel:
                sys.exit(0)
            else:
                self.state = State.EXPLORING
        elif key == 27:
            self.state = State.EXPLORING

    # ------------------------------------------------------------------
    # Movement and combat
    # ------------------------------------------------------------------

    def _try_move(self, dx: int, dy: int):
        p = self.player
        nx, ny = p.x + dx, p.y + dy

        if not self.dungeon.in_bounds(nx, ny):
            return

        monster = self.dungeon.monster_at(nx, ny)
        if monster:
            self._player_attack(monster)
            self._do_monsters()
            self._check_death()
            return

        if not self.dungeon.walkable(nx, ny):
            return

        p.x, p.y = nx, ny

        # Auto-pickup amulet
        if (self.dungeon.amulet_pos == (nx, ny) and not p.has_amulet):
            p.has_amulet = True
            self._msg('*** You grasp the Amulet of Depths! Find stairs [<] and escape! ***')

        # Stairs notification
        from .constants import T_STAIRS_DOWN, T_STAIRS_UP
        tile_type = self.dungeon.tile(nx, ny).type
        if tile_type == T_STAIRS_DOWN:
            if p.floor < NUM_FLOORS:
                self._msg('Stairs descend into darkness. Press [>] to go down.')
            else:
                self._msg('A dead end — the depths go no further.')
        elif tile_type == T_STAIRS_UP:
            if p.floor == 1:
                if p.has_amulet:
                    self._msg('The surface! Press [<] to ESCAPE with the Amulet!')
                else:
                    self._msg('The exit — but you need the Amulet of Depths first!')
            else:
                self._msg('Stairs climb upward. Press [<] to ascend.')

        # Item presence notification
        item = self.dungeon.item_at(nx, ny)
        if item:
            self._msg(f'You see a {item.name} here. [g] to pick up.')

        self.dungeon.compute_fov(p.x, p.y, FOV_RADIUS)
        self._do_monsters()
        self._check_death()

    def _player_attack(self, monster):
        roll  = self.player.attack_roll()
        dmg   = max(1, roll - monster.def_)
        monster.hp -= dmg
        self._msg(f'You strike the {monster.name} for {dmg} damage! '
                  f'({monster.hp}/{monster.max_hp} HP)')

        if not monster.alive:
            self._on_monster_kill(monster)

    def _on_monster_kill(self, monster):
        self._msg(f'The {monster.name} is slain!')
        self.player.gold += monster.gold
        leveled = self.player.gain_xp(monster.xp)
        self._msg(f'+{monster.xp} XP, +{monster.gold} gold.')
        self.dungeon.monsters.remove(monster)

        if leveled:
            gains = self.player.level_up()
            self._pending_level_up = gains
            self._msg(f'*** LEVEL UP! You are now level {self.player.level}! ***')
            self.state = State.LEVEL_UP

    def _do_monsters(self):
        """Each living monster takes a turn."""
        p = self.player
        for monster in list(self.dungeon.monsters):
            if not monster.alive:
                continue
            if not self.dungeon.tile(monster.x, monster.y).visible:
                # Only act if player has seen this area recently
                if not self.dungeon.tile(monster.x, monster.y).explored:
                    continue

            adjacent = self.dungeon.move_monster(monster, p)
            if adjacent:
                # Monster attacks
                raw = monster.attack_power()
                dmg = self.player.take_damage(raw)
                self._msg(f'The {monster.name} hits you for {dmg} damage!')

    def _check_death(self):
        if not self.player.alive:
            self._death_reason = 'Slain in the Ashen Depths'
            self.state = State.GAME_OVER

    # ------------------------------------------------------------------
    # Stairs
    # ------------------------------------------------------------------

    def _try_descend(self):
        p = self.player
        tile = self.dungeon.tile(p.x, p.y)
        if tile.type != T_STAIRS_DOWN:
            self._msg('No downward stairs here. Walk onto > to descend.')
            return
        if p.floor >= NUM_FLOORS:
            self._msg('You are already at the deepest floor.')
            return
        p.floor += 1
        self._load_floor(p.floor)
        lore = FLOOR_LORE[min(p.floor - 1, len(FLOOR_LORE) - 1)]
        self._msg(lore)

    def _try_ascend(self):
        p = self.player
        tile = self.dungeon.tile(p.x, p.y)
        if tile.type != T_STAIRS_UP:
            self._msg('No upward stairs here. Walk onto < to ascend.')
            return
        if p.floor == 1:
            # Escape!
            if p.has_amulet:
                self.state = State.VICTORY
            else:
                self._msg('You must find the Amulet of Depths before you can escape!')
            return
        p.floor -= 1
        self._load_floor(p.floor)
        self._msg(f'You climb back up to floor {p.floor}.')

    # ------------------------------------------------------------------
    # Pickup
    # ------------------------------------------------------------------

    def _try_pickup(self):
        p = self.player
        item = self.dungeon.item_at(p.x, p.y)
        if not item:
            self._msg('Nothing here to pick up.')
            return
        if len(p.inventory) >= MAX_INVENTORY:
            self._msg('Your backpack is full! Drop something first.')
            return
        self.dungeon.remove_item(item)
        p.pick_up(item)
        self._msg(f'You pick up the {item.name}.')

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _nearest_visible_monster(self):
        p = self.player
        best, best_dist = None, float('inf')
        for m in self.dungeon.monsters:
            if not m.alive:
                continue
            if not self.dungeon.tile(m.x, m.y).visible:
                continue
            dist = abs(m.x - p.x) + abs(m.y - p.y)
            if dist < best_dist:
                best, best_dist = m, dist
        return best

    def _msg(self, text: str):
        self.messages.append(text)
        if len(self.messages) > 200:
            self.messages = self.messages[-100:]

    # ------------------------------------------------------------------
    # New game / floor loading
    # ------------------------------------------------------------------

    def _start_new_game(self, name: str, class_name: str):
        self.player   = Player(name, class_name)
        self.messages = []
        self._load_floor(1)
        self._msg(f'Welcome, {name} the {class_name}!')
        self._msg('Descend to floor 10, find the Amulet, and return to the surface.')
        self._msg(FLOOR_LORE[0])
        self.state = State.EXPLORING

    def _load_floor(self, floor_num: int):
        self.player.floor = floor_num
        self.dungeon = DungeonFloor(floor_num, self.player)
        self.dungeon.compute_fov(self.player.x, self.player.y, FOV_RADIUS)

    def _reset_to_title(self):
        self.player   = None
        self.dungeon  = None
        self.messages = []
        self.state    = State.TITLE
        self._title_sel = 0
