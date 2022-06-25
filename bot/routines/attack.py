from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id

async def basic_stalker_attack(bot: BotAI, iteration, min_attack_count=4):
    
    stalkers = bot.units(id.STALKER).ready.idle
    stalker_count = bot.units(id.STALKER).amount
    
    for stalker in stalkers:
        if stalker_count >= min_attack_count:
            stalker.attack(bot.enemy_start_locations[0])
            
async def adept_attack_logic_basic(bot: BotAI, iteration, min_attack_count=1):
    """
    Basic logic for a single adept traversing the map and reaching the enemy. Doesn't use phaseshift while at enemy base.
    """
    
    adepts = bot.units(id.ADEPT).ready.idle
    adept_count = bot.units(id.ADEPT).amount
    
    for adept in adepts:
        if adept_count >= min_attack_count:
            adept.attack(bot.enemy_start_locations[0])
            if (adept.position.distance_to(bot.enemy_start_locations[0]) > 10):
                adept(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, bot.enemy_start_locations[0])
                adept.attack(bot.enemy_start_locations[0])
            else:
                adept.attack(bot.all_enemy_units)
                
async def basic_base_defense_logic(bot: BotAI, iteration):
    """
    Basic logic for base defense. Concentrate forces in front of the nexus that is the closest to the enemy, 
    defend when enemy is seen in vision and is not too far away
    """
    
    units = bot.units.ready.exclude_type({id.PROBE, id.OBSERVER, id.ADEPT})
    concentrate_location = bot.townhalls.closest_to(
        bot.enemy_start_locations[0]).position.towards(bot.enemy_start_locations[0], distance=6)
    
    enemy_attackers = bot.enemy_units.visible.closer_than(20, bot.townhalls.closest_to(bot.enemy_start_locations[0]))
    
    if enemy_attackers:
        for unit in units:
            unit.attack(enemy_attackers.random) # TODO: create a micro script
    else:
        for unit in units:
            if unit.distance_to(concentrate_location) > 3:
                unit.move(concentrate_location)