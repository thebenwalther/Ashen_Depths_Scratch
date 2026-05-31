"""Curses-based TUI renderer for Ashen Depths."""
from __future__ import annotations
import curses
import textwrap
from .constants import (
    T_WALL, T_FLOOR, T_STAIRS_DOWN, T_STAIRS_UP,
    C_PLAYER, C_MON_WEAK, C_MON_MED, C_MON_STRONG, C_MON_BOSS,
    C_WEAPON, C_ARMOR, C_POTION, C_GOLD, C_AMULET,
    C_WALL_LIT, C_FLOOR_LIT, C_STAIRS,
    C_WALL_DIM, C_FLOOR_DIM,
    C_UI, C_UI_BOLD, C_HP_HI, C_HP_MID, C_HP_LO,
    C_XP, C_TITLE, C_SUCCESS, C_WARNING, C_DANGER, C_SCROLL, C_DIM, C_TRAP,
)

# Map panel will be left portion; stats panel on right
STATS_W  = 26   # width of right stats panel (includes border)
MSG_H    = 7    # height of message log area at bottom
MIN_W    = 80
MIN_H    = 24


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


class Renderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self._init_colors()
        curses.curs_set(0)
        stdscr.keypad(True)

    # ------------------------------------------------------------------
    # Color setup
    # ------------------------------------------------------------------

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()

        def p(idx, fg, bg=-1):
            curses.init_pair(idx, fg, bg)

        p(C_PLAYER,     curses.COLOR_WHITE,   -1)
        p(C_MON_WEAK,   curses.COLOR_GREEN,   -1)
        p(C_MON_MED,    curses.COLOR_YELLOW,  -1)
        p(C_MON_STRONG, curses.COLOR_RED,     -1)
        p(C_MON_BOSS,   curses.COLOR_MAGENTA, -1)
        p(C_WEAPON,     curses.COLOR_CYAN,    -1)
        p(C_ARMOR,      curses.COLOR_BLUE,    -1)
        p(C_POTION,     curses.COLOR_GREEN,   -1)
        p(C_GOLD,       curses.COLOR_YELLOW,  -1)
        p(C_AMULET,     curses.COLOR_MAGENTA, -1)
        p(C_WALL_LIT,   curses.COLOR_WHITE,   -1)
        p(C_FLOOR_LIT,  curses.COLOR_WHITE,   -1)
        p(C_STAIRS,     curses.COLOR_YELLOW,  -1)
        p(C_WALL_DIM,   curses.COLOR_BLACK,   -1)
        p(C_FLOOR_DIM,  curses.COLOR_BLACK,   -1)
        p(C_UI,         curses.COLOR_WHITE,   -1)
        p(C_UI_BOLD,    curses.COLOR_CYAN,    -1)
        p(C_HP_HI,      curses.COLOR_GREEN,   -1)
        p(C_HP_MID,     curses.COLOR_YELLOW,  -1)
        p(C_HP_LO,      curses.COLOR_RED,     -1)
        p(C_XP,         curses.COLOR_CYAN,    -1)
        p(C_TITLE,      curses.COLOR_YELLOW,  -1)
        p(C_SUCCESS,    curses.COLOR_GREEN,   -1)
        p(C_WARNING,    curses.COLOR_YELLOW,  -1)
        p(C_DANGER,     curses.COLOR_RED,     -1)
        p(C_SCROLL,     curses.COLOR_MAGENTA, -1)
        p(C_DIM,        curses.COLOR_BLACK,   -1)
        p(C_TRAP,       curses.COLOR_RED,     -1)

    # ------------------------------------------------------------------
    # Safe draw helpers
    # ------------------------------------------------------------------

    def _safe_addch(self, y, x, ch, attr=0):
        h, w = self.stdscr.getmaxyx()
        if 0 <= y < h and 0 <= x < w - 1:
            try:
                self.stdscr.addch(y, x, ch, attr)
            except curses.error:
                pass

    def _safe_addstr(self, y, x, s, attr=0, max_len=None):
        h, w = self.stdscr.getmaxyx()
        if y < 0 or y >= h or x >= w - 1:
            return
        if x < 0:
            s = s[-x:]
            x = 0
        available = w - 1 - x
        if max_len is not None:
            available = min(available, max_len)
        s = s[:available]
        if s:
            try:
                self.stdscr.addstr(y, x, s, attr)
            except curses.error:
                pass

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _layout(self):
        h, w = self.stdscr.getmaxyx()
        stats_x  = w - STATS_W       # x where stats panel starts
        map_w    = stats_x            # map area width
        map_h    = h - MSG_H          # map area height
        msg_y    = h - MSG_H          # y where messages start
        return h, w, stats_x, map_w, map_h, msg_y

    # ------------------------------------------------------------------
    # Title screen
    # ------------------------------------------------------------------

    def render_title(self, selection: int):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        title_lines = [
            r"    _         _                 ____             _   _            ",
            r"   / \   ___ | |__   ___ _ __  |  _ \  ___ _ __ | |_| |__  ___  ",
            r"  / _ \ / __|| '_ \ / _ \ '_ \ | | | |/ _ \ '_ \| __| '_ \/ __| ",
            r" / ___ \\__ \| | | |  __/ | | || |_| |  __/ |_) | |_| | | \__ \ ",
            r"/_/   \_\___/|_| |_|\___|_| |_||____/ \___| .__/ \__|_| |_|___/ ",
            r"                                           |_|                    ",
        ]

        sub = "~ Descend. Fight. Survive. Escape. ~"
        options = ["[ New Game ]", "[ Quit ]"]

        # Center vertically
        start_y = max(1, h // 2 - 8)

        # Draw title art
        for i, line in enumerate(title_lines):
            x = max(0, (w - len(line)) // 2)
            self._safe_addstr(start_y + i, x, line, curses.color_pair(C_TITLE) | curses.A_BOLD)

        # Subtitle
        sub_y = start_y + len(title_lines) + 1
        self._safe_addstr(sub_y, (w - len(sub)) // 2, sub, curses.color_pair(C_WARNING))

        # Lore blurb
        lore = ("The Amulet of Depths lies on the 10th floor, guarded by the Ashen Lord."
                " Retrieve it and escape to win.")
        lore_y = sub_y + 2
        for i, chunk in enumerate(textwrap.wrap(lore, min(70, w - 4))):
            self._safe_addstr(lore_y + i, (w - len(chunk)) // 2, chunk, curses.color_pair(C_UI))

        # Menu options
        menu_y = lore_y + 4
        for i, opt in enumerate(options):
            attr = (curses.color_pair(C_TITLE) | curses.A_BOLD | curses.A_REVERSE
                    if i == selection else curses.color_pair(C_UI))
            self._safe_addstr(menu_y + i * 2, (w - len(opt)) // 2, opt, attr)

        # Controls hint
        hint = "Arrow keys / Enter to select"
        self._safe_addstr(h - 2, (w - len(hint)) // 2, hint, curses.color_pair(C_DIM))
        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Character creation screen
    # ------------------------------------------------------------------

    def render_char_create(self, name: str, class_sel: int, classes: list[str], class_data: dict):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        title = "=== CREATE YOUR CHARACTER ==="
        self._safe_addstr(2, (w - len(title)) // 2, title,
                          curses.color_pair(C_TITLE) | curses.A_BOLD)

        # Name field
        self._safe_addstr(5, 4, "Your Name: ", curses.color_pair(C_UI_BOLD))
        self._safe_addstr(5, 15, name + "_", curses.color_pair(C_UI) | curses.A_UNDERLINE)

        # Class selection
        self._safe_addstr(8, 4, "Choose Class:", curses.color_pair(C_UI_BOLD))
        for i, cls_name in enumerate(classes):
            cls = class_data[cls_name]
            sel = (i == class_sel)
            attr = (curses.color_pair(C_TITLE) | curses.A_BOLD | curses.A_REVERSE
                    if sel else curses.color_pair(C_UI))
            label = f"  {'>' if sel else ' '} {cls_name:<10}"
            self._safe_addstr(10 + i * 3, 4, label, attr)
            stats = f"    HP:{cls['hp']}  ATK:{cls['atk']}  DEF:{cls['def_']}"
            self._safe_addstr(10 + i * 3 + 1, 4, stats, curses.color_pair(C_DIM))
            desc_y = 10 + i * 3
            if sel:
                self._safe_addstr(desc_y, 36, cls['desc'], curses.color_pair(C_WARNING))

        # Controls
        controls = [
            "Type to enter name   |  Backspace to delete",
            "Tab / Arrow Down to change class",
            "Enter to begin your descent",
        ]
        base_y = h - len(controls) - 2
        for i, ctrl in enumerate(controls):
            self._safe_addstr(base_y + i, 4, ctrl, curses.color_pair(C_DIM))

        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Main game render
    # ------------------------------------------------------------------

    def render_game(self, dungeon, player, messages: list[str]):
        self.stdscr.erase()
        h, w, stats_x, map_w, map_h, msg_y = self._layout()

        self._draw_map(dungeon, player, map_w, map_h)
        self._draw_stats(player, dungeon, stats_x, h)
        self._draw_messages(messages, msg_y, w, h)
        self._draw_controls_hint(h, stats_x)
        self.stdscr.refresh()

    def _draw_map(self, dungeon, player, map_w: int, map_h: int):
        """Draw the dungeon map with camera centered on player."""
        # Camera: try to center on player, but clamp to dungeon bounds
        view_w = map_w - 2    # leave 1 char border
        view_h = map_h - 2

        cam_x = _clamp(player.x - view_w // 2, 0, max(0, dungeon.width  - view_w))
        cam_y = _clamp(player.y - view_h // 2, 0, max(0, dungeon.height - view_h))

        for vy in range(view_h):
            dy = cam_y + vy
            if dy >= dungeon.height:
                break
            for vx in range(view_w):
                dx = cam_x + vx
                if dx >= dungeon.width:
                    break

                screen_x = vx + 1
                screen_y = vy + 1

                tile = dungeon.tile(dx, dy)

                # Player
                if dx == player.x and dy == player.y:
                    attr = curses.color_pair(C_PLAYER) | curses.A_BOLD
                    self._safe_addch(screen_y, screen_x, '@', attr)
                    continue

                # Amulet (floor 10, before pickup)
                if (dungeon.amulet_pos == (dx, dy) and
                        not player.has_amulet and tile.visible):
                    self._safe_addch(screen_y, screen_x, '&',
                                     curses.color_pair(C_AMULET) | curses.A_BOLD)
                    continue

                # Monsters
                monster = dungeon.monster_at(dx, dy)
                if monster and tile.visible:
                    tier_color = {
                        'weak':   C_MON_WEAK,
                        'med':    C_MON_MED,
                        'strong': C_MON_STRONG,
                        'boss':   C_MON_BOSS,
                    }.get(monster.tier, C_MON_MED)
                    attr = curses.color_pair(tier_color)
                    if monster.is_boss:
                        attr |= curses.A_BOLD
                    self._safe_addch(screen_y, screen_x, monster.char, attr)
                    continue

                # Items
                item = dungeon.item_at(dx, dy)
                if item and tile.visible:
                    item_color = {
                        'weapon':     C_WEAPON,
                        'armor':      C_ARMOR,
                        'consumable': C_POTION if item.char == '!' else C_SCROLL,
                    }.get(item.kind, C_UI)
                    self._safe_addch(screen_y, screen_x, item.char,
                                     curses.color_pair(item_color))
                    continue

                # Tile itself
                if tile.visible:
                    ch, attr = self._tile_glyph_lit(tile)
                elif tile.explored:
                    ch, attr = self._tile_glyph_dim(tile)
                else:
                    continue  # unexplored = black

                self._safe_addch(screen_y, screen_x, ch, attr)

    def _tile_glyph_lit(self, tile) -> tuple[str, int]:
        t = tile.type
        if t == T_WALL:
            return '#', curses.color_pair(C_WALL_LIT)
        if t == T_FLOOR:
            return '.', curses.color_pair(C_FLOOR_LIT) | curses.A_DIM
        if t == T_STAIRS_DOWN:
            return '>', curses.color_pair(C_STAIRS) | curses.A_BOLD
        if t == T_STAIRS_UP:
            return '<', curses.color_pair(C_STAIRS) | curses.A_BOLD
        return '.', curses.color_pair(C_FLOOR_LIT)

    def _tile_glyph_dim(self, tile) -> tuple[str, int]:
        t = tile.type
        if t == T_WALL:
            return '#', curses.color_pair(C_WALL_DIM) | curses.A_BOLD
        if t in (T_FLOOR, T_STAIRS_DOWN, T_STAIRS_UP):
            ch = {T_FLOOR: '.', T_STAIRS_DOWN: '>', T_STAIRS_UP: '<'}[t]
            return ch, curses.color_pair(C_FLOOR_DIM) | curses.A_BOLD
        return ' ', 0

    def _draw_stats(self, player, dungeon, stats_x: int, h: int):
        s = self.stdscr
        w_panel = STATS_W

        def put(y, x, text, attr=0):
            self._safe_addstr(y, stats_x + x, text, attr, max_len=w_panel - x - 1)

        bold  = curses.color_pair(C_UI_BOLD)  | curses.A_BOLD
        norm  = curses.color_pair(C_UI)
        dim   = curses.color_pair(C_DIM)
        title = curses.color_pair(C_TITLE)    | curses.A_BOLD
        warn  = curses.color_pair(C_WARNING)
        dang  = curses.color_pair(C_DANGER)
        succ  = curses.color_pair(C_SUCCESS)

        # Vertical divider
        for y in range(h):
            self._safe_addch(y, stats_x, '|', dim)

        row = 0

        # Title
        put(row, 1, "ASHEN DEPTHS", title)
        row += 1
        put(row, 1, '─' * (w_panel - 2), dim)
        row += 1

        # Player name + class
        put(row, 1, f'{player.name[:14]:<14}', bold)
        row += 1
        cls_str = f'{player.class_name} Lv.{player.level}'
        put(row, 1, cls_str, norm)
        row += 1
        put(row, 1, '─' * (w_panel - 2), dim)
        row += 1

        # HP bar
        hp_frac  = player.hp_fraction()
        hp_color = (C_HP_HI if hp_frac > 0.5 else
                    C_HP_MID if hp_frac > 0.25 else C_HP_LO)
        hp_attr  = curses.color_pair(hp_color) | curses.A_BOLD
        put(row, 1, f'HP {player.hp:>3}/{player.max_hp:<3}', hp_attr)
        row += 1
        bar_w = w_panel - 4
        filled = int(hp_frac * bar_w)
        bar = '█' * filled + '░' * (bar_w - filled)
        put(row, 1, f'[{bar}]', curses.color_pair(hp_color))
        row += 1

        # XP bar
        xp_frac = player.xp_fraction()
        xp_bar_w = w_panel - 4
        xp_filled = int(xp_frac * xp_bar_w)
        xp_bar = '▓' * xp_filled + '░' * (xp_bar_w - xp_filled)
        put(row, 1, f'[{xp_bar}]', curses.color_pair(C_XP))
        row += 1
        put(row, 1, f'XP {player.xp}/{player.xp_to_next}', dim)
        row += 1
        put(row, 1, '─' * (w_panel - 2), dim)
        row += 1

        # Stats
        put(row, 1, f'ATK: {player.atk:<4} DEF: {player.def_:<4}', norm)
        row += 1
        put(row, 1, f'GOLD: {player.gold}', curses.color_pair(C_GOLD))
        row += 1
        put(row, 1, '─' * (w_panel - 2), dim)
        row += 1

        # Floor
        floor_bar_w = w_panel - 4
        floor_frac = player.floor / 10
        f_filled = int(floor_frac * floor_bar_w)
        f_bar = '▪' * f_filled + '·' * (floor_bar_w - f_filled)
        put(row, 1, f'Floor {player.floor:>2}/10', warn)
        row += 1
        put(row, 1, f'[{f_bar}]', dim)
        row += 1

        if player.has_amulet:
            put(row, 1, '** HAS AMULET **', curses.color_pair(C_AMULET) | curses.A_BOLD)
            row += 1

        put(row, 1, '─' * (w_panel - 2), dim)
        row += 1

        # Equipment
        put(row, 1, 'WEAPON:', bold)
        row += 1
        wname = player.weapon.name[:w_panel-3] if player.weapon else '(none)'
        put(row, 1, f' {wname}', curses.color_pair(C_WEAPON))
        row += 1
        if player.weapon:
            put(row, 1, f' +{player.weapon.atk_bonus} ATK', dim)
            row += 1

        put(row, 1, 'ARMOR:', bold)
        row += 1
        aname = player.armor.name[:w_panel-3] if player.armor else '(none)'
        put(row, 1, f' {aname}', curses.color_pair(C_ARMOR))
        row += 1
        if player.armor:
            put(row, 1, f' +{player.armor.def_bonus} DEF', dim)
            row += 1

        put(row, 1, '─' * (w_panel - 2), dim)
        row += 1

        # Inventory summary
        put(row, 1, f'BAG [{len(player.inventory)}/{20}]', bold)
        row += 1
        for i, item in enumerate(player.inventory[:5]):
            put(row, 1, f' {i+1}. {item.name[:w_panel-5]}', dim)
            row += 1
        if len(player.inventory) > 5:
            put(row, 1, f' ...+{len(player.inventory)-5} more', dim)
            row += 1

    def _draw_messages(self, messages: list[str], msg_y: int, w: int, h: int):
        # Separator line
        self._safe_addstr(msg_y, 0, '─' * (w - STATS_W - 1), curses.color_pair(C_DIM))

        # Last MSG_H-1 messages
        recent = messages[-(MSG_H - 1):]
        for i, msg in enumerate(recent):
            row = msg_y + 1 + i
            if row >= h:
                break
            # Color based on content keywords
            attr = curses.color_pair(C_UI)
            lower = msg.lower()
            if any(k in lower for k in ('die', 'dead', 'kill', 'slain', 'perish')):
                attr = curses.color_pair(C_DANGER) | curses.A_BOLD
            elif any(k in lower for k in ('level', 'gain', 'found', 'pick', 'equip')):
                attr = curses.color_pair(C_SUCCESS)
            elif any(k in lower for k in ('take', 'hit', 'damage', 'attack', 'wound')):
                attr = curses.color_pair(C_WARNING)
            elif any(k in lower for k in ('amulet', 'escape', 'victory')):
                attr = curses.color_pair(C_AMULET) | curses.A_BOLD
            self._safe_addstr(row, 1, msg[:w - STATS_W - 3], attr)

    def _draw_controls_hint(self, h: int, stats_x: int):
        controls = "[hjkl/arrows] Move  [g] Pickup  [i] Inventory  [>/<] Stairs  [q] Quit"
        self._safe_addstr(h - 1, 1, controls[:stats_x - 2], curses.color_pair(C_DIM))

    # ------------------------------------------------------------------
    # Inventory screen
    # ------------------------------------------------------------------

    def render_inventory(self, player, selection: int, mode: str):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        title = "=== INVENTORY ==="
        self._safe_addstr(1, (w - len(title)) // 2, title,
                          curses.color_pair(C_TITLE) | curses.A_BOLD)

        # Equipped
        self._safe_addstr(3, 2, "EQUIPPED:", curses.color_pair(C_UI_BOLD) | curses.A_BOLD)
        weap_str = player.weapon.display_name() if player.weapon else '(none)'
        armo_str = player.armor.display_name()  if player.armor  else '(none)'
        self._safe_addstr(4, 4, f'Weapon: {weap_str}', curses.color_pair(C_WEAPON))
        self._safe_addstr(5, 4, f'Armor:  {armo_str}', curses.color_pair(C_ARMOR))

        # Inventory list
        self._safe_addstr(7, 2, "BACKPACK:", curses.color_pair(C_UI_BOLD) | curses.A_BOLD)
        if not player.inventory:
            self._safe_addstr(8, 4, "(empty)", curses.color_pair(C_DIM))
        else:
            for i, item in enumerate(player.inventory):
                sel = (i == selection)
                color_id = {
                    'weapon':     C_WEAPON,
                    'armor':      C_ARMOR,
                    'consumable': C_POTION if item.char == '!' else C_SCROLL,
                }.get(item.kind, C_UI)
                attr = (curses.color_pair(color_id) | curses.A_BOLD | curses.A_REVERSE
                        if sel else curses.color_pair(color_id))
                marker = '>' if sel else ' '
                line = f' {marker} {i+1:>2}. {item.display_name()}'
                self._safe_addstr(8 + i, 4, line[:w - 8], attr)

        # Controls
        if mode == 'normal':
            hint_lines = [
                "↑↓ to select  |  [e/Enter] equip/use  |  [d] drop  |  [Esc/i] close",
                "Weapons and armor: press [e] to equip.",
                "Consumables: press [e/Enter] to use (offensive scrolls target nearest enemy).",
            ]
        else:
            hint_lines = ["Select action..."]

        base = h - len(hint_lines) - 2
        for i, hl in enumerate(hint_lines):
            self._safe_addstr(base + i, 2, hl[:w - 4], curses.color_pair(C_DIM))

        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Level up screen
    # ------------------------------------------------------------------

    def render_level_up(self, player, gains: dict):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        lines = [
            "╔══════════════════════════════╗",
            "║       LEVEL  UP!             ║",
            "╠══════════════════════════════╣",
            f"║  You are now level {player.level:<2}         ║",
            "║                              ║",
            f"║  + {gains.get('hp', 0):>2} Max HP                ║",
            f"║  + {gains.get('atk', 0):>2} Attack               ║",
            f"║  + {gains.get('def', 0):>2} Defense              ║",
            "║                              ║",
            "╚══════════════════════════════╝",
        ]
        sy = (h - len(lines)) // 2
        sx = (w - len(lines[0])) // 2
        for i, line in enumerate(lines):
            self._safe_addstr(sy + i, sx, line,
                              curses.color_pair(C_TITLE) | curses.A_BOLD)

        hint = "Press any key to continue..."
        self._safe_addstr(sy + len(lines) + 1, (w - len(hint)) // 2, hint,
                          curses.color_pair(C_DIM))
        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Game over / victory screens
    # ------------------------------------------------------------------

    def render_game_over(self, player, floor: int, reason: str):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        skull = [
            r"    ___   ",
            r"   /   \  ",
            r"  | x x | ",
            r"   \___/  ",
            r"  /|___|\ ",
        ]
        lines = [
            "",
            *skull,
            "",
            "    YOU HAVE DIED    ",
            "",
            f"  {player.name} the {player.class_name}",
            f"  reached floor {floor} of 10",
            f"  Level {player.level} — {player.xp} XP — {player.gold} gold",
            "",
            f"  Cause: {reason}",
            "",
        ]
        sy = max(1, (h - len(lines)) // 2)
        sx = max(1, (w - 22) // 2)
        for i, line in enumerate(lines):
            attr = curses.color_pair(C_DANGER) | curses.A_BOLD
            self._safe_addstr(sy + i, sx, line, attr)

        hint = "Press any key to return to title..."
        self._safe_addstr(sy + len(lines) + 1, (w - len(hint)) // 2, hint,
                          curses.color_pair(C_DIM))
        self.stdscr.refresh()

    def render_victory(self, player):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        lines = [
            "  ╔══════════════════════════════════╗  ",
            "  ║                                  ║  ",
            "  ║    ★  V I C T O R Y  ★           ║  ",
            "  ║                                  ║  ",
            "  ╠══════════════════════════════════╣  ",
            f"  ║  {player.name[:18]:<18} escaped!  ║  ",
            f"  ║  Level {player.level:<4}  XP: {player.xp:<8}     ║  ",
            f"  ║  Gold collected: {player.gold:<5}            ║  ",
            "  ║                                  ║  ",
            "  ║  The Amulet of Depths is yours.  ║  ",
            "  ║  The surface world is saved.     ║  ",
            "  ║                                  ║  ",
            "  ╚══════════════════════════════════╝  ",
        ]
        sy = (h - len(lines)) // 2
        sx = max(0, (w - len(lines[0])) // 2)
        for i, line in enumerate(lines):
            self._safe_addstr(sy + i, sx, line,
                              curses.color_pair(C_AMULET) | curses.A_BOLD)

        hint = "Press any key..."
        self._safe_addstr(sy + len(lines) + 1, (w - len(hint)) // 2, hint,
                          curses.color_pair(C_DIM))
        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Too-small terminal warning
    # ------------------------------------------------------------------

    def render_too_small(self):
        self.stdscr.erase()
        try:
            self.stdscr.addstr(0, 0, f"Terminal too small! Need at least {MIN_W}x{MIN_H}.")
        except curses.error:
            pass
        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Confirm dialog
    # ------------------------------------------------------------------

    def render_confirm(self, msg: str, y_sel: bool):
        h, w = self.stdscr.getmaxyx()
        box_w = max(len(msg) + 4, 30)
        box_h = 5
        sx = (w - box_w) // 2
        sy = (h - box_h) // 2

        for dy in range(box_h):
            self._safe_addstr(sy + dy, sx, ' ' * box_w, curses.color_pair(C_UI) | curses.A_REVERSE)

        self._safe_addstr(sy + 1, sx + 2, msg, curses.color_pair(C_WARNING) | curses.A_BOLD)
        yes_attr = (curses.color_pair(C_DANGER) | curses.A_BOLD | curses.A_REVERSE
                    if y_sel else curses.color_pair(C_UI))
        no_attr  = (curses.color_pair(C_SUCCESS) | curses.A_BOLD | curses.A_REVERSE
                    if not y_sel else curses.color_pair(C_UI))
        self._safe_addstr(sy + 3, sx + box_w // 4, ' Yes ', yes_attr)
        self._safe_addstr(sy + 3, sx + box_w * 3 // 4 - 4, ' No  ', no_attr)
        self.stdscr.refresh()
