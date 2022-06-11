from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

async def build_pylons_basic(bot: BotAI, iteration):
    
    nexus = bot.townhalls.ready.random
    pos = nexus.position.towards(bot.enemy_start_locations[0], 7)
    
    if (bot.can_afford(UnitTypeId.PYLON) and
        bot.already_pending(UnitTypeId.PYLON) == 0 and
        bot.supply_left < 3 * bot.townhalls.amount):
        
        await bot.build(UnitTypeId.PYLON, near=pos)
        
async def build_gateway_basic(bot: BotAI, iteration, amount_limit=1):
    
    if (bot.can_afford(UnitTypeId.GATEWAY) and
        bot.structures(UnitTypeId.PYLON).ready and
        bot.structures(UnitTypeId.GATEWAY).amount + bot.already_pending(UnitTypeId.CYBERNETICSCORE) < amount_limit):
        
        pylon = bot.structures(UnitTypeId.PYLON).ready.random
        await bot.build(UnitTypeId.GATEWAY, near=pylon)
    
async def build_cybercore_basic(bot: BotAI, iteration, amount_limit=1):
    
    if (bot.can_afford(UnitTypeId.CYBERNETICSCORE) and
        bot.structures(UnitTypeId.PYLON).ready and
        bot.structures(UnitTypeId.CYBERNETICSCORE).amount + bot.already_pending(UnitTypeId.CYBERNETICSCORE) < amount_limit):
        
        print(bot.already_pending(UnitTypeId.CYBERNETICSCORE))
        pylon = bot.structures(UnitTypeId.PYLON).ready.random
        await bot.build(UnitTypeId.CYBERNETICSCORE, near=pylon)
        
async def chronoboost(bot: BotAI, iteration, building_type=UnitTypeId.NEXUS):
    
    target = bot.structures(building_type).ready.random
    nexus = bot.townhalls.ready.random
    if nexus.energy >= 50:
        nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)