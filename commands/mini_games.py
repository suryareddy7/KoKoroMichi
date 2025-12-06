# Mini Games Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
import asyncio
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number
from utils.channel_manager import check_channel_restriction

class NumberGuessingView(discord.ui.View):
    """Interactive number guessing game view"""
    
    def __init__(self, user_id: int, target_number: int, max_guesses: int, reward: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.target_number = target_number
        self.max_guesses = max_guesses
        self.guesses_left = max_guesses
        self.reward = reward
        self.game_over = False
    
    @discord.ui.button(label="Make Guess", style=discord.ButtonStyle.primary, emoji="🔢")
    async def make_guess(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Make a guess in the number game"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your game session.", ephemeral=True)
            return
        
        if self.game_over:
            await interaction.response.send_message("❌ This game has already ended.", ephemeral=True)
            return
        
        # Create modal for guess input
        modal = GuessModal(self)
        await interaction.response.send_modal(modal)

class GuessModal(discord.ui.Modal):
    """Modal for number guess input"""
    
    def __init__(self, game_view):
        super().__init__(title="Make Your Guess")
        self.game_view = game_view
        
        self.guess_input = discord.ui.TextInput(
            label="Enter your guess (1-100)",
            placeholder="Type a number between 1 and 100...",
            min_length=1,
            max_length=3
        )
        self.add_item(self.guess_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle guess submission"""
        try:
            guess = int(self.guess_input.value)
            if guess < 1 or guess > 100:
                await interaction.response.send_message("❌ Please guess a number between 1 and 100.", ephemeral=True)
                return
            
            await self.game_view.process_guess(interaction, guess)
            
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)

class MiniGamesCommands(commands.Cog):
    """Fun mini-games for entertainment and rewards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_games = {}  # Track active game sessions
    
    @commands.command(name="games", aliases=["minigames", "play"])
    @check_channel_restriction()
    async def view_games(self, ctx):
        """View available mini-games"""
        try:
            embed = self.embed_builder.create_embed(
                title="🎮 Mini-Games Arena",
                description="Play fun games to earn rewards and pass time!",
                color=0x9370DB
            )
            
            # Available games
            games = {
                "Number Guessing": {
                    "description": "Guess the secret number (1-100) to win gold!",
                    "command": "!guess_number",
                    "rewards": "100-1000 gold",
                    "emoji": "🔢"
                },
                "Rock Paper Scissors": {
                    "description": "Classic game against the bot!",
                    "command": "!rps <choice>",
                    "rewards": "50-500 gold",
                    "emoji": "✂️"
                },
                "Trivia Challenge": {
                    "description": "Answer anime and gaming trivia questions!",
                    "command": "!trivia",
                    "rewards": "200-800 gold + XP",
                    "emoji": "🧠"
                },
                "Slot Machine": {
                    "description": "Try your luck with the magical slot machine!",
                    "command": "!slots <bet>",
                    "rewards": "Up to 10x your bet",
                    "emoji": "🎰"
                },
                "Word Scramble": {
                    "description": "Unscramble character names for rewards!",
                    "command": "!scramble",
                    "rewards": "150-600 gold",
                    "emoji": "🔤"
                }
            }
            
            for game_name, game_info in games.items():
                embed.add_field(
                    name=f"{game_info['emoji']} {game_name}",
                    value=f"*{game_info['description']}*\n"
                          f"**Command:** {game_info['command']}\n"
                          f"**Rewards:** {game_info['rewards']}",
                    inline=True
                )
            
            # Show user's gaming stats
            user_data = data_manager.get_user_data(str(ctx.author.id))
            gaming_stats = user_data.get("gaming_stats", {})
            
            embed.add_field(
                name="🏆 Your Gaming Stats",
                value=f"**Games Played:** {gaming_stats.get('total_games', 0)}\n"
                      f"**Games Won:** {gaming_stats.get('games_won', 0)}\n"
                      f"**Total Winnings:** {format_number(gaming_stats.get('total_winnings', 0))} gold\n"
                      f"**Gaming Level:** {self.calculate_gaming_level(gaming_stats)}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_game_activity(ctx, "browse")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Games Error",
                "Unable to load mini-games."
            )
            await ctx.send(embed=embed)
            print(f"Games command error: {e}")
    
    @commands.command(name="guess_number", aliases=["number_game"])
    @check_channel_restriction()
    async def number_guessing_game(self, ctx):
        """Play the number guessing mini-game"""
        try:
            # Check if user already has an active game
            if str(ctx.author.id) in self.active_games:
                embed = self.embed_builder.warning_embed(
                    "Game In Progress",
                    "You already have an active game! Finish it first."
                )
                await ctx.send(embed=embed)
                return
            
            # Check cooldown (5 minutes between games)
            user_data = data_manager.get_user_data(str(ctx.author.id))
            gaming_stats = user_data.get("gaming_stats", {})
            last_game = gaming_stats.get("last_number_game", "")
            
            if last_game:
                last_time = datetime.fromisoformat(last_game)
                if datetime.now() - last_time < timedelta(minutes=5):
                    time_left = timedelta(minutes=5) - (datetime.now() - last_time)
                    minutes_left = int(time_left.total_seconds() / 60)
                    
                    embed = self.embed_builder.warning_embed(
                        "Game Cooldown",
                        f"Please wait {minutes_left} minutes before playing again."
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Start new game
            target_number = random.randint(1, 100)
            max_guesses = 7
            base_reward = 500
            
            # Create game session
            self.active_games[str(ctx.author.id)] = {
                "type": "number_guessing",
                "target": target_number,
                "guesses_left": max_guesses,
                "started_at": datetime.now()
            }
            
            # Create game view
            game_view = NumberGuessingView(ctx.author.id, target_number, max_guesses, base_reward)
            
            embed = self.embed_builder.create_embed(
                title="🔢 Number Guessing Game",
                description="I'm thinking of a number between **1** and **100**!\n"
                           "Can you guess it before you run out of tries?",
                color=0x9370DB
            )
            
            embed.add_field(
                name="🎯 Game Rules",
                value=f"• You have **{max_guesses}** guesses\n"
                      f"• I'll give you hints after each guess\n"
                      f"• Faster guesses = bigger rewards!\n"
                      f"• Base reward: {format_number(base_reward)} gold",
                inline=False
            )
            
            embed.add_field(
                name="🎮 How to Play",
                value="Click the button below to make your guess!",
                inline=False
            )
            
            await ctx.send(embed=embed, view=game_view)
            await self.log_game_activity(ctx, "start", "Number Guessing Game")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Game Start Error",
                "Unable to start number guessing game."
            )
            await ctx.send(embed=embed)
            print(f"Number game error: {e}")
    
    @commands.command(name="rps", aliases=["rockpaperscissors"])
    @check_channel_restriction()
    async def rock_paper_scissors(self, ctx, choice: str = None):
        """Play Rock Paper Scissors against the bot"""
        try:
            if not choice:
                embed = self.embed_builder.create_embed(
                    title="✂️ Rock Paper Scissors",
                    description="Choose your weapon!",
                    color=0x9370DB
                )
                
                embed.add_field(
                    name="🎮 How to Play",
                    value="Use `!rps <choice>` where choice is:\n"
                          "• `rock` 🪨\n"
                          "• `paper` 📄\n"
                          "• `scissors` ✂️",
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 Rewards",
                    value="• **Win:** 300 gold + 50 XP\n"
                          "• **Tie:** 100 gold\n"
                          "• **Loss:** 25 XP (consolation)",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            # Validate choice
            valid_choices = ["rock", "paper", "scissors"]
            user_choice = choice.lower()
            
            if user_choice not in valid_choices:
                embed = self.embed_builder.error_embed(
                    "Invalid Choice",
                    "Choose rock, paper, or scissors!"
                )
                await ctx.send(embed=embed)
                return
            
            # Bot makes choice
            bot_choice = random.choice(valid_choices)
            
            # Determine winner
            result = self.determine_rps_winner(user_choice, bot_choice)
            
            # Calculate rewards
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            if result == "win":
                gold_reward = 300
                xp_reward = 50
                user_data["gold"] = user_data.get("gold", 0) + gold_reward
                user_data["xp"] = user_data.get("xp", 0) + xp_reward
                result_text = "🏆 You Win!"
                color = 0x32CD32
            elif result == "tie":
                gold_reward = 100
                xp_reward = 0
                user_data["gold"] = user_data.get("gold", 0) + gold_reward
                result_text = "🤝 It's a Tie!"
                color = 0xFFD700
            else:
                gold_reward = 0
                xp_reward = 25
                user_data["xp"] = user_data.get("xp", 0) + xp_reward
                result_text = "😅 You Lose!"
                color = 0xFF6B6B
            
            # Update gaming stats
            gaming_stats = user_data.setdefault("gaming_stats", {})
            gaming_stats["total_games"] = gaming_stats.get("total_games", 0) + 1
            gaming_stats["rps_games"] = gaming_stats.get("rps_games", 0) + 1
            
            if result == "win":
                gaming_stats["games_won"] = gaming_stats.get("games_won", 0) + 1
                gaming_stats["rps_wins"] = gaming_stats.get("rps_wins", 0) + 1
            
            gaming_stats["total_winnings"] = gaming_stats.get("total_winnings", 0) + gold_reward
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create result embed
            choice_emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
            
            embed = self.embed_builder.create_embed(
                title="✂️ Rock Paper Scissors",
                description=result_text,
                color=color
            )
            
            embed.add_field(
                name="🎮 Game Results",
                value=f"**Your Choice:** {choice_emojis[user_choice]} {user_choice.title()}\n"
                      f"**Bot Choice:** {choice_emojis[bot_choice]} {bot_choice.title()}\n"
                      f"**Outcome:** {result.title()}",
                inline=True
            )
            
            # Show rewards
            rewards_text = ""
            if gold_reward > 0:
                rewards_text += f"💰 Gold: +{format_number(gold_reward)}\n"
            if xp_reward > 0:
                rewards_text += f"⭐ XP: +{format_number(xp_reward)}\n"
            
            embed.add_field(
                name="🎁 Rewards",
                value=rewards_text if rewards_text else "Better luck next time!",
                inline=True
            )
            
            await ctx.send(embed=embed)
            await self.log_game_activity(ctx, "rps", f"{result} vs {bot_choice}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "RPS Error",
                "Unable to play Rock Paper Scissors."
            )
            await ctx.send(embed=embed)
            print(f"RPS command error: {e}")
    
    @commands.command(name="slots", aliases=["slot_machine"])
    @check_channel_restriction()
    async def slot_machine(self, ctx, bet: int = None):
        """Play the magical slot machine"""
        try:
            if not bet:
                embed = self.create_slots_info_embed()
                await ctx.send(embed=embed)
                return
            
            # Validate bet
            if bet < 50 or bet > 5000:
                embed = self.embed_builder.error_embed(
                    "Invalid Bet",
                    "Bet amount must be between 50 and 5,000 gold."
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_gold = user_data.get("gold", 0)
            
            if user_gold < bet:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"You need {format_number(bet)} gold to play. You have {format_number(user_gold)} gold."
                )
                await ctx.send(embed=embed)
                return
            
            # Deduct bet
            user_data["gold"] -= bet
            
            # Spin the slots
            symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "⭐", "💎", "🌟"]
            weights = [25, 20, 20, 15, 10, 5, 3, 2]  # Weighted probabilities
            
            reel1 = random.choices(symbols, weights=weights)[0]
            reel2 = random.choices(symbols, weights=weights)[0]
            reel3 = random.choices(symbols, weights=weights)[0]
            
            # Calculate winnings
            winnings = self.calculate_slot_winnings(bet, reel1, reel2, reel3)
            
            if winnings > 0:
                user_data["gold"] += winnings
            
            # Update gaming stats
            gaming_stats = user_data.setdefault("gaming_stats", {})
            gaming_stats["total_games"] = gaming_stats.get("total_games", 0) + 1
            gaming_stats["slots_games"] = gaming_stats.get("slots_games", 0) + 1
            gaming_stats["total_slot_bets"] = gaming_stats.get("total_slot_bets", 0) + bet
            
            if winnings > bet:
                gaming_stats["games_won"] = gaming_stats.get("games_won", 0) + 1
                gaming_stats["total_winnings"] = gaming_stats.get("total_winnings", 0) + (winnings - bet)
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create result embed
            profit = winnings - bet
            
            if profit > 0:
                title = "🎰 Jackpot!"
                description = f"Amazing! You won {format_number(winnings)} gold!"
                color = 0x32CD32
            elif profit == 0:
                title = "🎰 Break Even"
                description = "You got your bet back!"
                color = 0xFFD700
            else:
                title = "🎰 Better Luck Next Time"
                description = "The slots didn't align this time."
                color = 0xFF6B6B
            
            embed = self.embed_builder.create_embed(
                title=title,
                description=description,
                color=color
            )
            
            embed.add_field(
                name="🎰 Slot Results",
                value=f"**Reels:** {reel1} {reel2} {reel3}\n"
                      f"**Bet:** {format_number(bet)} gold\n"
                      f"**Winnings:** {format_number(winnings)} gold\n"
                      f"**Profit:** {format_number(profit)} gold",
                inline=True
            )
            
            embed.add_field(
                name="💰 Account Balance",
                value=f"**New Balance:** {format_number(user_data['gold'])} gold",
                inline=True
            )
            
            # Show special combination message
            combination_msg = self.get_combination_message(reel1, reel2, reel3)
            if combination_msg:
                embed.add_field(
                    name="✨ Special Combination",
                    value=combination_msg,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            await self.log_game_activity(ctx, "slots", f"Bet {format_number(bet)}, won {format_number(winnings)}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Slots Error",
                "Unable to play slot machine."
            )
            await ctx.send(embed=embed)
            print(f"Slots command error: {e}")
    
    @commands.command(name="trivia", aliases=["quiz"])
    @check_channel_restriction()
    async def trivia_game(self, ctx):
        """Play trivia challenge"""
        try:
            # Sample trivia questions
            trivia_questions = [
                {
                    "question": "What is the most common rarity tier in gacha games?",
                    "options": ["Common", "Rare", "Super Rare", "Legendary"],
                    "correct": 0,
                    "category": "Gaming"
                },
                {
                    "question": "In anime, what does 'tsundere' personality type mean?",
                    "options": ["Always angry", "Cold then warm", "Very shy", "Extremely happy"],
                    "correct": 1,
                    "category": "Anime"
                },
                {
                    "question": "What element is typically strong against Water in RPGs?",
                    "options": ["Fire", "Earth", "Electric", "Wind"],
                    "correct": 2,
                    "category": "RPG"
                },
                {
                    "question": "Which is a common anime studio?",
                    "options": ["Studio Ghibli", "Marvel Studios", "Universal", "Warner Bros"],
                    "correct": 0,
                    "category": "Anime"
                }
            ]
            
            # Select random question
            question_data = random.choice(trivia_questions)
            
            embed = self.embed_builder.create_embed(
                title="🧠 Trivia Challenge",
                description=f"**Category:** {question_data['category']}\n\n**Question:**\n{question_data['question']}",
                color=0x9370DB
            )
            
            # Add options
            options_text = ""
            for i, option in enumerate(question_data["options"]):
                letter = chr(65 + i)  # A, B, C, D
                options_text += f"**{letter}.** {option}\n"
            
            embed.add_field(
                name="📝 Answer Options",
                value=options_text,
                inline=False
            )
            
            embed.add_field(
                name="💰 Rewards",
                value="• **Correct:** 400 gold + 200 XP\n"
                      "• **Wrong:** 50 gold + 25 XP (participation)",
                inline=False
            )
            
            embed.add_field(
                name="⏱️ Instructions",
                value="React with 🇦 🇧 🇨 or 🇩 to answer!\n"
                      "You have 30 seconds to respond.",
                inline=False
            )
            
            # Send question and add reactions
            message = await ctx.send(embed=embed)
            
            reactions = ["🇦", "🇧", "🇨", "🇩"]
            for reaction in reactions[:len(question_data["options"])]:
                await message.add_reaction(reaction)
            
            # Wait for reaction
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) in reactions and 
                       reaction.message.id == message.id)
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                # Determine answer
                answer_index = reactions.index(str(reaction.emoji))
                correct = answer_index == question_data["correct"]
                
                # Apply rewards
                if correct:
                    gold_reward = 400
                    xp_reward = 200
                    result_text = "🎉 Correct!"
                    color = 0x32CD32
                else:
                    gold_reward = 50
                    xp_reward = 25
                    result_text = "❌ Incorrect!"
                    color = 0xFF6B6B
                
                user_data["gold"] = user_data.get("gold", 0) + gold_reward
                user_data["xp"] = user_data.get("xp", 0) + xp_reward
                
                # Update stats
                gaming_stats = user_data.setdefault("gaming_stats", {})
                gaming_stats["total_games"] = gaming_stats.get("total_games", 0) + 1
                gaming_stats["trivia_games"] = gaming_stats.get("trivia_games", 0) + 1
                
                if correct:
                    gaming_stats["games_won"] = gaming_stats.get("games_won", 0) + 1
                    gaming_stats["trivia_correct"] = gaming_stats.get("trivia_correct", 0) + 1
                
                gaming_stats["total_winnings"] = gaming_stats.get("total_winnings", 0) + gold_reward
                
                # Save data
                data_manager.save_user_data(str(ctx.author.id), user_data)
                
                # Create result embed
                embed = self.embed_builder.create_embed(
                    title="🧠 Trivia Results",
                    description=result_text,
                    color=color
                )
                
                embed.add_field(
                    name="📝 Answer",
                    value=f"**Correct Answer:** {question_data['options'][question_data['correct']]}\n"
                          f"**Your Answer:** {question_data['options'][answer_index]}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎁 Rewards",
                    value=f"💰 Gold: +{format_number(gold_reward)}\n"
                          f"⭐ XP: +{format_number(xp_reward)}",
                    inline=True
                )
                
                await message.edit(embed=embed)
                await self.log_game_activity(ctx, "trivia", f"{result_text} - {question_data['category']}")
                
            except asyncio.TimeoutError:
                timeout_embed = self.embed_builder.warning_embed(
                    "Time's Up!",
                    "You didn't answer in time. Try again with `!trivia`!"
                )
                await message.edit(embed=timeout_embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Trivia Error",
                "Unable to play trivia game."
            )
            await ctx.send(embed=embed)
            print(f"Trivia command error: {e}")
    
    def determine_rps_winner(self, user_choice: str, bot_choice: str) -> str:
        """Determine Rock Paper Scissors winner"""
        if user_choice == bot_choice:
            return "tie"
        
        winning_combinations = {
            "rock": "scissors",
            "paper": "rock", 
            "scissors": "paper"
        }
        
        if winning_combinations[user_choice] == bot_choice:
            return "win"
        else:
            return "lose"
    
    def calculate_slot_winnings(self, bet: int, reel1: str, reel2: str, reel3: str) -> int:
        """Calculate slot machine winnings"""
        # Three of a kind
        if reel1 == reel2 == reel3:
            multipliers = {
                "🌟": 10.0,  # Jackpot
                "💎": 8.0,
                "⭐": 6.0,
                "🔔": 4.0,
                "🍇": 3.0,
                "🍊": 2.5,
                "🍋": 2.0,
                "🍒": 1.5
            }
            return int(bet * multipliers.get(reel1, 1.0))
        
        # Two of a kind
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            return int(bet * 0.5)
        
        # Special combinations
        elif set([reel1, reel2, reel3]) == {"💎", "⭐", "🌟"}:
            return int(bet * 5.0)  # Special combo
        
        else:
            return 0  # No win
    
    def get_combination_message(self, reel1: str, reel2: str, reel3: str) -> Optional[str]:
        """Get special message for slot combinations"""
        if reel1 == reel2 == reel3:
            if reel1 == "🌟":
                return "🌟 **MEGA JACKPOT!** The stars have aligned! 🌟"
            elif reel1 == "💎":
                return "💎 **DIAMOND FORTUNE!** Precious gems rain down! 💎"
            elif reel1 == "⭐":
                return "⭐ **STELLAR WIN!** The cosmos smiles upon you! ⭐"
            else:
                return f"🎉 **TRIPLE {reel1}!** Three of a kind! 🎉"
        
        elif set([reel1, reel2, reel3]) == {"💎", "⭐", "🌟"}:
            return "✨ **COSMIC ALIGNMENT!** The ultimate combination! ✨"
        
        return None
    
    def calculate_gaming_level(self, gaming_stats: Dict) -> int:
        """Calculate gaming level based on games played"""
        total_games = gaming_stats.get("total_games", 0)
        return min(50, 1 + (total_games // 10))
    
    def create_slots_info_embed(self) -> discord.Embed:
        """Create slot machine information embed"""
        embed = self.embed_builder.create_embed(
            title="🎰 Magical Slot Machine",
            description="Test your luck with the enchanted slots!",
            color=0x9370DB
        )
        
        embed.add_field(
            name="🎮 How to Play",
            value="Use `!slots <bet_amount>` to spin!\n"
                  "Minimum bet: 50 gold\n"
                  "Maximum bet: 5,000 gold",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Winning Combinations",
            value="🌟🌟🌟 - 10x bet (Mega Jackpot!)\n"
                  "💎💎💎 - 8x bet\n"
                  "⭐⭐⭐ - 6x bet\n"
                  "🔔🔔🔔 - 4x bet\n"
                  "Any three of a kind - varies\n"
                  "Two of a kind - 0.5x bet",
            inline=True
        )
        
        embed.add_field(
            name="✨ Special Combos",
            value="💎⭐🌟 - 5x bet (Cosmic Alignment!)\n"
                  "Various rare combinations give bonus rewards!",
            inline=True
        )
        
        return embed
    
    async def log_game_activity(self, ctx, activity_type: str, details: str = ""):
        """Log gaming activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["🎮", "🎰", "🎯", "🏆", "✨", "🎉"]
            emoji = random.choice(emojis)
            
            if activity_type == "browse":
                message = f"{emoji} **{ctx.author.display_name}** explored the exciting world of mini-games!"
            elif activity_type == "start":
                message = f"{emoji} **{ctx.author.display_name}** started playing {details}!"
            elif activity_type == "rps":
                message = f"{emoji} **{ctx.author.display_name}** played Rock Paper Scissors and {details}!"
            elif activity_type == "slots":
                message = f"{emoji} **{ctx.author.display_name}** spun the magical slot machine: {details}!"
            elif activity_type == "trivia":
                message = f"{emoji} **{ctx.author.display_name}** challenged their knowledge in trivia: {details}!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** enjoyed some fun mini-games!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x9370DB
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging game activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(MiniGamesCommands(bot))