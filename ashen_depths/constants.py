# Dungeon dimensions
DUNGEON_W = 60
DUNGEON_H = 30

# Room generation
MAX_ROOMS = 15
MIN_ROOM_W, MAX_ROOM_W = 4, 9
MIN_ROOM_H, MAX_ROOM_H = 3, 7

# Gameplay
NUM_FLOORS = 10
FOV_RADIUS = 8
MONSTER_SIGHT = 7
MAX_INVENTORY = 20
MIN_ITEMS, MAX_ITEMS = 3, 6
MIN_MONSTERS, MAX_MONSTERS = 4, 9

# XP needed to reach level N (index = level, max tracked level = 10)
XP_NEEDED = [0, 0, 60, 160, 320, 540, 840, 1230, 1720, 2320, 3040, 9999]

# Tile types
T_WALL = 0
T_FLOOR = 1
T_STAIRS_DOWN = 2
T_STAIRS_UP = 3

# Color pair IDs
C_PLAYER     = 1
C_MON_WEAK   = 2
C_MON_MED    = 3
C_MON_STRONG = 4
C_MON_BOSS   = 5
C_WEAPON     = 6
C_ARMOR      = 7
C_POTION     = 8
C_GOLD       = 9
C_AMULET     = 10
C_WALL_LIT   = 11
C_FLOOR_LIT  = 12
C_STAIRS     = 13
C_WALL_DIM   = 14
C_FLOOR_DIM  = 15
C_UI         = 16
C_UI_BOLD    = 17
C_HP_HI      = 18
C_HP_MID     = 19
C_HP_LO      = 20
C_XP         = 21
C_TITLE      = 22
C_SUCCESS    = 23
C_WARNING    = 24
C_DANGER     = 25
C_SCROLL     = 26
C_DIM        = 27
C_TRAP       = 28
