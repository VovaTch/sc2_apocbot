from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId as id

async def train_stalkers_basic(bot: BotAI, iteration, position=None, warp=False):
    
    if warp is False or position is None:
        for gateway in bot.structures(id.GATEWAY).ready:
            if (bot.can_afford(id.STALKER) and gateway.is_idle):
                gateway.train(id.STALKER)
                
    else:
        for warpgate in bot.structures(id.WARPGATE).ready:
            if (bot.can_afford(id.STALKER) and warpgate.is_idle):
                warpgate.warp_in(id.STALKER, position=position)
                
async def train_gateway_unit_basic(bot: BotAI, unit_id: id, position=None):
    
    if bot.structures(id.WARPGATE).ready.amount == 0:
        for gateway in bot.structures(id.GATEWAY).ready:
            if (bot.can_afford(unit_id) and 
                gateway.is_idle and 
                bot.tech_requirement_progress(unit_id) == 1 and 
                bot.supply_left >= bot.calculate_supply_cost(unit_id)):
                
                gateway.train(unit_id)
                
    else:
        # Default position
        if position is None:
            position = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0]).position.random_on_distance(4)
            
        for warpgate in bot.structures(id.WARPGATE).ready:
            if (bot.can_afford(unit_id) and 
                warpgate.is_idle and 
                bot.tech_requirement_progress(unit_id) == 1 and 
                bot.supply_left >= bot.calculate_supply_cost(unit_id)):
                
                warpgate.warp_in(unit_id, position=position)
                
async def train_nongateway_unit_basic(bot: BotAI, unit_id: id, position=None):
    
    if unit_id in [id.OBSERVER, id.WARPPRISM, id.IMMORTAL, id.COLOSSUS, id.DISRUPTOR]:
        struct_id = id.ROBOTICSFACILITY
    elif unit_id in [id.PHOENIX, id.ORACLE, id.VOIDRAY, id.CARRIER, id.TEMPEST]:
        struct_id = id.STARGATE
    elif unit_id in [id.PROBE, id.MOTHERSHIP]:
        struct_id = id.NEXUS
        
    if bot.structures(struct_id).ready.amount > 0:
        for struct in bot.structures(struct_id).ready:
            if (bot.can_afford(unit_id) and 
                struct.is_idle and 
                bot.tech_requirement_progress(unit_id) == 1 and 
                bot.supply_left >= bot.calculate_supply_cost(unit_id)):
                
                struct.train(unit_id)