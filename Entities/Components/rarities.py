from enum import auto, Enum
from typing import Tuple

from UI import color


class Rarity(Enum):
    JUNK = auto()
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()


def item_color(rarity: Rarity) -> Tuple[int, int, int]:
    col = (0, 0, 0)
    if rarity == Rarity.UNCOMMON:
        col = color.item_uncommon
    elif rarity == Rarity.RARE:
        col = color.item_rare
    elif rarity == Rarity.EPIC:
        col = color.item_epic
    elif rarity == Rarity.LEGENDARY:
        col = color.item_legendary
    elif rarity == Rarity.COMMON:
        col = color.item_common
    elif rarity == Rarity.JUNK:
        col = color.item_junk
    return col

def get_rarity_name(rarity: Rarity) -> str:
    name = ""
    if rarity == Rarity.UNCOMMON:
        col = color.item_uncommon
    elif rarity == Rarity.RARE:
        col = color.item_rare
    elif rarity == Rarity.EPIC:
        col = color.item_epic
    elif rarity == Rarity.LEGENDARY:
        col = color.item_legendary
    elif rarity == Rarity.COMMON:
        col = color.item_common
    elif rarity == Rarity.JUNK:
        col = color.item_junk
    return col
