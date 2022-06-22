from sc2.bot_ai import BotAI, Race
from sc2.data import Result


class CompetitiveBot(BotAI):
    NAME: str = "CompetitiveBot"
    """This bot's name"""

    RACE: Race = Race.Protoss
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.distribute_workers()
        
        if self.game_info.player_races[1] == Race.Protoss:
            await self.pvp_gameplay(self, iteration)
            
        elif self.game_info.player_races[1] == Race.Terran:
            await self.pvt_gameplay(self, iteration)
            
        elif self.game_info.player_races[1] == Race.Zerg:
            await self.pvz_gameplay(self, iteration)
        
    
    async def pvp_gameplay(self, iteration: int):
        pass
    
    async def pvt_gameplay(self, iteration: int):
        pass
    
    async def pvz_gameplay(self, iteration: int):
        pass
        

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
