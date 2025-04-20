from decimal import Decimal
from enum import Enum
from functools import cache
from typing import Iterable, List, Tuple, Union


class Resonance(Enum):
    NORMAL = "Normal"
    MOONKISSED = "Moonkissed"
    TRIO = "Trio"
    DRACONIC = "Draconic"
    TROPICAL_ROCK = "Tropical Rock"
    SEA_SALT = "Sea Salt"
    RADIANT_CHEESE = "Radiant Cheese"
    FROSTED_CRYSTAL = "Frosted Crystal"
    LIFESPROUTING = "Life-sprouting"
    DESTRUCTIVE = "Destructive"
    FRAGRANT = "Fragrant"
    IRIS_GEM = "Iris Gem"
    DECEITFUL = "Deceitful"
    TRUTHFUL = "Truthful"
    SACRED_VOW = "Sacred Vow"


class Type(Enum):
    # in-game substats
    DMGRES = "DMG Resist"
    ATK = "ATK"
    CD = "Cooldown"
    ATKSPD = "ATK SPD"
    CRIT = "CRIT%"
    HP = "HP"
    BUFF = "Amplify Buff"
    DEF = "DEF"
    BUFFRES = "Debuff Resist"
    CRITRES = "CRIT Resist"
    # in-game non-standard substats (biscuit)
    DARK_DMG = "DARK DMG"
    ELEC_DMG = "ELEC DMG"
    FIRE_DMG = "FIRE DMG"
    EARTH_DMG = "EARTH DMG"
    POISON_DMG = "POISON DMG"
    LIGHT_DMG = "LIGHT DMG"
    # in-game attributes
    CRIT_DMG = "CRIT DMG"
    ATK_MULT = "ATK MULT"
    # custom objective functions
    COMBO = "Combo"
    E_DMG = "E[DMG]"
    VITALITY = "Vitality"
    # helpers
    RNG = "RNG"
    NONE = 'None'

ELEMENTAL_DMG = [
    Type.DARK_DMG, 
    Type.ELEC_DMG, 
    Type.FIRE_DMG, 
    Type.EARTH_DMG, 
    Type.POISON_DMG, 
    Type.LIGHT_DMG
]

INFO = {
    Type.DMGRES: {
        "name": "Solid Almond",
        "short": "DRS",
        "medium": "DMGRES",
        "filename": "dmgres",
        "value": Decimal("4.1"),
        "combos": [(2, Decimal("3")), (3, Decimal("7")), (5, Decimal("8")), (6, Decimal("10"))],
        "view_combos": [(2, Decimal("3")), (3, Decimal("7")), (5, Decimal("8")), (6, Decimal("10"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("6"),
    },
    Type.ATK: {
        "name": "Searing Raspberry",
        "short": "ATK",
        "medium": "ATK",
        "filename": "atk",
        "value": Decimal("9"),
        "combos": [(2, Decimal("4")), (3, Decimal("8")), (5, Decimal("10")), (6, Decimal("12"))],
        "view_combos": [(2, Decimal("4")), (3, Decimal("8")), (5, Decimal("10")), (6, Decimal("12"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("3"),
    },
    Type.CD: {
        "name": "Swift Chocolate",
        "short": "CD",
        "medium": "CD",
        "filename": "cd",
        "value": Decimal("3"),
        "combos": [(2, Decimal("2")), (3, Decimal("4")), (5, Decimal("5")), (6, Decimal("6"))],
        "view_combos": [(2, Decimal("2")), (3, Decimal("4")), (5, Decimal("5")), (6, Decimal("6"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("2"),
    },
    Type.ATKSPD: {
        "name": "Bouncy Caramel",
        "short": "SPD",
        "medium": "ATKSPD",
        "filename": "atkspd",
        "value": Decimal("4.1"),
        "combos": [(2, Decimal("7")), (3, Decimal("8")), (5, Decimal("10")), (6, Decimal("12"))],
        "view_combos": [(2, Decimal("7")), (3, Decimal("8")), (5, Decimal("10")), (6, Decimal("12"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("3"),
    },
    Type.CRIT: {
        "name": "Juicy Apple Jelly",
        "short": "CRT",
        "medium": "CRIT%",
        "filename": "crit",
        "value": Decimal("9"),
        "combos": [(2, Decimal("4")), (3, Decimal("6")), (5, Decimal("8")), (6, Decimal("10"))],
        "view_combos": [(2, Decimal("4")), (3, Decimal("6")), (5, Decimal("8")), (6, Decimal("10"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("3"),
    },
    Type.HP: {
        "name": "Healthy Peanut",
        "short": "HP",
        "medium": "HP",
        "filename": "hp",
        "value": Decimal("9"),
        "combos": [(2, Decimal("4")), (3, Decimal("10")), (5, Decimal("12")), (6, Decimal("15"))],
        "view_combos": [(2, Decimal("4")), (3, Decimal("10")), (5, Decimal("12")), (6, Decimal("15"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("3"),
    },
    Type.BUFF: {
        "name": "Sweet Candy",
        "short": "BUF",
        "medium": "BUFF",
        "filename": "buff",
        "value": Decimal("3"),
        "combos": [(2, Decimal("9")), (3, Decimal("10")), (5, Decimal("11")), (6, Decimal("12"))],
        "view_combos": [(2, Decimal("9")), (3, Decimal("10")), (5, Decimal("11")), (6, Decimal("12"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("2"),
    },
    Type.DEF: {
        "name": "Hard Walnut",
        "short": "DEF",
        "medium": "DEF",
        "filename": "def",
        "value": Decimal("9"),
        "combos": [(2, Decimal("10")), (3, Decimal("13")), (5, Decimal("20")), (6, Decimal("25"))],
        "view_combos": [(2, Decimal("10")), (3, Decimal("13")), (5, Decimal("20")), (6, Decimal("25"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("3"),
    },
    Type.BUFFRES: {
        "name": "Fresh Kiwi",
        "short": "DBF",
        "medium": "BUFFRES",
        "filename": "dbuff",
        "value": Decimal("3"),
        "combos": [(2, Decimal("10")), (3, Decimal("11")), (5, Decimal("12")), (6, Decimal("13"))],
        "view_combos": [(2, Decimal("10")), (3, Decimal("11")), (5, Decimal("12")), (6, Decimal("13"))],
        "minsub": Decimal("1"),
        "maxsub": Decimal("2"),
    },
    Type.CRITRES: {
        "name": "Hearty Hazelnut",
        "short": "CRS",
        "medium": "CRITRES",
        "filename": "critres",
        "value": Decimal("4.5"),
        "combos": [(2, Decimal("20")), (3, Decimal("25")), (5, Decimal("30")), (6, Decimal("35"))],
        "view_combos": [(2, Decimal("20")), (3, Decimal("25")), (5, Decimal("30")), (6, Decimal("35"))],
        "minsub": Decimal("3"),
        "maxsub": Decimal("4"),
    },
}

Substats = Union[Type, Tuple[Type]]


class Topping:
    """A single topping"""

    def __init__(self, substats: List[Tuple[str, str]], resonance: Resonance = None):
        self.resonance = resonance
        self.flavor = Type(substats[0][0])
        self.substats = [
            (Type(substat), Decimal(value) if value != float("inf") else value) for substat, value in substats
        ]

    def __str__(self):
        short = "short"
        return f"{INFO[self.flavor]['medium']} : {', '.join(f'{INFO[flav][short]} - {sub}' for flav, sub in self.substats[1:])}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.substats == other.substats and self.resonance == other.resonance

    def __hash__(self):
        return id(self)

    @cache
    def value(self, substats: Union[Type, Iterable[Type]]):
        """Value of a topping given a specific substat type"""
        substats = substats if type(substats) is tuple else (substats,)
        return sum(value for stat_type, value in self.substats if stat_type in substats)

    def validate(self):
        substat, value = self.substats[0]
        if value > INFO[substat]["value"]:
            return False
        if len(set(substat for substat, _ in self.substats[1:])) != len(self.substats[1:]):
            return False
        for substat, value in self.substats[1:]:
            if not (INFO[substat]["minsub"] <= value <= INFO[substat]["maxsub"]):
                return False
        return True


class ToppingSet:
    """A collection of five toppings as a complete set"""

    def __init__(self, toppings: List[Topping]):
        self.toppings = toppings

    def __str__(self):
        return "\n".join(
            [
                "┌─────────────┬─────────────┐",
                f"│ATK     {str(self.raw(Type.ATK)).rjust(4)}%│DEF     {str(self.raw(Type.DEF)).rjust(4)}%│",
                f"│HP      {str(self.raw(Type.HP)).rjust(4)}%│ATK SPD {str(self.raw(Type.ATKSPD)).rjust(4)}%│",
                f"│CRIT%   {str(self.raw(Type.CRIT)).rjust(4)}%│CD      {str(self.raw(Type.CD)).rjust(4)}%│",
                f"│DMGRES  {str(self.raw(Type.DMGRES)).rjust(4)}%│CRITRES {str(self.raw(Type.CRITRES)).rjust(4)}%│",
                f"│BUFF    {str(self.raw(Type.BUFF)).rjust(4)}%│BUFFRES {str(self.raw(Type.BUFFRES)).rjust(4)}%│",
                "└─────────────┴─────────────┘",
            ]
        )

    def __hash__(self):
        return id(self)

    def raw(self, substat: Type, tart: Topping = None):
        total = sum(topping.value(substat) for topping in self.toppings)

        if tart and tart.substat == substat:
            total += tart.target
            
        return total

    def set_effect(self, substat: Type):
        """Value of the set bonus given topping set makeup"""
        for required_count, set_bonus in INFO[substat]["combos"][::-1]:
            if len([topping for topping in self.toppings if topping.flavor == substat]) >= required_count:
                return required_count, set_bonus
        return 0, Decimal("0")

    def value(self, substats: Union[Type, Iterable[Type]]):
        """Value of a topping set given a specific substat type"""
        substats = substats if type(substats) == tuple else (substats,)
        return sum(self.raw(substat) + self.set_effect(substat)[1] for substat in substats)
