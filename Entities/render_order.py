from enum import auto, Enum


class RenderOrder(Enum):
    CORPSE = auto()
    FURNITURE = auto()
    ITEM = auto()
    ACTOR = auto()