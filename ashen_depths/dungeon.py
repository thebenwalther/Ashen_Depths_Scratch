"""Procedural dungeon generation, FOV, and pathfinding."""
from __future__ import annotations
import random
import math
from typing import Optional
from .constants import (DUNGEON_W, DUNGEON_H, MAX_ROOMS, MIN_ROOM_W, MAX_ROOM_W,
                         MIN_ROOM_H, MAX_ROOM_H, T_WALL, T_FLOOR, T_STAIRS_DOWN,
                         T_STAIRS_UP, NUM_FLOORS, MIN_MONSTERS, MAX_MONSTERS,
                         MIN_ITEMS, MAX_ITEMS, MONSTER_SIGHT)
from .data import MONSTER_TEMPLATES
from .entities import Item, Monster, Player


# ---------------------------------------------------------------------------
# Tile
# ---------------------------------------------------------------------------

class Tile:
    __slots__ = ('type', 'visible', 'explored')

    def __init__(self, tile_type: int = T_WALL):
        self.type     = tile_type
        self.visible  = False   # currently in player's FOV
        self.explored = False   # has been seen before

    @property
    def walkable(self) -> bool:
        return self.type != T_WALL

    @property
    def blocks_sight(self) -> bool:
        return self.type == T_WALL


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------

class Room:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w - 1, y + h - 1

    @property
    def cx(self) -> int:
        return (self.x1 + self.x2) // 2

    @property
    def cy(self) -> int:
        return (self.y1 + self.y2) // 2

    def center(self) -> tuple[int, int]:
        return self.cx, self.cy

    def intersects(self, other: Room, margin: int = 1) -> bool:
        return (self.x1 - margin <= other.x2 and self.x2 + margin >= other.x1 and
                self.y1 - margin <= other.y2 and self.y2 + margin >= other.y1)

    def random_point(self) -> tuple[int, int]:
        return (random.randint(self.x1 + 1, self.x2 - 1),
                random.randint(self.y1 + 1, self.y2 - 1))


# ---------------------------------------------------------------------------
# DungeonFloor
# ---------------------------------------------------------------------------

class DungeonFloor:
    def __init__(self, floor: int, player: Player):
        self.floor   = floor
        self.width   = DUNGEON_W
        self.height  = DUNGEON_H
        self.tiles: list[list[Tile]] = []
        self.rooms:    list[Room]    = []
        self.monsters: list[Monster] = []
        self.items:    list[Item]    = []
        self.amulet_pos: Optional[tuple[int, int]] = None

        self._generate(player)

    # --- Map access helpers ---

    def tile(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[y][x].walkable

    def monster_at(self, x: int, y: int) -> Optional[Monster]:
        for m in self.monsters:
            if m.alive and m.x == x and m.y == y:
                return m
        return None

    def item_at(self, x: int, y: int) -> Optional[Item]:
        for it in self.items:
            if it.x == x and it.y == y:
                return it
        return None

    def remove_item(self, item: Item):
        if item in self.items:
            self.items.remove(item)

    # --- Generation ---

    def _generate(self, player: Player):
        # Initialize all walls
        self.tiles = [[Tile(T_WALL) for _ in range(self.width)]
                      for _ in range(self.height)]

        rooms: list[Room] = []
        attempts = 0

        while len(rooms) < MAX_ROOMS and attempts < MAX_ROOMS * 5:
            attempts += 1
            w = random.randint(MIN_ROOM_W, MAX_ROOM_W)
            h = random.randint(MIN_ROOM_H, MAX_ROOM_H)
            x = random.randint(1, self.width  - w - 2)
            y = random.randint(1, self.height - h - 2)
            room = Room(x, y, w, h)

            if any(room.intersects(r) for r in rooms):
                continue

            self._carve_room(room)
            if rooms:
                self._connect_rooms(rooms[-1], room)
            rooms.append(room)

        self.rooms = rooms

        # Place stairs (always in different rooms if possible)
        if rooms:
            last_room = rooms[-1]
            sx, sy = last_room.center()
            self.tiles[sy][sx].type = T_STAIRS_DOWN

            if self.floor > 1:
                # Stairs up go in first room; if only 1 room use a different spot
                first_room = rooms[0]
                if len(rooms) > 1:
                    ux, uy = first_room.center()
                else:
                    ux, uy = first_room.random_point()
                    # Make sure it's not on the down stairs
                    for _ in range(10):
                        if (ux, uy) != (sx, sy):
                            break
                        ux, uy = first_room.random_point()
                self.tiles[uy][ux].type = T_STAIRS_UP

        # Place amulet on floor 10 (in a separate room near the boss)
        if self.floor == NUM_FLOORS and len(rooms) >= 2:
            ax, ay = rooms[-1].random_point()
            self.amulet_pos = (ax, ay)

        # Place player in first room
        px, py = rooms[0].center() if rooms else (2, 2)
        # Don't place on stairs
        if self.tiles[py][px].type == T_STAIRS_UP:
            px, py = rooms[0].random_point() if rooms else (2, 2)
        player.x, player.y = px, py

        # Populate monsters and items
        self._populate(player)

    def _carve_room(self, room: Room):
        for y in range(room.y1, room.y2 + 1):
            for x in range(room.x1, room.x2 + 1):
                self.tiles[y][x].type = T_FLOOR

    def _connect_rooms(self, a: Room, b: Room):
        ax, ay = a.center()
        bx, by = b.center()
        # Randomly choose L-shape direction
        if random.random() < 0.5:
            self._hcorridor(ax, bx, ay)
            self._vcorridor(ay, by, bx)
        else:
            self._vcorridor(ay, by, ax)
            self._hcorridor(ax, bx, by)

    def _hcorridor(self, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if self.in_bounds(x, y):
                self.tiles[y][x].type = T_FLOOR

    def _vcorridor(self, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if self.in_bounds(x, y):
                self.tiles[y][x].type = T_FLOOR

    def _populate(self, player: Player):
        num_monsters = random.randint(MIN_MONSTERS, MAX_MONSTERS)
        num_items    = random.randint(MIN_ITEMS, MAX_ITEMS)

        # Eligible monster templates for this floor
        eligible = [t for t in MONSTER_TEMPLATES
                    if t['floors'][0] <= self.floor <= t['floors'][1]
                    and not t.get('is_boss', False)]

        # Place boss on floor 10
        if self.floor == NUM_FLOORS:
            boss_tmpl = next((t for t in MONSTER_TEMPLATES if t.get('is_boss')), None)
            if boss_tmpl and len(self.rooms) >= 2:
                bx, by = self.rooms[-1].center()
                self.monsters.append(Monster(boss_tmpl, bx, by, self.floor))

        # Place regular monsters (skip room 0 where player starts)
        placed = 0
        for _ in range(num_monsters * 5):
            if placed >= num_monsters or not eligible:
                break
            room = random.choice(self.rooms[1:]) if len(self.rooms) > 1 else self.rooms[0]
            mx, my = room.random_point()
            if self.monster_at(mx, my) or (mx == player.x and my == player.y):
                continue
            tmpl = random.choice(eligible)
            self.monsters.append(Monster(tmpl, mx, my, self.floor))
            placed += 1

        # Place items (any room, but not on player start)
        placed = 0
        for _ in range(num_items * 5):
            if placed >= num_items:
                break
            room = random.choice(self.rooms)
            ix, iy = room.random_point()
            if (self.item_at(ix, iy) or
                    (ix == player.x and iy == player.y) or
                    self.tiles[iy][ix].type in (T_STAIRS_DOWN, T_STAIRS_UP)):
                continue
            item = Item.random_for_floor(self.floor, ix, iy)
            self.items.append(item)
            placed += 1

    # --- Field of View ---

    def compute_fov(self, px: int, py: int, radius: int):
        """Shadowcasting FOV. Marks tiles visible/explored."""
        # Reset visibility
        for row in self.tiles:
            for t in row:
                t.visible = False

        # Always mark player tile
        if self.in_bounds(px, py):
            self.tiles[py][px].visible  = True
            self.tiles[py][px].explored = True

        # Cast rays at many angles
        for angle_deg in range(0, 360):
            rad = math.radians(angle_deg)
            dx  = math.cos(rad)
            dy  = math.sin(rad)
            rx, ry = float(px), float(py)
            for _ in range(radius):
                rx += dx
                ry += dy
                ix, iy = int(round(rx)), int(round(ry))
                if not self.in_bounds(ix, iy):
                    break
                t = self.tiles[iy][ix]
                t.visible  = True
                t.explored = True
                if t.blocks_sight:
                    break

    # --- Monster AI move ---

    def move_monster(self, monster: Monster, player: Player) -> bool:
        """Move monster toward player if in sight. Return True if adjacent (will attack)."""
        if not monster.alive:
            return False
        if monster.stunned > 0:
            monster.stunned -= 1
            return False

        dx = player.x - monster.x
        dy = player.y - monster.y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist > MONSTER_SIGHT:
            return False

        if dist <= 1.5:
            return True  # adjacent, engine should trigger attack

        # Move one step toward player
        mx = 0 if dx == 0 else (1 if dx > 0 else -1)
        my = 0 if dy == 0 else (1 if dy > 0 else -1)

        # Try diagonal, then cardinal, then random
        candidates = []
        if mx != 0 and my != 0:
            candidates.append((mx, my))
        if mx != 0:
            candidates.append((mx, 0))
        if my != 0:
            candidates.append((0, my))

        random.shuffle(candidates)
        for cmx, cmy in candidates:
            nx, ny = monster.x + cmx, monster.y + cmy
            if (self.walkable(nx, ny) and
                    not self.monster_at(nx, ny) and
                    not (nx == player.x and ny == player.y)):
                monster.x, monster.y = nx, ny
                return False

        return False

    def teleport_player(self, player: Player):
        """Move player to a random floor tile."""
        floor_tiles = [(x, y)
                       for y in range(self.height)
                       for x in range(self.width)
                       if self.tiles[y][x].type == T_FLOOR
                       and not self.monster_at(x, y)
                       and abs(x - player.x) > 3]
        if floor_tiles:
            player.x, player.y = random.choice(floor_tiles)
