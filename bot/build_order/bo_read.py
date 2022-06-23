from typing import Dict

import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id
from bot.routines.economy import default_econ_power
from sc2.ids.upgrade_id import UpgradeId

STRUCTURES = {'pylon', 'gate', 'core', 'nexus', 'gas'}
UNITS = {'probe', 'stalker', 'zealot'}
UPGRADES = {'warpgate'}

TRANSLATOR = {'pylon': id.PYLON, # Buildings 
              'gate': id.GATEWAY, 
              'core': id.CYBERNETICSCORE, 
              'nexus': id.NEXUS, 
              'gas': id.ASSIMILATOR,
              
              'probe': id.PROBE, # Units
              'stalker': id.STALKER, 
              'zealot': id.ZEALOT,
              
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
            
    async def execute(self, bot: BotAI, iteration):
        
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
            
            current_supply = bot.supply_used
            print(self.current_tasks)
            
            # Break if supply is smaller, task is not pending yet
            if current_supply < sup_key:
                break
            
            # If the supply is equal, append tasks
            elif current_supply == sup_key and self.parse_supply < current_supply:
                tasks = tasks_together.split()
                self.current_tasks.extend(tasks)
                self.parse_supply = current_supply
            
            for task_idx in range(len(self.current_tasks)):
                await self._perform_task(bot, task_idx, iteration)
                
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
            elif 'proxy' in task_split:
                proxy_pylon = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0])
                build_location = proxy_pylon.position.random_on_distance(4)
            elif 'pylon' in task_split:
                nexus = bot.townhalls.ready.random
                build_location = nexus.position.towards(bot.enemy_start_locations[0], 7)
            else:
                build_location = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
                
            if bot.can_afford(struct_id):
                await bot.build(struct_id, build_location)
                self.current_tasks[task_idx] = '-'
                
            if struct_id == 'gas':
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
                
            if task_split[0] == 'probe':
                nexus = bot.structures(id.NEXUS).ready.random
                nexus.train(id.PROBE)
                self.current_tasks[task_idx] = '-'
                
            elif task_split[0] in ['zealot', 'stalker', 'ht', 'dt', 'adept', 'sentry']:
                unit_type = TRANSLATOR[task_split[0]]
                # Warpgate warp-in
                if bot.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 1 and bot.can_afford(unit_type) and bot.supply_left >= 2:
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
                    
        
                
                
            
        
                