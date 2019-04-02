import json

import utils

with open("data/pokedex.json", "r", encoding="utf-8") as f:
    pokedex_by_id = json.load(f)
    pokedex_by_name = {value: key for key, value in pokedex_by_id.items()}
with open("data/categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)


class Generation(utils.OrderedEnum):
    GEN1 = 1
    GEN2 = 2
    GEN3 = 3
    GEN4 = 4
    GEN5 = 5
    GEN6 = 6
    GEN7 = 7

    @staticmethod
    def from_pokemon_id(id):
        if not (1 <= id <= len(pokedex_by_id)):
            raise KeyError

        if id >= 722:
            return Generation.GEN7
        if id >= 650:
            return Generation.GEN6
        if id >= 494:
            return Generation.GEN5
        if id >= 387:
            return Generation.GEN4
        if id >= 252:
            return Generation.GEN3
        if id >= 152:
            return Generation.GEN2
        else:
            return Generation.GEN1

    def __str__(self):
        return f"{self.value}G"


class Category(utils.OrderedEnum):
    Trash = 1
    Common = 2
    Rare = 3
    Mythical = 4
    Legendary = 5

    @staticmethod
    def from_pokemon_id(id):
        id = str(id)
        if id not in pokedex_by_id:
            raise KeyError

        name = pokedex_by_id[id]
        if name in categories['Legendary']:
            return Category.Legendary
        if name in categories['Mythical']:
            return Category.Mythical
        if name in categories['Rare']:
            return Category.Rare
        return Category.Common

    @staticmethod
    def parse(arg):
        if not isinstance(arg, str):
            return
        if arg.isdigit():
            return Category(int(arg))
        else:
            return Category[arg.title()]

    def __str__(self):
        return self.name


class Pokemon:
    def __init__(self, id, name, alolan=False):
        self.id = id
        self.name = name
        self.alolan = alolan
        self.generation = Generation.from_pokemon_id(self.id)
        self.category = Category.from_pokemon_id(self.id)

    def __repr__(self):
        variant = "Alolan " if self.alolan else ""
        return f"{variant}{self.name} [{self.category}] (#{str(self.id).zfill(3)} {self.generation})"

    def __str__(self):
        variant = "Alolan " if self.alolan else ""
        return f"{variant}{self.name}"

    def to_dict(self):
        return {key: (value.to_dict() if callable(getattr(value, "to_dict", None)) else value) for
                key, value in self.__dict__.items()}

    @classmethod
    def from_id(cls, id):
        name = pokedex_by_id[str(id)]
        return cls(int(id), name)

    @classmethod
    def from_name(cls, name):
        alolan = "Alolan" in name
        name = name.replace("Alolan", "").strip()
        id = int(pokedex_by_name[name])
        return cls(id, name, alolan=alolan)
