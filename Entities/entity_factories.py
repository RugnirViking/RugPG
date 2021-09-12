from Entities.Components.ai import HostileEnemy
from Entities.Components.consumable import HealingConsumable
from Entities.Components.fighter import Fighter
from Entities.Components.inventory import Inventory
from Entities.entity import Actor, Item

#####################
#   Actors/Mobs     #
#####################
player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=30, defense=2, power=5),
    inventory=Inventory(capacity=26),
)

orc = Actor( # "lean", green and mean
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=10, defense=0, power=3),
    inventory=Inventory(capacity=0), # TODO: consider allowing enemies to pick up items
)
troll = Actor( # real ugly lookin fellow
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=16, defense=1, power=4),
    inventory=Inventory(capacity=0),
)


#####################
#       Items       #
#####################
health_potion = Item(
    char="!",
    color=(227, 127, 255),
    name="Health Potion",
    consumable=HealingConsumable(amount=4),
)