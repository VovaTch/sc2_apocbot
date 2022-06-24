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
            and nexus.is_idle and bot.workers.amount < bot.townhalls.amount * 21:
        nexus.train(UnitTypeId.PROBE)
        
    # await mine_gasses_basic(bot, iteration)
    
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
                    
async def distribute_workers_with_exception(bot: BotAI, iteration, exception_probe=None, resource_ratio: float = 2.0):
    
    if not bot.mineral_field or not bot.workers or not bot.townhalls.ready:
            return
    worker_pool = bot.workers.idle
    if exception_probe in worker_pool:
        worker_pool.remove(exception_probe)
    bases = bot.townhalls.ready
    gas_buildings = bot.gas_buildings.ready

    # list of places that need more workers
    deficit_mining_places = []

    for mining_place in bases | gas_buildings:
        difference = mining_place.surplus_harvesters
        # perfect amount of workers, skip mining place
        if not difference:
            continue
        if mining_place.has_vespene:
            # get all workers that target the gas extraction site
            # or are on their way back from it
            local_workers = bot.workers.filter(
                lambda unit: unit.order_target == mining_place.tag or
                (unit.is_carrying_vespene and unit.order_target == bases.closest_to(mining_place).tag)
            )
        else:
            # get tags of minerals around expansion
            local_minerals_tags = {
                mineral.tag
                for mineral in bot.mineral_field if mineral.distance_to(mining_place) <= 8
            }
            # get all target tags a worker can have
            # tags of the minerals he could mine at that base
            # get workers that work at that gather site
            local_workers = bot.workers.filter(
                lambda unit: unit.order_target in local_minerals_tags or
                (unit.is_carrying_minerals and unit.order_target == mining_place.tag)
            )
        # too many workers
        if difference > 0:
            for worker in local_workers[:difference]:
                worker_pool.append(worker)
        # too few workers
        # add mining place to deficit bases for every missing worker
        else:
            deficit_mining_places += [mining_place for _ in range(-difference)]

    # prepare all minerals near a base if we have too many workers
    # and need to send them to the closest patch
    if len(worker_pool) > len(deficit_mining_places):
        all_minerals_near_base = [
            mineral for mineral in bot.mineral_field
            if any(mineral.distance_to(base) <= 8 for base in bot.townhalls.ready)
        ]
    # distribute every worker in the pool
    for worker in worker_pool:
        # as long as have workers and mining places
        if deficit_mining_places:
            # choose only mineral fields first if current mineral to gas ratio is less than target ratio
            if bot.vespene and bot.minerals / bot.vespene < resource_ratio:
                possible_mining_places = [place for place in deficit_mining_places if not place.vespene_contents]
            # else prefer gas
            else:
                possible_mining_places = [place for place in deficit_mining_places if place.vespene_contents]
            # if preferred type is not available any more, get all other places
            if not possible_mining_places:
                possible_mining_places = deficit_mining_places
            # find closest mining place
            current_place = min(deficit_mining_places, key=lambda place: place.distance_to(worker))
            # remove it from the list
            deficit_mining_places.remove(current_place)
            # if current place is a gas extraction site, go there
            if current_place.vespene_contents:
                worker.gather(current_place)
            # if current place is a gas extraction site,
            # go to the mineral field that is near and has the most minerals left
            else:
                local_minerals = (
                    mineral for mineral in bot.mineral_field if mineral.distance_to(current_place) <= 8
                )
                # local_minerals can be empty if townhall is misplaced
                target_mineral = max(local_minerals, key=lambda mineral: mineral.mineral_contents, default=None)
                if target_mineral:
                    worker.gather(target_mineral)
        # more workers to distribute than free mining spots
        # send to closest if worker is doing nothing
        elif worker.is_idle and all_minerals_near_base:
            target_mineral = min(all_minerals_near_base, key=lambda mineral: mineral.distance_to(worker))
            worker.gather(target_mineral)
        else:
            # there are no deficit mining places and worker is not idle
            # so dont move him
            pass