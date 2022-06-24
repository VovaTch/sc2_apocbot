from typing import Dict
import asyncio

import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id
from bot.routines.economy import default_econ_power
from sc2.ids.upgrade_id import UpgradeId
from bot.routines.economy import distribute_workers_with_exception

STRUCTURES = {'pylon', 'gate', 'core', 'nexus', 'gas'}
UNITS = {'probe', 'stalker', 'zealot'}
UPGRADES = {'warpgate'}

TRANSLATOR = {'pylon': id.PYLON, # Buildings 
              'gate': id.GATEWAY, 
              'core': id.CYBERNETICSCORE, 
              'nexus': id.NEXUS, 
              'gas': id.ASSIMILATOR,
              'robo': id.ROBOTICSFACILITY,
              'forge': id.FORGE,
              'bay': id.ROBOTICSBAY,
              
              'probe': id.PROBE, # Units
              'stalker': id.STALKER, 
              'zealot': id.ZEALOT,
              'sentry': id.SENTRY,
              'adept': id.ADEPT,
              'dt': id.DARKTEMPLAR,
              'ht': id.HIGHTEMPLAR,
              'prism': id.WARPPRISM,
              'immortal': id.IMMORTAL,
              'colossus': id.COLOSSUS,
              'disruptor': id.DISRUPTOR,
              'phoenix': id.PHOENIX,
              'voidray': id.VOIDRAY,
              'oracle': id.ORACLE,
              'carrier': id.CARRIER,
              'tempest': id.TEMPEST,
              'archon': id.ARCHON,
              
              'warpgate': id.WARPGATE} # Upgrades

class BuildOrder:
    """
    A class that stores and executes a build order.
    """
    
    def __init__(self, 
                 bo_file_path: str,
                 chosen_bo: str) -> None:
        
        with open(bo_file_path, 'r') as f:
            raw_dict = yaml.safe_load(f)
            
        self.bo_dict: Dict[int, str] = raw_dict[chosen_bo]
            
        self.current_tasks = []
        self.chrono_target = None
        self.parse_supply = 0
        self.proxy_probe = None # This will assume a single proxy probe for now.
        self.required_build_counts = {}
        self.complete = False
            
    async def execute(self, bot: BotAI, iteration):
        
        # distribute the workers with excluding a proxy probe
        await distribute_workers_with_exception(bot, iteration, exception_probe=self.proxy_probe)
        
        # Designate a chronoboost nexus
        chrono_nexus = bot.structures(id.NEXUS).ready.random
        
        # Build probes by default
        await default_econ_power(bot, iteration)
        if bot.supply_used == 16:
            self.chrono_target = bot.structures(id.NEXUS).ready.first
        
        # Apply chronoboost
        if self.chrono_target is not None and chrono_nexus.energy >= 50:
            chrono_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.chrono_target)
                 
        for sup_key, tasks_together in self.bo_dict.items():
            
            # Restart the building amount dict
            self.required_build_counts = {}
            
            # Count the current supply and produce a required buildings count
            current_supply = bot.supply_used
            self._count_required_buildings(current_supply)
            
            # Break if supply is smaller, task is not pending yet
            if current_supply < sup_key:
                break
            
            # If the supply is equal, append tasks
            elif current_supply == sup_key and self.parse_supply < current_supply:
                tasks = tasks_together.split()
                self.current_tasks.extend(tasks)
                self.parse_supply = current_supply
            
            # Perform the tasks in order
            current_task_flag = False
            for task_idx in range(len(self.current_tasks)):
                if self.current_tasks[task_idx] != '-':
                    await self._perform_task(bot, task_idx, iteration)
                    current_task_flag = True
                if current_task_flag:
                    break
                
    async def _perform_task(self, bot: BotAI, task_idx: str, iteration):
        
        # If task is - then return.
        if self.current_tasks[task_idx] == '-':
            return
        
        task_split = self.current_tasks[task_idx].split('_')
        
        # Build building
        if task_split[0] in STRUCTURES:
            
            struct_id = TRANSLATOR[task_split[0]]
            
            # TODO: Change when the networks are activated, make gas
            if 'proxy' in task_split and 'pylon' in task_split:
                build_location = bot.game_info.map_center.towards(bot.enemy_start_locations[0], 4)
                self.proxy_probe = bot.units(id.PROBE).closest_to(build_location)
            elif 'proxy' in task_split:
                proxy_pylon = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0])
                if not proxy_pylon.is_ready:
                    return
                build_location = proxy_pylon.position.random_on_distance(4)
                self.proxy_probe = bot.units(id.PROBE).closest_to(build_location)
            elif 'pylon' in task_split:
                nexus = bot.townhalls.ready.random
                build_location = nexus.position.towards(bot.enemy_start_locations[0], 7)
            else:
                build_location = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
                
            build_location = await bot.find_placement(struct_id, near=build_location, placement_step=1)
                
            # Build either in the proxy location or in the base
            if bot.can_afford(struct_id) and struct_id != id.ASSIMILATOR:
                
                if bot.already_pending(struct_id) + bot.structures(struct_id).ready.amount < self.required_build_counts[task_split[0]]:
                    if 'proxy' in task_split:
                        self.proxy_probe.build(struct_id, build_location)
                    else:
                        await bot.build(struct_id, build_location)

                else:
                    self.current_tasks[task_idx] = '-'
                
            elif struct_id == id.ASSIMILATOR:
                nexus = bot.townhalls.ready.random
                gas_nodes = bot.vespene_geyser.closer_than(15, nexus)
                for gas_node in gas_nodes:
                    if not bot.can_afford(id.ASSIMILATOR):
                        return
                    worker = bot.select_build_worker(gas_node.position)
                    if worker is None:
                        return
                    if not bot.gas_buildings or not bot.gas_buildings.closer_than(1, gas_node):
                        worker.build(id.ASSIMILATOR, gas_node)
                        worker.stop(queue=True)
                        self.current_tasks[task_idx] = '-'
                
        # Unit building
        elif task_split[0] in UNITS:
                
            if task_split[0] == 'probe' and bot.structures(id.NEXUS).ready > 0:
                nexus = bot.structures(id.NEXUS).ready.random
                nexus.train(id.PROBE)
                self.current_tasks[task_idx] = '-'
                
            elif (task_split[0] in ['zealot', 'stalker', 'ht', 'dt', 'adept', 'sentry'] and 
                  bot.structures(id.GATEWAY).ready.amount + bot.structures(id.WARPGATE).ready.amount > 0):
                
                unit_type = TRANSLATOR[task_split[0]]
                # Warpgate warp-in
                if bot.structures(id.WARPGATE).ready.amount > 0 and bot.can_afford(unit_type) and bot.supply_left >= 2:
                    warpgate = bot.structures(id.WARPGATE).ready.random
                    warp_location = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0]).position.random_on_distance(4)
                    warpgate.warp_in(unit_type, warp_location)
                    self.current_tasks[task_idx] = '-'
                # Gateway training
                elif bot.can_afford(unit_type) and bot.supply_left >= 2:
                    gateway = bot.structures(id.GATEWAY).ready.random
                    if task_split[0] == 'zealot':
                        gateway.train(unit_type)
                        self.current_tasks[task_idx] = '-'
                    if task_split[0] in ['stalker', 'adept', 'sentry'] and bot.structures(id.CYBERNETICSCORE).ready.amount > 0:
                        gateway.train(unit_type)
                        self.current_tasks[task_idx] = '-'
                    if task_split[0] == 'ht' and bot.structures(id.TEMPLARARCHIVE).ready.amount > 0:
                        gateway.train(unit_type)
                        self.current_tasks[task_idx] = '-'
                    if task_split[0] == 'dt' and bot.structures(id.DARKSHRINE).ready.amount > 0:
                        gateway.train(unit_type)
                        self.current_tasks[task_idx] = '-'
                    
        # Upgrades
        elif task_split[0] in UPGRADES:
            
            if task_split[0] == 'warpgate':
                if (bot.can_afford(UpgradeId.WARPGATERESEARCH) and 
                    bot.already_pending(UpgradeId.WARPGATERESEARCH) == 0 and
                    bot.structures(id.CYBERNETICSCORE).ready.amount > 0):
                    
                    print(bot.structures(id.CYBERNETICSCORE).ready)
                    
                    cybercore = bot.structures(id.CYBERNETICSCORE).ready.first
                    cybercore.research(UpgradeId.WARPGATERESEARCH)
                    self.current_tasks[task_idx] = '-'
                    
                    if 'chrono' in task_split:
                        self.chrono_target = cybercore
                        
    def _count_required_buildings(self, current_supply):
        
        for sup_key, tasks_together in self.bo_dict.items():
            
            # Filter out premature build order commands
            if sup_key > current_supply:
                return
            
            tasks = tasks_together.split()
            
            for task in tasks:
                
                task_split = task.split('_')
                
                if task_split[0] in STRUCTURES and task_split[0] not in self.required_build_counts:
                    self.required_build_counts[task_split[0]] = 1
                elif task_split[0] in STRUCTURES and task_split[0] in self.required_build_counts:
                    self.required_build_counts[task_split[0]] += 1
        
                
                
            
        
                