import discord
import asyncio
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
from discord.ext import commands
from modules.models import ChatBotModel
from modules.character import CharacterPersona

def main(args, chatbot):
    intents = discord.Intents.default()
    intents = discord.Intents.all()
    intents.members = True

    queue = asyncio.Queue()
    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")
        asyncio.get_running_loop().create_task(background_task())


    # Message detection and response function
    @bot.event
    async def on_message(current_message):
        # Do not continue is message is from self
        if current_message.author == bot.user:
            return

        await bot.process_commands(current_message)
        chatbot.discord_name = bot.user.name

        if isinstance(current_message.channel, discord.channel.DMChannel) or (bot.user and bot.user.mentioned_in(current_message)):
            # Fetch a list of cleaned message history
            message_history = await fetch_past_messages(current_message.channel)

            if current_message.reference:
                last_message = await current_message.channel.fetch_message(current_message.reference.message_id)
            else:
                last_message = None

            # Make sure last_message isn't included twice
            if last_message and (last_message in message_history):
                last_message = None

            await queue.put((current_message, last_message, message_history))


    async def fetch_past_messages(channel):
        global chatbot
        message_history = [message async for message in channel.history(limit=chatbot.message_history_limit)]
        return message_history


    async def background_task():
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        print("Model loaded, ready for generation.")
        while True:
            message_tuple: tuple[discord.Message, discord.Message, list] = await queue.get()
            current_message, last_message, message_history = message_tuple

            message_history_clean = [(message.author.display_name.strip(), message.clean_content.strip()) for message in message_history]
            current_message_clean = (current_message.author.display_name.strip(), current_message.clean_content.strip())
            if last_message:
                last_message_clean = (last_message.author.display_name.strip(), last_message.clean_content.strip())
            else:
                last_message_clean = None

            prompt = chatbot.generate_prompt(current_message_clean,
                                             last_message_clean,
                                             message_history_clean)

            response = await loop.run_in_executor(executor, chatbot.generate_reply, prompt)
            print(f"|| Prompt ||\n{prompt}\n\n||Response||\n{response}\n")

            try:
                await current_message.reply(response, mention_author=False)
            except discord.errors.Forbidden:
                print("Error: Missing Permissions")
                await current_message.channel.send("Retry")

    ##########################
    # Configuration Commands #
    ##########################

    # Command to change the message history context for chatbot
    @bot.command(description='Set maximum messages in history')
    @commands.is_owner()
    async def setlimit(ctx, limit: int):
        chatbot.message_history_limit = limit
        await ctx.send(f'Message history limit set to {limit}')

    @setlimit.error
    async def setlimit_error(ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('You do not have permission to use this command.')
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send('Invalid command. Usage: !setlimit <number>')

    @bot.command(description='Set response generation parameters')
    @commands.is_owner()
    async def updateparam(ctx, param: str, value):
        chatbot.param[f"{param}"] = value
        await ctx.send(f' parameter {param} updated to: {value}')

    @updateparam.error
    async def updateparam_error(ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('You do not have permission to use this command.')
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send('Invalid command. Usage: !updateparam <param_name:str> <value>')

    @bot.command(description='Change character json reference')
    @commands.is_owner()
    async def updatecharacter(ctx, character: str):
        chatbot.character_name = character
        await ctx.send(f' Character swapped to {character}')

    @updatecharacter.error
    async def updatecharacter_error(ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('You do not have permission to use this command.')
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send('Invalid command. Usage: !updatecharacter <str>')

    @bot.command(description='Print current params')
    @commands.is_owner()
    async def printparam(ctx, param: str):
        await ctx.send(f'Current {param}: {chatbot.params[f"{param}"]}')

    @printparam.error
    async def printparam_error(ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('You do not have permission to use this command.')
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send('Invalid command. Usage: !printparams')

    # Load the API key
    with open(os.path.join('config','key','key.txt'), "r") as f:
        key = f.read()
    # Start bot
    bot.run(key)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model_name", type=str, default = None, 
                        help="Input foldername of model within models subdirectory")
    parser.add_argument("-c", "--character", type=str, default = "default_character", 
                        help="Input character json filename  within character subdirectory")
    parser.add_argument("-p", "--params", type=str, default = "default_params")
    parser.add_argument("-pl", "--persistent_logs", action="store_true", help="Use persistent character log")
    parser.add_argument("-hl", "--history_limit", default=10, type=int, help="How many messages of history to use as context")
    parser.add_argument("-pdc", "--permanent_dialogue_context", action="store_true", help="Make character dialogue examples permanent context")
    args = parser.parse_args()
    print(f'model: {args.model_name}, character: {args.character}, params: {args.params}')

    character_path = os.path.join('characters', args.character+'.json')
    character_persona = CharacterPersona(character_path, args.permanent_dialogue_context, args.persistent_logs)

    chatbot = ChatBotModel(args.model_name, character_persona, args.params, args.history_limit)
    main(args, chatbot)
