from Entities.Components.ai import HostileEnemy
from Entities.Components import consumable, equippable
from Entities.Components.equipment import Equipment
from Entities.Components.fighter import Fighter
from Entities.Components.inventory import Inventory
from Entities.Components.level import Level
from Entities.entity import Actor, Item, Entity

#####################
#   Actors/Mobs     #
#####################
player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)

orc = Actor( # "lean", green and mean
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0), # TODO: consider allowing enemies to pick up items
    level=Level(xp_given=35),
)
troll = Actor( # real ugly lookin fellow
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)

snowdrift = Entity(
    char="^",
    color=(255, 255, 255),
    name="A snowdrift",
)
statue = Entity(
    char="Ω",
    color=(120, 100, 100),
    name="A horribly twisted statue",
)
tree = Entity(
    char="▲",
    color=(50, 150, 50),
    name="A hardy evergreen tree",
    blocks_movement=True
)

###########################
#       Consumables       #
###########################
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


#########################
#       Equipment       #
#########################
dagger = Item(
    char="/", color=(0, 191, 255), name="Dagger", equippable=equippable.Dagger()
)

sword = Item(
    char="/", color=(0, 191, 255), name="Sword", equippable=equippable.Sword()
)

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatherArmor(),
)

chain_mail = Item(
    char="[", color=(139, 69, 19), name="Chain Mail", equippable=equippable.ChainMail()
)