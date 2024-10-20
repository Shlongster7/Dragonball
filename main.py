import random
from collections import defaultdict
from datetime import datetime, timedelta
import pygame
from twitchio.ext import commands

# Twitch bot setup (replace with your own Twitch token and channel)
CHANNEL = 'your_channel'
bot = commands.Bot(
    irc_token='oauth:your_token',
    client_id='your_client_id',
    nick='your_bot_nickname',
    prefix='!',
    initial_channels=[CHANNEL]
)

# Global variables
last_summon_time = defaultdict(lambda: None)
last_wish_time = defaultdict(lambda: None)
dragon_summon_status = defaultdict(lambda: False)

# Dragonball collection tracking
dragonballs_collection = defaultdict(lambda: {'Earth': [], 'Namekian': [], 'Super': [], 'wish_count': {}})

# Possible dragonball numbers for each set
available_balls = {
    'Earth': [1, 2, 3, 4, 5, 6, 7],
    'Namekian': [1, 2, 3, 4, 5, 6, 7],
    'Super': [1, 2, 3, 4, 5, 6, 7]
}

# Cost definitions
costs = {
    'Earth': 5000,
    'Namekian': 12500,
    'Super': 20000
}

# Initialize Pygame for music playback and screen effects
pygame.init()
screen = pygame.display.set_mode((800, 600))  # Set your desired dimensions
pygame.mixer.init()

def add_dragonball(viewer_name, ball_type, ball_name):
    """Add a dragonball to the viewer's collection."""
    if ball_type in dragonballs_collection[viewer_name]:
        if ball_name not in dragonballs_collection[viewer_name][ball_type]:
            dragonballs_collection[viewer_name][ball_type].append(ball_name)

def all_7_dragonballs(viewer_name):
    """Check if the viewer has all 7 dragonballs of any type."""
    for ball_type in dragonballs_collection[viewer_name]:
        if len(dragonballs_collection[viewer_name][ball_type]) == 7:
            return True
    return False

def reset_dragonballs(viewer_name):
    """Reset the viewer's dragonball collection."""
    for ball_type in dragonballs_collection[viewer_name]:
        if ball_type != 'wish_count':
            dragonballs_collection[viewer_name][ball_type] = []
    dragonballs_collection[viewer_name]['wish_count'] = {key: 0 for key in ['Earth', 'Namekian', 'Super']}

def play_music():
    """Play the Shenron song."""
    pygame.mixer.music.load('path/to/shenron_song.mp3')  # Replace with the local path to the song
    pygame.mixer.music.play(-1)  # Loop indefinitely

def stop_music():
    """Stop the music."""
    pygame.mixer.music.stop()

def draw_dark_overlay():
    """Draw a dark overlay when the dragon is summoned."""
    overlay_surface = pygame.Surface((800, 600))  # Create a surface the same size as the screen
    overlay_surface.fill((0, 0, 0))  # Fill it with black
    overlay_surface.set_alpha(128)  # Set the alpha for transparency
    screen.blit(overlay_surface, (0, 0))  # Draw the overlay on the screen

@bot.command(name='redeem_dragonball')
async def redeem_dragonball(ctx, ball_type: str):
    """Redeem a dragonball from the specified set."""
    viewer_name = ctx.author.name
    
    if ball_type not in available_balls:
        await ctx.send(f"{viewer_name}, please choose a valid dragonball set: Earth, Namekian, or Super.")
        return

    current_balls = dragonballs_collection[viewer_name][ball_type]
    
    new_ball = random.choice(available_balls[ball_type])
    
    while new_ball in current_balls:
        new_ball = random.choice(available_balls[ball_type])
        
    add_dragonball(viewer_name, ball_type, f"{new_ball} stars")
    await ctx.send(f"{viewer_name} has redeemed a {new_ball}-star {ball_type} dragonball!")

@bot.command(name='steal_dragonball')
async def steal_dragonball(ctx, target_username: str, ball_type: str):
    """Steal a dragonball from another viewer."""
    viewer_name = ctx.author.name
    
    if ball_type not in available_balls:
        await ctx.send(f"{viewer_name}, please choose a valid dragonball set: Earth, Namekian, or Super.")
        return
    
    # Check if the target user has any dragonballs of the specified type
    target_balls = dragonballs_collection[target_username][ball_type]
    
    if not target_balls:
        await ctx.send(f"{target_username} has no {ball_type} dragonballs to steal.")
        return

    # Calculate the cost
    steal_cost = costs[ball_type] * 2.5
    # You would normally check the user's channel points here (not shown in this code)
    
    # Randomly select a dragonball to steal
    stolen_ball = random.choice(target_balls)
    
    # Add the stolen ball to the viewer's collection
    add_dragonball(viewer_name, ball_type, stolen_ball)
    
    # Remove the stolen ball from the target's collection
    dragonballs_collection[target_username][ball_type].remove(stolen_ball)
    
    await ctx.send(f"{viewer_name} has stolen a {stolen_ball} star {ball_type} dragonball from {target_username}! (Cost: {steal_cost} points)")

@bot.command(name='wish')
async def make_wish(ctx, ball_type: str):
    """Make a wish using a specified set of dragonballs."""
    viewer_name = ctx.author.name

    if ball_type not in available_balls:
        await ctx.send(f"{viewer_name}, please choose a valid dragonball set: Earth, Namekian, or Super.")
        return

    if len(dragonballs_collection[viewer_name][ball_type]) < 7:
        await ctx.send(f"{viewer_name}, you need all 7 {ball_type} dragonballs to make a wish!")
        return

    current_time = datetime.now()
    last_time = last_wish_time[viewer_name]

    if last_time is not None and current_time < last_time + timedelta(minutes=5):
        remaining_time = (last_time + timedelta(minutes=5) - current_time).seconds // 60
        await ctx.send(f"{viewer_name}, you can only make a wish every 5 minutes! Please wait {remaining_time} more minute(s).")
        return

    wish_limits = {
        'Earth': 1,
        'Namekian': 3,
        'Super': 1
    }

    if 'wish_count' not in dragonballs_collection[viewer_name]:
        dragonballs_collection[viewer_name]['wish_count'] = {key: 0 for key in wish_limits.keys()}

    if dragonballs_collection[viewer_name]['wish_count'][ball_type] >= wish_limits[ball_type]:
        await ctx.send(f"{viewer_name}, you have already made the maximum number of wishes with your {ball_type} dragonballs!")
        return

    # Wish outcome messages
    outcomes = {
        'Earth': 'You make a simple wish, and it comes true!',
        'Namekian': 'Your wish brings you something useful!',
        'Super': 'The dragon grants you a powerful wish!'
    }

    # Increment the wish count
    dragonballs_collection[viewer_name]['wish_count'][ball_type] += 1
    last_wish_time[viewer_name] = current_time  # Update the last wish time

    # Send the outcome message
    await ctx.send(f"{viewer_name}, your wish with {ball_type} dragonballs: {outcomes[ball_type]}")
    
    # Reset dragonballs if all wishes are made
    if dragonballs_collection[viewer_name]['wish_count'][ball_type] >= wish_limits[ball_type]:
        reset_dragonballs(viewer_name)

    # Set summon status to true
    dragon_summon_status[viewer_name] = True
    play_music()  # Play music when the dragon is summoned

@bot.command(name='cancel')
async def cancel(ctx):
    """Cancel the summon after making a wish."""
    viewer_name = ctx.author.name

    if dragon_summon_status[viewer_name]:
        dragon_summon_status[viewer_name] = False  # Cancel the summon
        stop_music()  # Stop the music
        await ctx.send(f"{viewer_name}, you have canceled the summon of the dragon. Your wishes remain valid for future use!")
    else:
        await ctx.send(f"{viewer_name}, there is no summon to cancel.")

# Main loop for Pygame
def main_loop():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen
        screen.fill((255, 255, 255))  # Fill with white or your background color

        # Check if the dragon is summoned and draw the overlay
        if any(dragon_summon_status.values()):
            draw_dark_overlay()

        # Update the display
        pygame.display.flip()
        pygame.time.Clock().tick(60)

    pygame.quit()

if __name__ == "__main__":
    main_loop
