from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

async def basic_stalker_kiting(bot: BotAI, iteration):
    
    stalkers = bot.units(UnitTypeId.STALKER)
    enemy_location = bot.enemy_start_locations[0]
    
    if bot.structures(UnitTypeId.PYLON).ready:
        pylon = bot.structures(UnitTypeId.PYLON).closest_to(enemy_location)
        
        for stalker in stalkers:
            if stalker.weapon_cooldown == 0:
                stalker.attack(enemy_location)
            elif stalker.weapon_cooldown < 0:
                stalker.move(pylon)
            else:
                stalker.move(pylon)