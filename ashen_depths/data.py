"""Game data tables: monsters, weapons, armors, consumables."""

# Each monster: name, char, floors (min,max), hp, atk, def_, xp, gold, tier
# tier: 'weak' | 'med' | 'strong' | 'boss'
MONSTER_TEMPLATES = [
    # --- Early floors (1-4) ---
    dict(id='ash_rat',      name='Ash Rat',        char='r', floors=(1,4),
         hp=(8,14),   atk=(2,4),   def_=(0,1),  xp=5,   gold=(1,3),   tier='weak',
         desc='A mangy rodent coated in grey ash.'),
    dict(id='cinder_bat',   name='Cinder Bat',     char='b', floors=(1,5),
         hp=(10,18),  atk=(3,6),   def_=(0,2),  xp=8,   gold=(1,4),   tier='weak',
         desc='A bat whose wings smolder at the tips.'),
    dict(id='skeleton',     name='Skeleton',       char='s', floors=(2,6),
         hp=(15,25),  atk=(4,8),   def_=(1,3),  xp=12,  gold=(2,6),   tier='weak',
         desc='Animated bones that clatter as they walk.'),
    dict(id='cave_spider',  name='Cave Spider',    char='x', floors=(1,4),
         hp=(12,20),  atk=(3,7),   def_=(0,2),  xp=10,  gold=(1,5),   tier='weak',
         desc='A bloated spider with glowing red eyes.'),

    # --- Mid floors (3-7) ---
    dict(id='ember_hound',  name='Ember Hound',    char='h', floors=(3,7),
         hp=(22,38),  atk=(7,12),  def_=(2,4),  xp=20,  gold=(4,8),   tier='med',
         desc='A canine wreathed in dying embers.'),
    dict(id='shadow_stalker', name='Shadow Stalker', char='S', floors=(4,8),
         hp=(28,45),  atk=(9,15),  def_=(2,5),  xp=28,  gold=(5,10),  tier='med',
         desc='A shade that hunts by scent alone.'),
    dict(id='bone_knight',  name='Bone Knight',    char='K', floors=(5,8),
         hp=(38,58),  atk=(8,14),  def_=(5,9),  xp=35,  gold=(6,12),  tier='med',
         desc='Armored skeleton with a rusted sword.'),
    dict(id='ashen_ghost',  name='Ashen Ghost',    char='g', floors=(4,7),
         hp=(20,35),  atk=(10,16), def_=(1,3),  xp=25,  gold=(3,8),   tier='med',
         desc='A translucent spirit of ash and regret.'),

    # --- Deep floors (6-10) ---
    dict(id='infernal_wraith', name='Infernal Wraith', char='W', floors=(6,10),
         hp=(45,70),  atk=(13,22), def_=(3,7),  xp=50,  gold=(7,15),  tier='strong',
         desc='A spirit of pure infernal fury.'),
    dict(id='lava_golem',   name='Lava Golem',     char='G', floors=(7,10),
         hp=(60,85),  atk=(15,24), def_=(7,13), xp=65,  gold=(9,18),  tier='strong',
         desc='A hulking mass of cooled magma, still burning within.'),
    dict(id='ashen_drake',  name='Ashen Drake',    char='D', floors=(8,10),
         hp=(65,95),  atk=(18,28), def_=(6,11), xp=85,  gold=(12,22), tier='strong',
         desc='A lesser dragon born from volcanic ash.'),
    dict(id='crypt_lich',   name='Crypt Lich',     char='L', floors=(7,10),
         hp=(50,75),  atk=(16,26), def_=(4,8),  xp=75,  gold=(10,20), tier='strong',
         desc='An ancient sorcerer bound to undeath.'),

    # --- Floor 10 Boss ---
    dict(id='ashen_lord',   name='The Ashen Lord',  char='A', floors=(10,10),
         hp=(200,200), atk=(22,36), def_=(12,16), xp=600, gold=(80,120), tier='boss',
         desc='The ancient tyrant of the Depths. He guards the Amulet.',
         is_boss=True),
]

# Weapons: name, char, atk_bonus, value, floors (min,max)
WEAPON_TEMPLATES = [
    dict(name='Rusty Dagger',        char='/', atk_bonus=2,  value=5,   floors=(1,3)),
    dict(name='Short Sword',         char='/', atk_bonus=5,  value=15,  floors=(1,5)),
    dict(name='Iron Axe',            char='/', atk_bonus=7,  value=25,  floors=(2,6)),
    dict(name='Bone Blade',          char='/', atk_bonus=9,  value=40,  floors=(3,7)),
    dict(name='Ember Sword',         char='/', atk_bonus=12, value=60,  floors=(5,8)),
    dict(name='Shadow Edge',         char='/', atk_bonus=15, value=85,  floors=(6,9)),
    dict(name='Infernal Blade',      char='/', atk_bonus=19, value=130, floors=(8,10)),
    dict(name='Obsidian Greatsword', char='/', atk_bonus=24, value=220, floors=(9,10)),
]

# Armors: name, char, def_bonus, value, floors (min,max)
ARMOR_TEMPLATES = [
    dict(name='Tattered Robe',     char=']', def_bonus=1,  value=5,   floors=(1,3)),
    dict(name='Leather Armor',     char=']', def_bonus=3,  value=15,  floors=(1,5)),
    dict(name='Chain Mail',        char=']', def_bonus=6,  value=30,  floors=(3,7)),
    dict(name='Ash Knight Armor',  char=']', def_bonus=9,  value=55,  floors=(5,8)),
    dict(name='Infernal Plate',    char=']', def_bonus=13, value=100, floors=(7,10)),
    dict(name='Shadowweave Cloak', char=']', def_bonus=16, value=160, floors=(9,10)),
]

# Consumables: name, char, effect, power, value
# effect: 'heal' | 'fire' | 'lightning' | 'freeze' | 'teleport' | 'strength'
CONSUMABLE_TEMPLATES = [
    dict(name='Minor Health Potion',  char='!', effect='heal',      power=20,  value=10),
    dict(name='Health Potion',        char='!', effect='heal',      power=45,  value=25),
    dict(name='Greater Health Potion',char='!', effect='heal',      power=90,  value=55),
    dict(name='Scroll of Fire',       char='?', effect='fire',      power=35,  value=20),
    dict(name='Scroll of Lightning',  char='?', effect='lightning', power=55,  value=35),
    dict(name='Scroll of Freeze',     char='?', effect='freeze',    power=0,   value=30),
    dict(name='Scroll of Teleport',   char='?', effect='teleport',  power=0,   value=25),
    dict(name='Elixir of Strength',   char='!', effect='strength',  power=5,   value=80),
]

# Class definitions: name, hp, atk, def_, start_weapon, start_armor, description
CLASSES = {
    'Warrior': dict(
        hp=70, atk=10, def_=8,
        start_weapon='Short Sword',
        start_armor='Leather Armor',
        desc='Resilient fighter. High HP and defense.',
    ),
    'Rogue': dict(
        hp=50, atk=14, def_=5,
        start_weapon='Rusty Dagger',
        start_armor='Tattered Robe',
        desc='Swift and deadly. High attack, lower defense.',
    ),
    'Mage': dict(
        hp=42, atk=8, def_=4,
        start_weapon='Rusty Dagger',
        start_armor='Tattered Robe',
        desc='Wielder of scrolls. Starts with 2 scrolls.',
        bonus_scrolls=2,
    ),
}

# Floor lore/flavor text shown on descent
FLOOR_LORE = [
    "You descend deeper into the Ashen Depths.",
    "The air grows hotter. Ash rains from the ceiling.",
    "Strange runes glow along the walls.",
    "The bones of adventurers litter the floor.",
    "A distant roar echoes through the tunnels.",
    "The darkness here feels alive.",
    "Columns of obsidian line the ancient halls.",
    "You smell sulfur. Something massive lurks nearby.",
    "The walls pulse with infernal heat.",
    "You feel the Amulet's presence. The Ashen Lord awaits.",
]
