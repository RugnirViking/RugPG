from Entities.Components.ai import HostileEnemy
from Entities.Components import consumable
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
    consumable=consumable.HealingConsumable(amount=4),
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Scroll of Thunderclap",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)
confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Scroll of Lesser Confusion",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)
fireball_scroll = Item(
    char="~",
    color=(255, 75, 0),
    name="Scroll of Fireball",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)
fear_scroll = Item(
    char="~",
    color=(115, 115, 235),
    name="Scroll of Lesser Terror",
    consumable=consumable.FearConsumable(number_of_turns=10),
)
charm_scroll = Item(
    char="~",
    color=(135, 235, 75),
    name="Scroll of Lesser Mind Control",
    consumable=consumable.CharmConsumable(number_of_turns=10),
)