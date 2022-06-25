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