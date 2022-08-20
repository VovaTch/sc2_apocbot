import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from bot.build_order.pvt_3gate_3base_colossi_8gate_chargelot import BuildOrder as BuildOrderPvT
from bot.midgame_strategy.pvt_4col_5ht_zealot_midgame import MidGameStrategy as MidGameStrategyPvT

'''
TODO:
1. General attacking routine
2. General expansion routine

TODO longer term:
1. Probe scouting routine
2. Adept scouting routine
3. Scouting information stack
4. Unit specific micro
5. Dynamic positioning
6. Endgame strategy

TODO deep learning:
1. Building placement
2. Micro?
3. Higher level strategy?

'''

class ApocBot(BotAI):
    NAME: str = "ApocAlypsE Bot"
    """This bot's name"""

    RACE: Race = Race.Protoss
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    async def on_start(self, config_path='bot/config/config.yaml'):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # PvT strategy
        self.pvt_build_order = BuildOrderPvT()
        self.pvt_midgame = MidGameStrategyPvT()
        
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        
        # Protoss vs Protoss gameplay loop
        if self.game_info.player_races[2] == 3:
            await self.pvp_gameplay(iteration)
            
        # Protoss vs Terran gameplay loop
        elif self.game_info.player_races[2] == 1:
            await self.pvt_gameplay(iteration)
            
        # Protoss vs Zerg or Random gameplay loop TODO: The random one is a placeholder
        elif self.game_info.player_races[2] in [2, 4]:
            await self.pvz_gameplay(iteration)
        
    
    async def pvp_gameplay(self, iteration: int):
        pass
    
    async def pvt_gameplay(self, iteration: int):
        
        # Execute a build order. TODO: Do it from a configuration yaml, specific for the bot/matchup
        if not self.pvt_build_order.build_order_finished:
            await self.pvt_build_order.execute(self, iteration)
        else:
            await self.pvt_midgame.execute(self, iteration)
    
    async def pvz_gameplay(self, iteration: int):
        pass
        

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
