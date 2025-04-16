from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from functools import cache
from typing import Any, List, Tuple, Optional

import yaml
from yaml import SafeLoader

from topping_bot.crk.cookies import Cookie
from topping_bot.optimize.toppings import INFO, Resonance, Topping, Type
from topping_bot.optimize.objectives import Special, Combo, EDMG, Vitality, Objective
from topping_bot.optimize.validity import Normal, Range, Equality, Relative
from topping_bot.util.const import TMP_PATH


DEFAULT_MODIFIERS = {
    Type.ATK: {
        "Base": Decimal(100),
    },
    Type.CRIT: {
        "Base": Decimal(5),
        "Eerie Haunted House Landmark": Decimal(8),
    },
    Type.CRIT_DMG: {
        "Base": Decimal(150),
        "CRIT DMG Bonus Lab": Decimal(20),
        "Chocolate Alter of the Fallen Landmark": Decimal(20),
    },
    Type.HP: {"Base": Decimal(100)},
}


def sanitize(requirements_fp, user_id=0, rem_leaderboard=False):
    tmp = TMP_PATH / f"{user_id}.yaml"

    with open(requirements_fp) as f:
        requirements = yaml.safe_load(f)

    if rem_leaderboard:
        requirements.pop("leaderboard", None)

    for cookie in requirements.get("cookies", []):
        for i, requirement in enumerate(cookie.get("requirements", [])):
            if type(requirement) == dict and requirement.get("max") and requirement["max"] == "E[Vit]":
                converted_req = {"max": "Vitality"}
                for substat, value in requirement.items():
                    if substat != "max":
                        converted_req[substat] = value
                cookie["requirements"][i] = converted_req

    filtered_mods = {}
    for substat, mods in requirements.get("modifiers", {}).items():
        filtered_substat = [mod for mod in mods if mod["source"]
            not in DEFAULT_MODIFIERS.get(Type(substat), {})]
        if filtered_substat:
            filtered_mods[substat] = filtered_substat
    if filtered_mods:
        requirements["modifiers"] = filtered_mods

    with open(tmp, "w") as f:
        yaml.safe_dump(requirements, f, indent=2, sort_keys=False)

    return tmp


class Requirements:
    def __init__(self, name: str, valid: List, objective: Any, mods: dict, resonance: List[Resonance], tart: Optional[Equality], biscuit: Optional[List[Equality]], weight: int = None):
        if not objective:
            raise Exception(f"{name} : one objective must be specified")
        self.name = name
        self.valid = valid
        self.objective = objective
        self.mods = mods
        self.resonance = resonance
        self.tart = tart
        self.biscuit = biscuit 
        self.weight = weight

    def __str__(self):
        result = f"**{self.name.upper()}**"
        result += "\n```"
        if self.resonance:
            filtered_resonance = [res for res in self.resonance if res != Resonance.NORMAL]
            if filtered_resonance:
                result += "\nResonance"
                for res in filtered_resonance:
                    result += f"\n├ {res.value}"
        if self.tart:
            result += "\nTart"
            result += f"\n├ {self.tart}"
        if self.biscuit:
            result += "\nBiscuit"
            for biscuit_line in self.biscuit:
                result += f"\n├ {biscuit_line}"
        if self.valid:
            result += "\nValidity"
            for valid in self.valid:
                result += f"\n├ {str(valid)}"
        result += "\nObjective"
        result += f"\n├ max {self.objective.type.value}"
        if self.objective.type == Type.COMBO:
            for substat in self.objective.objectives:
                result += f"\n  ↳ {substat.value}"
        return result + "```"

    @classmethod
    def from_yaml(cls, fp):
        """Loads cookie requirements from a properly formatted yaml file"""
        with open(fp) as f:
            requirements = yaml.load(f, SafeLoader)

        mods = defaultdict(Decimal)
        for stat, buffs in DEFAULT_MODIFIERS.items():
            for source, value in buffs.items():
                mods[stat] += value

        for stat, buffs in requirements.get("modifiers", {}).items():
            for buff in buffs:
                mods[Type(stat)] += Decimal(buff["value"])

        cookies = []
        cookie_names = set()

        for cookie in requirements["cookies"]:
            cookie_mods = mods.copy()
            valid_reqs, objective = [], None
            parsed_tart = None
            parsed_biscuit = []

            for requirement in cookie["requirements"]:
                if type(requirement) is str:
                    valid = cls.parse_valid_requirement(requirement)

                    if valid is None:
                        raise Exception(
                            f"{cookie['name']} : could not parse {requirement}")
                    if type(valid) is Relative and valid.cookie not in cookie_names:
                        raise Exception(
                            f"{cookie['name']} : relative target must be a previously seen cookie")

                    valid_reqs.append(valid)

                elif type(requirement) is dict:
                    if objective is not None:
                        raise Exception(
                            f"{cookie['name']} : only one objective may be specified")
                    if requirement.get("max") is None:
                        raise Exception(
                            f"{cookie['name']} : objective must have the 'max' key")

                    objective = cls.parse_objective_requirement(
                        requirement, cookie_mods)

                    if type(objective) is Combo and not objective.types:
                        raise Exception(
                            f"{cookie['name']} : Combo objective must specify substats")

            cookie_names.add(cookie["name"])
            if cookie.get("resonant"):
                resonances = [Resonance(r) for r in cookie.get("resonant")]
            elif Cookie.get(cookie["name"]):
                resonances = Cookie.get(cookie["name"]).resonant
            else:
                resonances = []
            resonances = resonances + [Resonance.NORMAL]
            weight = (
                int(requirements["leaderboard"][cookie["name"]])
                if requirements.get("leaderboard", {}).get(cookie["name"])
                else None
            )

            if cookie.get("tart") and isinstance(cookie["tart"], list):
                len_tart = len(cookie["tart"])
                if len_tart > 1:
                    raise Exception(f"{cookie['name']} : only one tart may be specified")
                
                if len_tart == 1:
                    tart_line = cookie["tart"][0]
                    if type(tart_line) is str:
                        tart_valid = cls.parse_valid_tart_line(tart_line)

                        if tart_valid is None:
                            raise Exception(
                                f"{cookie['name']} : could not parse tart {tart_line}")

                        parsed_tart = tart_valid

            if cookie.get("biscuit") and isinstance(cookie["biscuit"], list):
                for biscuit_line in cookie["biscuit"]:
                    if type(biscuit_line) is str:
                        biscuit_valid = cls.parse_valid_biscuit_line(biscuit_line)

                        if biscuit_valid is None:
                            raise Exception(
                                f"{cookie['name']} : could not parse biscuit {biscuit_line}")

                        parsed_biscuit.append(biscuit_valid)

            cookies.append(Requirements(
                cookie["name"], valid_reqs, objective, cookie_mods, resonances, parsed_tart, parsed_biscuit, weight=weight)
            )
        return cookies

    @staticmethod
    def parse_valid_biscuit_line(biscuit_line: str):
        result = Equality.parse(biscuit_line)
        if result:
            return result

    @staticmethod
    def parse_valid_tart_line(tart_line: str):
        result = Equality.parse(tart_line)
        if result:
            return result

    @staticmethod
    def parse_valid_requirement(requirement: str):
        for parser in (Normal, Range, Equality, Relative):
            result = parser.parse(requirement)
            if result:
                return result

    @staticmethod
    def parse_objective_requirement(requirement: dict, cookie_mods):
        objective = Type(requirement["max"])

        if objective == Type.COMBO:
            return Combo([Type(substat) for substat in requirement["substats"]], cookie_mods)
        elif objective == Type.E_DMG:
            for substat in cookie_mods:
                cookie_mods[substat] += Decimal(
                    requirement.get(substat.value, "0"))
            return EDMG(cookie_mods)
        elif objective == Type.VITALITY:
            for substat in cookie_mods:
                cookie_mods[substat] += Decimal(
                    requirement.get(substat.value, "0"))
            return Vitality(cookie_mods)
        else:
            return Objective(substat=objective)

    def realize(self, cookie_sets: dict):
        self.adjusted_valid = [req for valid in self.adjusted_valid for req in valid.convert(
            cookies=cookie_sets)]

        collapsed = {}
        for valid in self.adjusted_valid:
            valid.fuzz()

            if collapsed.get(valid):
                extreme = max if valid.op.str == ">=" else min
                collapsed[valid] = extreme(collapsed[valid], valid, key=lambda x: x.target)  # noqa
            else:
                collapsed[valid] = valid

        self.adjusted_valid = list(collapsed.values())

        matched = defaultdict(dict)
        for valid in self.adjusted_valid:
            matched[valid.substat][valid.op.str] = valid.target

        for s, bounds in matched.items():
            if bounds.get("<=", float("inf")) < bounds.get(">=", 0):
                raise ValueError(
                    f"{self.name} contains impossible requirements {bounds['>=']} <= {s.value} <= {bounds['<=']}"
                )

        if isinstance(self.objective, Special):
            bounds = self.objective.bounds
            for req in self.floor_reqs():
                substat, required = req.substat, req.target
                if bounds.get(substat):
                    bounds[substat]["min"] = min(
                        bounds[substat]["min"], required / Decimal("100"))
            for req in self.ceiling_reqs():
                substat, required = req.substat, req.target
                if bounds.get(substat):
                    bounds[substat]["max"] = min(
                        bounds[substat]["max"], required / Decimal("100"))

    @property
    @cache
    def merged_biscuit(self):
        """Merge biscuit lines by accumulating targets for the same substat."""
        if not self.biscuit:
            return None

        merged_biscuit = {}
        for curr_line in self.biscuit:
            substat_name = curr_line.substat.name
            if substat_name in merged_biscuit:
                merged_biscuit[substat_name].target += curr_line.target
            else:
                merged_biscuit[substat_name] = deepcopy(curr_line)

        return list(merged_biscuit.values())

    
    @property
    def adjusted_valid(self):
        """Adjust valid requirements by offsetting them with biscuit values."""
        
        if hasattr(self, "_adjusted_valid"):
            return self._adjusted_valid
        
        adjusted_valid = {line.substat.name: deepcopy(line) for line in self.valid}

        if self.merged_biscuit:
            for curr_biscuit_line in self.merged_biscuit:
                substat_name = curr_biscuit_line.substat.name
                biscuit_line_value = curr_biscuit_line.target
                
                if substat_name in adjusted_valid:
                    curr_adjusted_valid = adjusted_valid[substat_name]

                    if isinstance(curr_adjusted_valid, Range):
                        # For Range, we need to adjust both low and high targets
                        curr_adjusted_valid.low_target = max(
                            curr_adjusted_valid.low_target - biscuit_line_value, 0
                        )
                        curr_adjusted_valid.high_target = max(
                            curr_adjusted_valid.high_target - biscuit_line_value, 0
                        )
                    elif isinstance(curr_adjusted_valid, Equality) or isinstance(curr_adjusted_valid, Normal):
                        # For Equality and Normal, we just adjust the target
                        curr_adjusted_valid.target = max(
                            curr_adjusted_valid.target - biscuit_line_value, 0
                        )
                    else:
                        # todo confirm if need to handle Relative
                        pass
        return list(adjusted_valid.values())
    
    @adjusted_valid.setter
    def adjusted_valid(self, value):
        """Allow setting adjusted_valid."""
        self._adjusted_valid = value
    
    @property
    @cache
    def valid_substats(self):
        return tuple(r.substat for r in self.adjusted_valid if r.op.str == ">=" and r.substat not in self.objective.types)

    @property
    @cache
    def all_substats(self):
        return tuple(set(self.valid_substats + self.objective.types))

    @cache
    def floor(self, substat: Type):
        for req in self.adjusted_valid:
            if req.substat == substat and req.op.str == ">=":
                return req.target
        return Decimal(0)

    @cache
    def floor_reqs(self):
        return [valid for valid in self.adjusted_valid if valid.op.str == ">="]

    @cache
    def ceiling_reqs(self):
        return [valid for valid in self.adjusted_valid if valid.op.str == "<=" and valid.target != Decimal(0)]

    @cache
    def zero_reqs(self):
        return [valid for valid in self.adjusted_valid if valid.op.str == "<=" and valid.target == Decimal(0)]

    def best_possible_set_effect(self, combo: List[Topping], substats: Tuple[Type], non_match_count: int):
        best_set_bonuses = {
            2: {},
            3: {},
            5: {},
            6: {},
        }

        for s in substats:
            matching_count = sum(1 for t in combo if t.flavor == s)
            for req, bonus in INFO[s]["combos"]:
                if req <= matching_count:
                    best_set_bonuses[req][s] = max(best_set_bonuses[req].get(s, Decimal(0)), bonus)

        # check valid 2+3 combinations with different substats
        best_2_3_combo = Decimal(0)
        for s2, bonus2 in best_set_bonuses[2].items():
            for s3, bonus3 in best_set_bonuses[3].items():
                if s2 != s3:
                    best_2_3_combo = max(best_2_3_combo, bonus2 + bonus3)

        # best 2/3/5/6-piece bonuses (from any single substat)
        best_2 = max(best_set_bonuses[2].values(), default=Decimal(0))
        best_3 = max(best_set_bonuses[3].values(), default=Decimal(0))
        best_5 = max(best_set_bonuses[5].values(), default=Decimal(0))
        best_6 = max(best_set_bonuses[6].values(), default=Decimal(0))

        return max(best_2_3_combo, best_2, best_3, best_5, best_6)
                