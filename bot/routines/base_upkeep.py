from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id

async def build_pylons_basic(bot: BotAI, iteration):
    
    if bot.structures(id.NEXUS).amount == 0:
        builder = bot.units(id.PROBE).ready.random
        bot.do(builder.build(id.NEXUS, bot.start_location))
        return
    
    nexus = bot.townhalls.ready.random
    pos = nexus.position.towards(bot.enemy_start_locations[0], 7)
    
    if (bot.can_afford(id.PYLON) and
        bot.already_pending(id.PYLON) == 0 and
        bot.supply_left < 3 * bot.townhalls.amount):
        
        await bot.build(id.PYLON, near=pos)
        
async def build_proxy_pylon(bot: BotAI, iteration, warpgate_amount=4, amount_limit=1):
    
    if (bot.can_afford(id.PYLON) and
        not bot.proxy_built and bot.structures(id.WARPGATE).amount >= warpgate_amount):
        
        pos = bot.game_info.map_center.towards(bot.enemy_start_locations[0], 5)
        await bot.build(id.PYLON, near=pos)
        bot.proxy_built = True
        
async def build_gateway_basic(bot: BotAI, iteration, amount_limit=1):
    
    if (bot.can_afford(id.GATEWAY) and
        bot.structures(id.PYLON).ready and
        bot.structures(id.GATEWAY).amount + bot.structures(id.WARPGATE).amount + 
        bot.already_pending(id.CYBERNETICSCORE) < amount_limit):
        
        pylon = bot.structures(id.PYLON).ready.random
        await bot.build(id.GATEWAY, near=pylon)
    
async def build_cybercore_basic(bot: BotAI, iteration, amount_limit=1):
    
    if (bot.can_afford(id.CYBERNETICSCORE) and
        bot.structures(id.PYLON).ready and
        bot.structures(id.CYBERNETICSCORE).amount + bot.already_pending(id.CYBERNETICSCORE) < amount_limit):
        
        pylon = bot.structures(id.PYLON).ready.random
        await bot.build(id.CYBERNETICSCORE, near=pylon)
        
async def build_building(bot: BotAI, struct_id: id, iteration, location, worker=None, amount_limit=1):
    
    if struct_id != id.ASSIMILATOR:
        
        # Count all required buildings
        struct_amount = bot.structures(id.GATEWAY).ready.amount\
            + bot.structures(id.WARPGATE).ready.amount + bot.already_pending(id.GATEWAY) + bot.already_pending(id.WARPGATE)\
            if struct_id in [id.GATEWAY, id.WARPGATE]\
            else bot.structures(struct_id).ready.amount + bot.already_pending(struct_id)

        # print(struct_id, struct_amount, amount_limit, bot.structures(id.GATEWAY).amount, 
        #       bot.structures(id.WARPGATE).amount, bot.already_pending(id.GATEWAY))

        if (bot.can_afford(struct_id) and 
            struct_amount < amount_limit):
            
            if worker is None:
                await bot.build(struct_id, near=location)
            else:
                worker.build(struct_id, location)
    else:
        
        # Assimilator logic. Build if is available and not exceeding the limit count
        nexus = bot.townhalls.ready.random
        gas_node = bot.vespene_geyser.closer_than(15, nexus).random
        if not bot.can_afford(id.ASSIMILATOR):
            return
        worker = bot.select_build_worker(gas_node.position)
        if worker is None:
            return
        if ((not bot.gas_buildings or not bot.gas_buildings.closer_than(1, gas_node)) and
            bot.structures(id.ASSIMILATOR).ready.amount + bot.already_pending(id.ASSIMILATOR) < amount_limit):
            
            worker.build(id.ASSIMILATOR, gas_node)
            worker.stop(queue=True)
    
        
async def chronoboost(bot: BotAI, iteration, building_type=id.NEXUS):
    
    if bot.structures(id.NEXUS).amount == 0:
        return
    
    target = bot.structures(building_type).ready.random
    nexus = bot.townhalls.ready.random
    if nexus.energy >= 50:
        nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)
        