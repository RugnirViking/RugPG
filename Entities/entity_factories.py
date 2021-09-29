from Entities.Components.ai import HostileEnemy, PlayerAI, IceSpellEnemy, RatMunchEnemy, BeastMunchEnemy, \
    IceSentryBossEnemy
from Entities.Components import consumable, equippable
from Entities.Components.equipment import Equipment
from Entities.Components.fighter import Fighter
from Entities.Components.inventory import Inventory
from Entities.Components.level import Level
from Entities.Components.rarities import Rarity
from Entities.entity import Actor, Item, Entity, PlateEntity, DoorShutTriggerEntity

#####################
#   Actors/Mobs     #
#####################
from Entities.render_order import RenderOrder


###########################
#       Enemies           #
###########################
player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=PlayerAI,
    equipment=Equipment(),
    fighter=Fighter(hp=50, base_defense=1, base_power=2),#fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
    emits_light=True,
    light_level=14,
)

orc = Actor( # "lean", green and mean
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3, will_chance=0.8),
    inventory=Inventory(capacity=0), # TODO: consider allowing enemies to pick up items
    level=Level(xp_given=35),
)
troll = Actor( # real ugly lookin fellow
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4, will_chance=0.95),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)
ice_golem = Actor( # big ice man big ice plan
    char="G",
    color=(0, 156, 226),
    name="Ice Golem",
    ai_cls=IceSpellEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=25, base_defense=3, base_power=4, will_chance=1.0),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=120),
)

mawrat = Actor( # it knows...
    char="r",
    color=(226, 156, 156),
    name="Mawrat",
    ai_cls=RatMunchEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=8, base_defense=0, base_power=2, will_chance=1.0),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=50),
)
mawbeast = Actor( # it knows more...
    char="M",
    color=(226, 156, 156),
    name="Mawbeast",
    ai_cls=BeastMunchEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=18, base_defense=4, base_power=4, will_chance=1.0),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=150),
)

ice_sentry_boss = Actor( # monstrous but good in a drink
    char="S",
    color=(0, 156, 226),
    name="Ice Sentry",
    ai_cls=IceSentryBossEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=150, base_defense=4, base_power=10, will_chance=1.0),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=1200),
    is_boss=True,
)

###########################
#       Furniture         #
###########################
snowdrift = Entity(
    char="^",
    color=(255, 255, 255),
    name="A snowdrift",
)
statue = Entity(
    char="Ω",
    color=(120, 100, 100),
    name="A horribly twisted statue",
    blocks_movement=True,
)
tree = Entity(
    char="▲",
    color=(50, 150, 50),
    name="A hardy evergreen tree",
    blocks_movement=True
)
stone_plate = PlateEntity(
    char="■",
    color=(150, 150, 150),
    name="A smooth stone plate",
    blocks_movement=False
)
hidden_door_shut_trigger = DoorShutTriggerEntity(
    char="",
    color=(150, 150, 150),
    name="",
    blocks_movement=False
)
cave_plant = Entity(
    char=":",
    color=(100, 150, 120),
    name="Cave Moss",
    blocks_movement=False
)
cave_plant2 = Entity(
    char="¥",
    color=(150, 100, 100),
    name="Bloodthistle Lichen",
    blocks_movement=False
)
cave_plant3 = Entity(
    char="*",
    color=(100, 120, 180),
    name="Brewspout Mushroom",
    blocks_movement=False
)
cave_plant4 = Entity(
    char="τ",
    color=(120, 80, 70),
    name="Babymuffin Mushroom",
    blocks_movement=False
)
table = Entity(
    char="┬",
    color=(70, 50, 0),
    name="A wooden table",
    blocks_movement=True,
    render_order=RenderOrder.FURNITURE
)

bedroll = Entity(
    char="º",
    color=(170, 150, 100),
    name="A crude linen bedroll",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE
)
barrel = Entity(
    char="o",
    color=(150, 100, 50),
    name="A barrel of foul-smelling liquid",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE
)
shelf = Entity(
    char="╬",
    color=(150, 100, 50),
    name="A shelf",
    blocks_movement=True,
    render_order=RenderOrder.FURNITURE
)
chair = Entity(
    char="h",
    color=(70, 50, 0),
    name="A wooden chair",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE
)
brazier = Entity(
    char="δ",
    color=(150, 110, 50),
    name="A flickering brazier",
    blocks_movement=True,
    render_order=RenderOrder.FURNITURE,
    emits_light=True,
    light_level=10,
)
torch = Entity(
    char="ƒ",
    color=(150, 110, 50),
    name="A flickering torch",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
    emits_light=True,
    light_level=10,
)
candles = Entity(
    char="╜",
    color=(150, 150, 150),
    name="A collection of candles",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
    emits_light=True,
    light_level=10,
)
candles2 = Entity(
    char="╙",
    color=(150, 150, 150),
    name="A collection of candles",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
    emits_light=True,
    light_level=10,
)
bed = Entity(
    char="Θ",
    color=(150, 130, 50),
    name="A wooden bed",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
)
wardrobe = Entity(
    char="∩",
    color=(150, 130, 50),
    name="A wooden wardrobe",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
)
cabinet = Entity(
    char="π",
    color=(150, 130, 50),
    name="A wooden cabinet",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
)
lectern = Entity(
    char="τ",
    color=(150, 130, 50),
    name="A wooden lectern",
    blocks_movement=False,
    render_order=RenderOrder.FURNITURE,
)

###########################
#       Consumables       #
###########################
health_potion = Item(
    char="!",
    color=(227, 127, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
    rarity=Rarity.COMMON,
    description="A vial of a red liquid - a healing potion. It heals 4 hitpoints when used. "
                "Doesn't smell great and tastes sickly sweet"
)
antivenom_potion = Item(
    char="!",
    color=(167, 227, 127),
    name="Antivenom Potion",
    consumable=consumable.AntivenomConsumable(),
    rarity=Rarity.COMMON,
    description="A vial of a green liquid - an emergency tincture that grants relief to those that have been poisoned. "
                "Removes poison effects when used. Doesn't smell great and tastes sickly sweet"
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Scroll of Thunderclap",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
    rarity=Rarity.COMMON,
    description="A scroll of Thunderclap. When used, strikes the nearest enemy with the force of a lightning strike. "
                "Magical scrolls are rolls of parchment with glyphs inset onto them, allowing an untrained user to "
                "activate it by reading aloud the activation phrase written on it. After use, the glyph fades, "
                "its power depleted"
)
confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Scroll of Lesser Confusion",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
    rarity=Rarity.COMMON,
    description="A scroll of Lesser Confusion. The user selects a target creature, and is able to scramble its "
                "thoughts, causing it to forget where it is and what it is doing. "
                "Magical scrolls are rolls of parchment with glyphs inset onto them, allowing an untrained user to "
                "activate it by reading aloud the activation phrase written on it. After use, the glyph fades, "
                "its power depleted"
)
fireball_scroll = Item(
    char="~",
    color=(255, 75, 0),
    name="Scroll of Fireball",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
    rarity=Rarity.UNCOMMON,
    description="A scroll of Fireball. The classic. The user activates its glyph and points at a target area, and "
                "everything within distance is engulfed in flame."
                "Magical scrolls are rolls of parchment with glyphs inset onto them, allowing an untrained user to "
                "activate it by reading aloud the activation phrase written on it. After use, the glyph fades, "
                "its power depleted"
)
fear_scroll = Item(
    char="~",
    color=(115, 115, 235),
    name="Scroll of Lesser Terror",
    consumable=consumable.FearConsumable(number_of_turns=10),
    rarity=Rarity.COMMON,
    description="A scroll of Lesser Terror. The user selects a target creature, and it runs in mortal fear from "
                "the caster, going so far as to attack anything that gets in its way so it can get further from the "
                "source of its fear."
                "Magical scrolls are rolls of parchment with glyphs inset onto them, allowing an untrained user to "
                "activate it by reading aloud the activation phrase written on it. After use, the glyph fades, "
                "its power depleted"
)
charm_scroll = Item(
    char="~",
    color=(135, 235, 75),
    name="Scroll of Lesser Mind Control",
    consumable=consumable.CharmConsumable(number_of_turns=10),
    rarity=Rarity.UNCOMMON,
    description="A scroll of Lesser Mind Control. The user selects a target creature, and is able to scramble its "
                "thoughts, causing it to forget where it is and what it is doing. "
                "Magical scrolls are rolls of parchment with glyphs inset onto them, allowing an untrained user to "
                "activate it by reading aloud the activation phrase written on it. After use, the glyph fades, "
                "its power depleted"
)


#########################
#       Equipment       #
#########################
dagger = Item(
    char="/",
    color=(0, 191, 255),
    name="Dagger",
    equippable=equippable.Dagger(),
    rarity=Rarity.COMMON,
    description="This is a dagger given to you by your father before he went to serve in the duke's armies. "
                "Some time ago you crudely carved your initials on the handle. It's a nice memento, and thanks to"
                "several run-ins with wolves in the forest you know how to use it, too."
)

sword = Item(
    char="/",
    color=(255, 191, 255),
    name="Sword",
    equippable=equippable.Sword(),
    rarity=Rarity.COMMON,
    description="This is a fine sword of the type used by soldiers of the duke. You're not quite sure how it got all "
                "the way down here - perhaps it was dropped by the last unlucky soul to try adventuring around here. "
                "Still, its a good weapon, and longer than a dagger"
)

ice_shard = Item(
    char="/",
    color=(140, 191, 255),
    name="Icerend",
    equippable=equippable.IceSword(),
    rarity=Rarity.RARE,
    description="This terrible sword, made from dwarven steel, is inset with cursed magical runes. It causes anyone "
                "struck by it to become terribly cold (10% chance on hit: inflict frost shock status)"
)

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatherArmor(),
    rarity=Rarity.COMMON,
    description="A leather tunic and some wits has saved many a person's life, and yours is no exception. With those "
                "two bite marks from, that time you were cornered by a mean looking boar it's somewhat "
                "worse for wear, but its the best you've got"
)
chain_mail = Item(
    char="[",
    color=(139, 69, 19),
    name="Chain Mail",
    equippable=equippable.ChainMail(),
    rarity=Rarity.COMMON,
    description="A suit of rusted chain mail. You had always wanted one of these after you saw a travelling merchant "
                "roll into town with a gleaming suit of chain-link armour. It provides good protection from blows "
                "but requires taking care of with oil to keep it from rusting, which the previous owner apparently "
                "didn't know."
)
scale_mail = Item(
    char="[",
    color=(139, 69, 19),
    name="Scale Mail",
    equippable=equippable.ScaleMail(),
    rarity=Rarity.UNCOMMON,
    description="An unusual suit of armour made from small interlocking metal plates. The links are somewhat "
                "vulnerable to flying apart when hit particularly hard. You think it makes you look like a fish. "
                "(+3 def +1 pow)"
)
red_shroud = Item(
    char="[",
    color=(139, 69, 19),
    name="Red Shroud",
    equippable=equippable.RedShroud(),
    rarity=Rarity.RARE,
    description="An unsettling red shroud with a rough picture of a face burned into it. "
                "Who made this horrible thing, and why? Holding it you can tell its made well, but there's something "
                "that tells you it is not a good idea to wear for too long (+1 def, Shroudthirst)"
)


cross_ring = Item(
    char="[",
    color=(160, 160, 160),
    name="Cross-Faced Ring",
    equippable=equippable.CrossRing(),
    rarity=Rarity.COMMON,
    description="This stone ring has an ornate cross face into its face. Wearing it makes you feel tougher"
                "(+15 max hp)"
)
antivenom_ring = Item(
    char="[",
    color=(0, 191, 255),
    name="Ring of the Serpent",
    equippable=equippable.AntivenomRing(),
    rarity=Rarity.UNCOMMON,
    description="These lightly magical rings are mass-produced in the south, where they are useful for dealing with "
                "the effects of animal bites (resist poison effects +1)"
)
antimagic_ring = Item(
    char="[",
    color=(100, 100, 120),
    name="Antimagic Ring",
    equippable=equippable.AntimagicRing(),
    rarity=Rarity.RARE,
    description="These valuable rings are used in the training of wizards. It allows the wearer to be less effected "
                "by magic, which is helpful when a novice sorcerer casts fireball in the auditorium! "
                "(resist magic effects +1)"
)
blood_ring = Item(
    char="[",
    color=(255, 0, 0),
    name="Blood Ring",
    equippable=equippable.BloodRing(),
    rarity=Rarity.RARE,
    description="This ring has a teardrop cabochon cut ruby inset into it's face. Wearing it makes you feel upset "
                "with the world (+1 pow)"
)
mana_ring = Item(
    char="[",
    color=(0, 80, 225),
    name="Mana Ring",
    equippable=equippable.ManaRing(),
    rarity=Rarity.RARE,
    description="This ring infuses the wearer with magical energies. Often used by sorcerers when performing long "
                "rituals, it allows the wearer cast more spells without feeling tired"
)