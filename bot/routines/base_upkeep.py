from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

async def build_pylons_basic(bot: BotAI, iteration):
    
    if bot.structures(UnitTypeId.NEXUS).amount == 0:
        builder = bot.units(UnitTypeId.PROBE).ready.random
        bot.do(builder.build(UnitTypeId.NEXUS, bot.start_location))
        return
    
    nexus = bot.townhalls.ready.random
    pos = nexus.position.towards(bot.enemy_start_locations[0], 7)
    
    if (bot.can_afford(UnitTypeId.PYLON) and
        bot.already_pending(UnitTypeId.PYLON) == 0 and
        bot.supply_left < 3 * bot.townhalls.amount):
        
        await bot.build(UnitTypeId.PYLON, near=pos)
        
async def build_proxy_pylon(bot: BotAI, iteration, warpgate_amount=4, amount_limit=1):
    
    if (bot.can_afford(UnitTypeId.PYLON) and
        not bot.proxy_built and bot.structures(UnitTypeId.WARPGATE).amount >= warpgate_amount):
        
        pos = bot.game_info.map_center.towards(bot.enemy_start_locations[0], 5)
        await bot.build(UnitTypeId.PYLON, near=pos)
        bot.proxy_built = True
        
async def build_gateway_basic(bot: BotAI, iteration, amount_limit=1):
    
    if (bot.can_afford(UnitTypeId.GATEWAY) and
        bot.structures(UnitTypeId.PYLON).ready and
        bot.structures(UnitTypeId.GATEWAY).amount + bot.structures(UnitTypeId.WARPGATE).amount + 
        bot.already_pending(UnitTypeId.CYBERNETICSCORE) < amount_limit):
        
        pylon = bot.structures(UnitTypeId.PYLON).ready.random
        await bot.build(UnitTypeId.GATEWAY, near=pylon)
    
async def build_cybercore_basic(bot: BotAI, iteration, amount_limit=1):
    
    if (bot.can_afford(UnitTypeId.CYBERNETICSCORE) and
        bot.structures(UnitTypeId.PYLON).ready and
        bot.structures(UnitTypeId.CYBERNETICSCORE).amount + bot.already_pending(UnitTypeId.CYBERNETICSCORE) < amount_limit):
        
        pylon = bot.structures(UnitTypeId.PYLON).ready.random
        await bot.build(UnitTypeId.CYBERNETICSCORE, near=pylon)
        
async def chronoboost(bot: BotAI, iteration, building_type=UnitTypeId.NEXUS):
    
    if bot.structures(UnitTypeId.NEXUS).amount == 0:
        return
    
    target = bot.structures(building_type).ready.random
    nexus = bot.townhalls.ready.random
    if nexus.energy >= 50:
        nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)