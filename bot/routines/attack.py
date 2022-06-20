from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId

async def basic_stalker_attack(bot: BotAI, iteration, min_attack_count=4):
    
    stalkers = bot.units(UnitTypeId.STALKER).ready.idle
    stalker_count = bot.units(UnitTypeId.STALKER).amount
    
    for stalker in stalkers:
        if stalker_count >= min_attack_count:
            stalker.attack(bot.enemy_start_locations[0])