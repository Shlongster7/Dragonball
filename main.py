from twitchio.ext import commands
import os
from dotenv import load_dotenv
import pygame
from datetime import datetime, timedelta
import random
from collections import defaultdict
import requests
import asyncio

load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
API_BASE_URL = os.getenv('API_BASE_URL')
CHANNEL_ID = '480465221'

class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=ACCESS_TOKEN, prefix='!', initial_channels=['Shlongster7'])
        
        # Initialize global variables
        self.last_summon_time = defaultdict(lambda: None)
        self.last_wish_time = defaultdict(lambda: None)
        self.dragon_summon_status = defaultdict(lambda: False)
        self.dragonballs_collection = defaultdict(lambda: {'Earth': [], 'Namekian': [], 'Super': [], 'wish_count': {}})
        
        # Possible dragonball numbers for each set
        self.available_balls = {
            'Earth': [1, 2, 3, 4, 5, 6, 7],
            'Namekian': [1, 2, 3, 4, 5, 6, 7],
            'Super': [1, 2, 3, 4, 5, 6, 7]
        }
        
        self.costs = {
            'Earth': 5000,
            'Namekian': 12500,
            'Super': 20000
        }
        
        #Initialize Pygame for music playback
        pygame.mixer.init()
        
        self.redemption_names = {
            'Buy a Earth Dragonball': 'Earth',
            'Buy a Namekian Dragonball': 'Namekian',
            'Buy a Super Dragonball': 'Super' 
        }

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        asyncio.create_task(self.check_redemptions())
        
        
    async def check_redemptions(self):
        url = f'https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions'
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Client-ID': CLIENT_ID,
        }
        
        while True:
            params = {
                'broadcaster_id': CHANNEL_ID
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                redemptions = response.json().get('data', [])
                for redemption in redemptions:
                    if redemption['status'] == 'UNFULFILLED':
                        await self.handle_redemption(redemption)
            else:
                print(f"Error fetching redemptions: {response.status_code} - {response.text}")
            await asyncio.sleep(30)
                        
    async def handle_redemption(self, redemption):
        viewer_name = redemption['user_name']
        reward_title = redemption['reward']['title']
        
        if reward_title in self.redemption_names:
            print(f"{viewer_name} is attempting to redeem a {reward_title}.")
            await self.redeem_dragonball(viewer_name, self.redemption_names[reward_title])
            
    async def redeem_dragonball(self, viewer_name, ball_type):
        if ball_type not in self.available_balls:
            return
        
        user_points = await self.get_channel_points(viewer_name)
        cost = self.costs[ball_type]
        
        if user_points < cost:
            print(f"{viewer_name} does not have enough channel points to redeem a {ball_type}. Cost: {cost} points")
            return
        
        await self.deduct_channel_points(viewer_name, cost)
        
        current_balls = self.dragonballs_collection[viewer_name][ball_type]
        available_numbers = set(self.available_balls[ball_type])
        owned_numbers = {int(ball.split()[0]) for ball in current_balls}
        unowned_numbers = list(available_numbers - owned_numbers)
        
        if not unowned_numbers:
            print(f"{viewer_name} has already redeemed all {ball_type} dragonballs!")
            return
        
        new_ball_number = random.choice(unowned_numbers)
        new_ball = f"{new_ball_number} stars"
        
        self.add_dragonball(viewer_name, ball_type, new_ball)
        await self.send_message(f"{viewer_name} has redeemed a {new_ball}-star {ball_type} dragonall!")
        
    def add_dragonball(self, viewer_name, ball_type, ball_name):
        if viewer_name not in self.dragonballs_collection:
            self.dragonballs_collection[viewer_name] = {'Earth': [], 'Namekian': [], 'Super': [], 'wish_count': {}}
            
        if ball_type not in self.dragonballs_collection[viewer_name]['wish_count']:
            self.dragonballs_collection[viewer_name]['wish_count'] = {key: 0 for key in ['Earth', 'Namekian', 'Super']}
            
        if ball_type in self.dragonballs_collection[viewer_name]:
            if ball_name not in self.dragonballs_collection[viewer_name][ball_type]:
                self.dragonballs_collection[viewer_name][ball_type].append(ball_name)
                
    async def send_message(self, message):
        await self.get_channel('shlongster7').send(message)
        
    async def get_channel_points(self, viewer_name):
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Client-ID': CLIENT_ID
        }
        response = requests.get(f"{API_BASE_URL}/users?login={viewer_name}", headers=headers)
        user_data = response.json()
        
        if user_data['data']:
            user_id = user_data['data'][0]['id']
            user_points_response = requests.get(f"{API_BASE_URL}/channel_points?broadcaster_id={user_id}", headers=headers)
            return user_points_response.json().get('points', 0)
        return 0
    
    async def deduct_channel_points(self, viewer_name, amount):
        print(f"Deducted {amount} points from {viewer_name}.")
        
    

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        await ctx.send(f'Hello {ctx.author.name}!')
        
    @commands.command(name='redeem_dragonball')
    async def command_redeem_dragonball(self, ctx, ball_type: str):
        viewer_name = ctx.author.name
        print(f"{viewer_name} is attempting to redeem a {ball_type} dragonball.")
        
        if ball_type not in self.available_balls:
            await ctx.send(f"{viewer_name}, please choose a valid dragonball set: Earth, Namekian, or Super.")
            return
        
        user_points = await self.get_channel_points(viewer_name)
        cost = self.costs[ball_type]
        
        if user_points < cost:
            await ctx.send(f"{viewer_name}, you don't have enough channel points to redeem a {ball_type}. Cost {cost} point")
            return
        
        await self.deduct_channel_points(viewer_name, cost)
        
        current_balls = self.dragonballs_collection[viewer_name][ball_type]
        available_numbers = set(self.available_balls[ball_type])
        owned_numbers = {int(ball.split()[0]) for ball in current_balls}
        unowned_numbers = list(available_numbers - owned_numbers)
        
        if not unowned_numbers:
            await ctx.send(f"{viewer_name}, you have already redeemed all {ball_type} dragonballs!")
            return
        
        new_ball_number = random.choice(unowned_numbers)
        new_ball = f"{new_ball_number} stars"
            
        self.add_dragonball(viewer_name, ball_type, new_ball)
        await ctx.send(f"{viewer_name} has redeemed a {new_ball}-star {ball_type} dragonball!")
        
                
    @commands.command(name='summon')
    async def command_summon(self, ctx):
        viewer_name = ctx.author.name
        
        if not (len(self.dragonballs_collection[viewer_name]['Earth']) == 7 or
                len(self.dragonballs_collection[viewer_name]['Namekian']) == 7 or
                len(self.dragonballs_collection[viewer_name]['Super']) == 7):
            await ctx.send(f"{viewer_name}, you need all 7 dragonballs of any type to summon the dragon!")
            return
        
        if self.dragon_summon_status[viewer_name]:
            await ctx.send(f"{viewer_name}, you have already summoned the dragon! Make your wish.")
            return
        
        self.dragon_summon_status[viewer_name] = True
        self.last_summon_time[viewer_name] = datetime.now()
        self.play_music()
        
        asyncio.create_task(self.check_wish_timeout(viewer_name))
        
        print("Screen darkened (simulated).")
        
        await ctx.send(f"{viewer_name} has summoned Shenron! Type !wish followed by the type of dragonballs to make the wish.")
        
    async def check_wish_timeout(self, viewer_name):
        """check if the viewer takes too long to make a wish"""
        await asyncio.sleep(300)
        
        if self.dragon_summon_status[viewer_name]:
            await self.reset_dragonballs(viewer_name)
            self.dragon_summon_status[viewer_name] = False
            self.stop_music()
            await self.send_message(f"{viewer_name}, you took too long to make a wish! The dragon has returned to rest.")
            
    def reset_dragonballs(self, viewer_name):
        """Reset the viewer's dragonballs collection."""
        for ball_type in self.dragonballs_collection[viewer_name]:
            if ball_type != 'wish_count':
                self.dragonballs_collection[viewer_name][ball_type] = []
        self.dragonballs_collection[viewer_name]['wish_count'] = {key: 0 for key in ['Earth', 'Namekian', 'Super']}
                
    @commands.command(name='wish')
    async def command_make_wish(self, ctx, ball_type: str):
        """Make a wish using a specific set of dragonballs."""
        viewer_name = ctx.author.name
        
        if not self.dragon_summon_status[viewer_name]:
            await ctx.send(f"{viewer_name}, you must summon the dragon first using !summon!")
            return
        
        if ball_type not in self.available_balls:
            await ctx.send(f"{viewer_name}, please choose a valid dragonball set: Earth, Namekian, or Super.")
            return
        
        if len(self.dragonballs_collection[viewer_name][ball_type]) < 7:
            await ctx.send(f"{viewer_name}, you need all 7 {ball_type} dragonballs to make a wish!")
            return
        
        current_time = datetime.now()
        last_time = self.last_wish_time[viewer_name]
        
        if last_time is not None and current_time < last_time + timedelta(minutes=1):
            remaining_time = (last_time + timedelta(minutes=1) - current_time).seconds // 60
            await ctx.send(f"{viewer_name}, you can only make a wish after a minute! please wait {remaining_time} more second(s).")
            return
        
        wish_limits = {
            'Earth': 1,
            'Namekian': 3,
            'Super': 1
        }
        
        if 'wish_count' not in self.dragonballs_collection[viewer_name]:
            self.dragonballs_collection[viewer_name]['wish_count'] = {key: 0 for key in wish_limit.keys()}
            
        if self.dragonballs_collection[viewer_name]['wish_count'][ball_type] >= wish_limits[ball_type]:
            await ctx.send(f"{viewer_name}, you have already made the maximum number of wishes with your {ball_type} dragonballs!")
            return
        
        outcomes = {
            'Earth': 'You make a regular wish, and it comes true!',
            'Namekian': 'Your regular wish(s) comes true!',
            'Super': 'The dragon grants you a legendary wish!'
        }
        
        self.dragonballs_collection[viewer_name]['wish_count'][ball_type] +=1
        self.last_wish_time[viewer_name] = current_time
        
        await ctx.send(f"{viewer_name}, your wish with {ball_type} dragonballs: {outcomes[ball_type]}")
        
        if self.dragonballs_collection[viewer_name]['wish_count'][ball_type] >= wish_limits[ball_type]:
            self.reset_dragonballs(viewer_name)
            
        self.dragon_summon_status[viewer_name] = False
        self.stop_music()
        
        print("Screen restored (simulated).")
        
    def reset_dragonballs(self, viewer_name):
        """Reset the viewer's dragonball collection."""
        for ball_type in self.dragonballs_collection[viewer_name]:
            if ball_type != 'wish_count':
                self.dragonballs_collection[viewer_name][ball_type] = []
        self.dragonballs_collection[viewer_name]['wish_count'] = {key: 0 for key in ['Earth', 'Namekian', 'Super']}
        
    def play_music(self):
        """Play the Shenron song."""
        pygame.mixer.music.load('shenron_song.mp3')
        pygame.mixer.music.play(-1)
        
    def stop_music(self):
        """Stop the music."""
        pygame.mixer.music.stop()
        
    
    @commands.command(name='cancel')
    async def command_cancel(self, ctx):
        """Cancel the summon after making a wish."""
        viewer_name = ctx.author.name
        
        if self.dragon_summon_status[viewer_name]:
            self.dragon_summon_status[viewer_name] = False
            self.stop_music()
            await ctx.send(f"{viewer_name}, you have canceled the summon of the dragon. Your wishes remain valid for future use!")
        else:
            await ctx.send(f"{viewer_name}, there is no summon to cancel.")


bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.