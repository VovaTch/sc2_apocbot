from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId

async def default_econ_power(bot: BotAI, iteration):
    
    try: # Try and see there is a nexus
        nexus = bot.townhalls.ready.random
    except:
        print('No Nexi are left!')
        return
    
    if bot.can_afford(UnitTypeId.PROBE) \
            and nexus.is_idle and bot.workers.amount + bot.already_pending(UnitTypeId.PROBE) < bot.townhalls.amount * 22:
        nexus.train(UnitTypeId.PROBE)
        
    await mine_gasses_basic(bot, iteration)
    
async def mine_gasses_basic(bot: BotAI, iteration):
    
    if bot.structures(UnitTypeId.GATEWAY):
        for nexus in bot.townhalls.ready:
            gas_nodes = bot.vespene_geyser.closer_than(15, nexus)
            for gas_node in gas_nodes:
                if not bot.can_afford(UnitTypeId.ASSIMILATOR):
                    break
                worker = bot.select_build_worker(gas_node.position)
                if worker is None:
                    break
                if not bot.gas_buildings or not bot.gas_buildings.closer_than(1, gas_node):
                    worker.build(UnitTypeId.ASSIMILATOR, gas_node)
                    worker.stop(queue=True)