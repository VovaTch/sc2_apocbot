import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from bot.build_order.bo_read import BuildOrder

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
        
        self.pvt_build_order = BuildOrder('bot/build_order/bo_pvp.yaml', self.config['pvt_build_order'])
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.distribute_workers()
        
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
        await self.pvt_build_order.execute(self, iteration)
    
    async def pvz_gameplay(self, iteration: int):
        pass
        

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
