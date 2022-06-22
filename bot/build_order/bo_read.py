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
                 bo_file_path: str) -> None:
        with open(bo_file_path, 'r') as f:
            self.bo_dict: Dict[int, str] = yaml.safe_load(f)
            
        self.current_tasks = []
        self.chrono_target = None
            
    async def execute(self, bot: BotAI, iteration):
        
        # Designate a chronoboost nexus
        chrono_nexus = bot.structures(id.NEXUS).ready.random
        
        # Build probes by default
        await default_econ_power()
        if bot.supply_army == 15:
            self.chrono_target = bot.structures(id.NEXUS).ready.first
        
        # Apply chronoboost
        if self.chrono_target is not None and chrono_nexus.energy >= 50:
            chrono_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.chrono_target)
            
        current_supply = bot.supply_army
        
        for sup_key, tasks_together in self.bo_dict.items():
            
            # Break if supply is smaller, task is not pending yet
            if current_supply < sup_key:
                break
            
            # If the supply is equal, append tasks
            elif current_supply == sup_key:
                tasks = tasks_together.split()
                self.current_tasks.extend(tasks)
            
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
                build_location = bot.game_info.map_center.towards(bot.enemy_start_locations[0], 20)
            elif 'proxy' in task_split:
                proxy_pylon = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0])
                build_location = proxy_pylon.position.random_on_distance(4)
            elif 'pylon' in task_split:
                nexus = bot.townhalls.ready.random
                build_location = nexus.position.towards(bot.enemy_start_locations[0], 7)
            else:
                build_location = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
                
            if bot.can_afford(struct_id):
                bot.do(bot.build(struct_id, build_location))
                self.current_tasks[task_idx] = '-'
                
        # Unit building
        elif task_split[0] in UNITS:
                
            if task_split[0] == 'probe':
                nexus = bot.structures(id.NEXUS).ready.random
                nexus.train(id.PROBE)
                self.current_tasks[task_idx] = '-'
                
            elif task_split[0] in ['zealot', 'stalker', 'ht', 'dt', 'adept', 'sentry']:
                unit_type = TRANSLATOR(task_split[0])
                # Warpgate warp-in
                if bot.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 1 and bot.can_afford(unit_type) and bot.supply_left >= 2:
                    warpgate = bot.structures(id.WARPGATE).ready.random
                    warp_location = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0]).position.random_on_distance(4)
                    warpgate.warp_in(unit_type, warp_location)
                    self.current_tasks[task_idx] = '-'
                # Gateway training
                elif bot.can_afford(unit_type) and bot.supply_left >= 2:
                    gateway = bot.structures(id.GATEWAY).ready.random
                    gateway.train(unit_type)
                    self.current_tasks[task_idx] = '-'
                    
        # Upgrades
        elif task_split[0] in UPGRADES:
            
            if task_split[0] == 'warpgate':
                if bot.can_afford(UpgradeId.WARPGATERESEARCH) and bot.already_pending(UpgradeId.WARPGATERESEARCH) == 0:
                    cybercore = bot.structures(id.CYBERNETICSCORE).ready.first
                    cybercore.research(UpgradeId.WARPGATERESEARCH)
                    self.current_tasks[task_idx] = '-'
                    
                if 'chrono' in task_split:
                    self.chrono_target = cybercore
                    
        
                
                
            
        
                