"""Entity classes: Item, Monster, Player."""
from __future__ import annotations
import random
from .constants import MAX_INVENTORY, XP_NEEDED, NUM_FLOORS
from .data import WEAPON_TEMPLATES, ARMOR_TEMPLATES, CONSUMABLE_TEMPLATES, CLASSES


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

class Item:
    def __init__(self, name: str, char: str, kind: str, **kwargs):
        self.name = name
        self.char = char
        self.kind = kind          # 'weapon' | 'armor' | 'consumable'
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        # weapon/armor
        self.atk_bonus = kwargs.get('atk_bonus', 0)
        self.def_bonus = kwargs.get('def_bonus', 0)
        self.value     = kwargs.get('value', 0)
        # consumable
        self.effect = kwargs.get('effect', '')
        self.power  = kwargs.get('power', 0)

    def __repr__(self):
        return f'<Item {self.name}>'

    @staticmethod
    def from_template(tmpl: dict, x=0, y=0) -> Item:
        kind = ('weapon' if 'atk_bonus' in tmpl
                else 'armor' if 'def_bonus' in tmpl
                else 'consumable')
        skip = {'name', 'char', 'floors'}
        extra = {k: v for k, v in tmpl.items() if k not in skip}
        return Item(tmpl['name'], tmpl['char'], kind, x=x, y=y, **extra)

    @staticmethod
    def random_for_floor(floor: int, x=0, y=0) -> Item:
        """Pick a random item appropriate for this floor."""
        candidates = []
        for t in WEAPON_TEMPLATES:
            if t['floors'][0] <= floor <= t['floors'][1]:
                candidates.append(('weapon', t))
        for t in ARMOR_TEMPLATES:
            if t['floors'][0] <= floor <= t['floors'][1]:
                candidates.append(('armor', t))
        # consumables appear on any floor
        for t in CONSUMABLE_TEMPLATES:
            candidates.append(('consumable', t))

        if not candidates:
            # fallback
            tmpl = random.choice(CONSUMABLE_TEMPLATES)
            return Item.from_template(tmpl, x, y)

        _, tmpl = random.choice(candidates)
        return Item.from_template(tmpl, x, y)

    @staticmethod
    def make(name: str, x=0, y=0) -> Item:
        """Create an item by name from all templates."""
        for t in WEAPON_TEMPLATES + ARMOR_TEMPLATES + CONSUMABLE_TEMPLATES:
            if t['name'] == name:
                return Item.from_template(t, x, y)
        raise ValueError(f'Unknown item: {name}')

    def display_name(self) -> str:
        if self.kind == 'weapon':
            return f'{self.name} (+{self.atk_bonus} ATK)'
        if self.kind == 'armor':
            return f'{self.name} (+{self.def_bonus} DEF)'
        return self.name


# ---------------------------------------------------------------------------
# Monster
# ---------------------------------------------------------------------------

class Monster:
    def __init__(self, tmpl: dict, x: int, y: int, floor: int):
        self.id      = tmpl['id']
        self.name    = tmpl['name']
        self.char    = tmpl['char']
        self.tier    = tmpl['tier']
        self.desc    = tmpl.get('desc', '')
        self.is_boss = tmpl.get('is_boss', False)
        self.x, self.y = x, y

        self.max_hp = random.randint(*tmpl['hp'])
        self.hp     = self.max_hp
        self.atk    = random.randint(*tmpl['atk'])
        self.def_   = random.randint(*tmpl['def_'])
        self.xp     = tmpl['xp']
        self.gold   = random.randint(*tmpl['gold'])

        self.stunned  = 0   # turns remaining of stun
        self.asleep   = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply damage, return actual damage dealt."""
        actual = max(1, amount - self.def_)
        self.hp = max(0, self.hp - actual)
        return actual

    def attack_power(self) -> int:
        return max(1, self.atk + random.randint(-2, 2))


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class Player:
    def __init__(self, name: str, class_name: str):
        self.name       = name
        self.class_name = class_name
        cls = CLASSES[class_name]

        self.max_hp  = cls['hp']
        self.hp      = cls['hp']
        self.base_atk = cls['atk']
        self.base_def = cls['def_']
        self.level   = 1
        self.xp      = 0
        self.gold    = 0
        self.floor   = 1
        self.has_amulet = False

        self.x = 0
        self.y = 0

        self.weapon: Item | None = Item.make(cls['start_weapon'])
        self.armor:  Item | None = Item.make(cls['start_armor'])
        self.inventory: list[Item] = []

        # Mage bonus scrolls
        if 'bonus_scrolls' in cls:
            for _ in range(cls['bonus_scrolls']):
                from .data import CONSUMABLE_TEMPLATES
                scrolls = [t for t in CONSUMABLE_TEMPLATES if t['char'] == '?']
                if scrolls:
                    self.inventory.append(Item.from_template(random.choice(scrolls)))

        # Stat bonuses from items (applied on equip)
        self.strength_bonus = 0   # from elixirs

    # --- Computed stats ---

    @property
    def atk(self) -> int:
        w = self.weapon.atk_bonus if self.weapon else 0
        return self.base_atk + w + self.strength_bonus

    @property
    def def_(self) -> int:
        a = self.armor.def_bonus if self.armor else 0
        return self.base_def + a

    # --- XP / leveling ---

    @property
    def xp_to_next(self) -> int:
        lvl = min(self.level, len(XP_NEEDED) - 2)
        return XP_NEEDED[lvl + 1]

    def gain_xp(self, amount: int) -> bool:
        """Add XP, return True if leveled up."""
        self.xp += amount
        if self.level < len(XP_NEEDED) - 2 and self.xp >= self.xp_to_next:
            return True
        return False

    def level_up(self) -> dict:
        """Perform level up, return dict of stat gains."""
        self.level += 1
        gains = {}
        if self.class_name == 'Warrior':
            hp_gain = random.randint(7, 12)
            atk_gain = random.randint(1, 2)
            def_gain = random.randint(1, 2)
        elif self.class_name == 'Rogue':
            hp_gain = random.randint(5, 9)
            atk_gain = random.randint(2, 3)
            def_gain = random.randint(0, 1)
        else:  # Mage
            hp_gain = random.randint(4, 7)
            atk_gain = random.randint(1, 3)
            def_gain = random.randint(0, 1)

        self.max_hp   += hp_gain
        self.hp        = min(self.hp + hp_gain // 2, self.max_hp)
        self.base_atk += atk_gain
        self.base_def += def_gain
        gains['hp']   = hp_gain
        gains['atk']  = atk_gain
        gains['def']  = def_gain
        return gains

    # --- Combat ---

    def attack_roll(self) -> int:
        variance = max(1, self.atk // 5)
        return self.atk + random.randint(-variance, variance)

    def take_damage(self, raw: int) -> int:
        """Apply incoming damage after defense, return actual damage."""
        actual = max(1, raw - self.def_ + random.randint(-1, 1))
        self.hp = max(0, self.hp - actual)
        return actual

    @property
    def alive(self) -> bool:
        return self.hp > 0

    # --- Inventory ---

    def pick_up(self, item: Item) -> bool:
        if len(self.inventory) >= MAX_INVENTORY:
            return False
        self.inventory.append(item)
        return True

    def equip(self, item: Item) -> Item | None:
        """Equip item, return previously equipped item (or None)."""
        if item.kind == 'weapon':
            old = self.weapon
            self.weapon = item
            if item in self.inventory:
                self.inventory.remove(item)
            if old:
                self.inventory.append(old)
            return old
        elif item.kind == 'armor':
            old = self.armor
            self.armor = item
            if item in self.inventory:
                self.inventory.remove(item)
            if old:
                self.inventory.append(old)
            return old
        return None

    def use_consumable(self, item: Item, target: Monster | None = None) -> list[str]:
        """Use a consumable, return list of message strings."""
        msgs = []
        if item not in self.inventory:
            return msgs
        self.inventory.remove(item)

        if item.effect == 'heal':
            healed = min(item.power, self.max_hp - self.hp)
            self.hp += healed
            msgs.append(f'You drink the {item.name} and restore {healed} HP.')
        elif item.effect == 'fire':
            if target:
                dmg = item.power + random.randint(0, 15)
                target.hp = max(0, target.hp - dmg)
                msgs.append(f'Fire engulfs the {target.name} for {dmg} damage!')
            else:
                msgs.append('No target. The scroll fizzles.')
        elif item.effect == 'lightning':
            if target:
                dmg = item.power + random.randint(0, 20)
                target.hp = max(0, target.hp - dmg)
                msgs.append(f'Lightning strikes the {target.name} for {dmg} damage!')
            else:
                msgs.append('No target. The scroll fizzles.')
        elif item.effect == 'freeze':
            if target:
                target.stunned = 3
                msgs.append(f'The {target.name} is frozen solid!')
            else:
                msgs.append('No target. The scroll fizzles.')
        elif item.effect == 'teleport':
            msgs.append('TELEPORT')  # engine handles actual repositioning
        elif item.effect == 'strength':
            self.strength_bonus += item.power
            msgs.append(f'Your muscles surge with power! ATK +{item.power}.')

        return msgs

    def hp_fraction(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0

    def xp_fraction(self) -> float:
        if self.level >= len(XP_NEEDED) - 2:
            return 1.0
        prev = XP_NEEDED[self.level]
        needed = XP_NEEDED[self.level + 1]
        if needed == prev:
            return 1.0
        return (self.xp - prev) / (needed - prev)
