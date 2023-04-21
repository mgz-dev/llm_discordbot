import discord
import asyncio
import argparse
from typing import List
from concurrent.futures import ThreadPoolExecutor
from discord.ext import commands, tasks
from modules.models import ChatBotModel
from modules.character import CharacterPersona
from modules.utils import load_json

#######################
# load in config file #
#######################

config = load_json('config/config.json')

REQUIRED_ROLE_NAME = config['required_role_name']
MY_GUILD = discord.Object(id=config['my_guild'])
MY_ID = config['my_id']
key = config['key']

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, chatbot):
        super().__init__(intents=intents)
        """
        A CommandTree is a special type that holds all the application command
        state required to make it work. This is a separate class because it
        allows all the extra state to be opt-in.
        """

        self.tree = discord.app_commands.CommandTree(self)
        self.queue = asyncio.Queue() 
        self.chatbot = chatbot

    async def setup_hook(self):
        """
        This copies the global commands over to your guild.
        """
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        """
        Event handler for when the bot is ready.
        """
        await self.change_presence(activity=discord.Game(name="A.I. World Domination"))

        # Update bot's nickname
        guild = self.get_guild(MY_GUILD.id)
        member = guild.get_member(self.user.id)
        await member.edit(nick=self.chatbot.character_name)

        print(f"Logged in as {self.user} (ID: {self.user.id}, nickname: {self.chatbot.character_name})\n------")
    
        # Start background task
        self.background_task.start()

    @tasks.loop(seconds=5.0)
    async def background_task(self):
        """
        Background task to process prompts and generate replies using the chatbot model.
        """
        print("Waiting...")
        await self.wait_until_ready()
        print("Model loaded, ready for generation.")

        with ThreadPoolExecutor(max_workers=1) as executor:
            discord_obj, prompt, instruct = await self.queue.get()
            print("Message fetched from queue")

            current_channel = discord_obj.channel
            await current_channel.typing()
            response = await self.generate_reply(prompt, executor)
 

            print(f"|| Prompt ||\n{prompt}\n\n||Response||\n{response}\n")

            if type(discord_obj) == discord.Message:
                print("responding to message")
                await discord_obj.reply(response)
            elif type(discord_obj) == discord.Interaction:
                user = discord_obj.user
                embed = create_embed(instruct, user)
                if not discord_obj.response.is_done():
                    print("responding to interaction")
                    await discord_obj.response.send_message(content=response, embed=embed)
                else:
                    await discord_obj.followup.send(content=response, embed=embed)
    
    
    async def generate_reply(self, prompt, executor):
        """
        Generate a reply using the chatbot model given a prompt.
        """
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(executor, self.chatbot.generate_reply, prompt)
        return response
    
    
    ####################
    # Helper Functions #
    ####################

    def should_process_message(self, current_message: discord.Message) -> bool:
        """
        Determine if the bot should process the given message.
        """
        return current_message.author != self.user and (
            isinstance(current_message.channel, discord.channel.DMChannel) or self.user.mentioned_in(current_message)
        )

    async def get_last_message_if_referenced(self, current_message: discord.Message) -> discord.Message:
        "Retrieve the last message if the current message is a reply to it."
        if current_message.reference:
            return await current_message.channel.fetch_message(current_message.reference.message_id)
        return None

    async def fetch_past_messages(self, channel: discord.abc.Messageable) -> List[discord.Message]:
        """
        Fetch past messages from the channel up to the message history limit.
        """
        message_history = [message async for message in channel.history(limit=self.chatbot.message_history_limit)]
        print(f"Fetched: {chatbot.message_history_limit} messages")
        return message_history


    def clean_single_message(self, message: discord.Message) -> tuple[str, str]:
        """
        Clean a single message by extracting the display name and clean content.
        """
        return message.author.display_name.strip(), message.clean_content.strip()


    def clean_message_history(self, message_history: List[discord.Message]) -> List[tuple[str, str]]:
        """
        Clean the message history by extracting display names and clean contents for each message.
        """
        print("Cleaned History")
        return [self.clean_single_message(message) for message in message_history]

def has_required_role():
    """
    Check if the user has the required role to perform a command.
    """
    def predicate(ctx):
        return any(role.name == REQUIRED_ROLE_NAME for role in ctx.author.roles)
    return commands.check(predicate)

def create_embed(prompt, user):
    embed = discord.Embed(title='CogniBot', description=prompt, color=0x00ff00)
    embed.set_author(name=user.name, url="https://placeholder", icon_url=user.display_avatar.url)
    embed.set_thumbnail(url="attachment://thumb.webp")
    return embed


def main(args: argparse.Namespace, chatbot: ChatBotModel):
    """
    The main function to start the Discord bot and handle events.
    """
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    client = MyClient(intents=intents, chatbot=chatbot)

    @client.tree.command(name='sync', description='Owner only')
    async def sync(interaction: discord.Interaction):
        if interaction.user.id == MY_ID:
            await client.tree.sync()
            print('Command tree synced.')
            await interaction.response.send_message("Command tree synced")
        else:
            await interaction.response.send_message('You must be the owner to use this command!')

    ############################
    # Primary Message Commands #
    ############################

    @client.event
    async def on_message(current_message: discord.Message):
        """
        Event handler for when a message is sent in a channel the bot can read.
        """
        if not client.should_process_message(current_message):
            return

        client.chatbot.discord_name = client.user.name

        message_history = await client.fetch_past_messages(current_message.channel)
        last_message = await client.get_last_message_if_referenced(current_message)

        if last_message and (last_message in message_history):
            print("Last message was in history, removed from context")
            last_message = None
    
        message_history_clean = client.clean_message_history(message_history)
        current_message_clean = client.clean_single_message(current_message)
        last_message_clean = client.clean_single_message(last_message) if last_message else None

        prompt = client.chatbot.generate_prompt(current_message_clean, last_message_clean, message_history_clean)
        print("Prompt Generated:")
        print(prompt)

        await client.queue.put((current_message, prompt, None))

    ########################
    # Moderation  Commands #
    ########################

    @client.tree.command(name="purge_channel", description="Delete messages in the current channel")
    @discord.app_commands.checks.has_role(REQUIRED_ROLE_NAME)
    async def purge_channel(interaction: discord.Interaction):
        deleted = await interaction.channel.purge(limit=100)
        await interaction.response.send_message(f"Deleted len{deleted} message(s).")

    @client.tree.command(name="reset_channel", description="Delete and remake current channel")
    @discord.app_commands.checks.has_role(REQUIRED_ROLE_NAME)
    async def reset_channel(interaction: discord.Interaction):
        channel_name = interaction.channel.name
        category_name = interaction.channel.category
        guild = interaction.channel.guild
    
        await interaction.channel.delete()
        await guild.create_text_channel(name=channel_name, category=category_name)
        # await interaction.response.send_message(f"Reset {channel_name} in {category_name}")


    ##########################
    # Configuration Commands #
    ##########################

    # Command to change the message history context for chatbot
    @client.tree.command(name="setlimit", description='Set maximum messages in history')
    @discord.app_commands.checks.has_role(REQUIRED_ROLE_NAME)
    async def setlimit(interaction: discord.Interaction, limit: int):
        client.chatbot.message_history_limit = limit
        await interaction.response.send_message(f'Message history limit set to {limit}')

    @client.tree.command(name="updateparam", description="Set response generation parameters")
    @discord.app_commands.checks.has_role(REQUIRED_ROLE_NAME)
    async def updateparam(interaction: discord.Interaction, param: str, value: str):
    
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                await interaction.response.send_message(f"Invalid value for parameter {param}", ephemeral=True)
                return

        client.chatbot.params[f"{param}"] = value
        await interaction.response.send_message(f'Parameter {param} updated to: {value}', ephemeral=True)

    @client.tree.command(name="updatecharacter", description="Change character persona json reference")
    @discord.app_commands.checks.has_role(REQUIRED_ROLE_NAME)
    async def updatecharacter(interaction: discord.Interaction, character: str):
        client.chatbot.load_persona(character)
        await interaction.guild.me.edit(nick=client.chatbot.character_name)
        await interaction.response.send_message(f'Character swapped to {character}', ephemeral=True)

    @client.tree.command(name="printparam", description="Print current params")
    @discord.app_commands.checks.has_role(REQUIRED_ROLE_NAME)
    async def printparam(interaction: discord.Interaction, param: str):
        await interaction.response.send_message(f'Current {param}: {chatbot.params[f"{param}"]}', ephemeral=True)


    ################
    # Fun commands #
    ################
    @client.tree.command(name="trivia", description="Generate a trivia question")
    async def trivia(interaction: discord.Interaction):
        instruct = "Create a trivia question"

        # Acknowledge the interaction
        await interaction.response.defer()
        persona = "casual"
        prompt = chatbot.generate_instruct(persona, instruct)
        await client.queue.put((interaction, prompt, instruct))

    @client.tree.command(name="conversation_starter", description="Generate a conversation starter based on a given topic")
    async def conversation_starter(interaction: discord.Interaction, topic: str):
        instruct = f"Create a conversation starter about {topic}"

        # Acknowledge the interaction
        await interaction.response.defer()
        persona = "casual"
        prompt = chatbot.generate_instruct(persona, instruct)
        await client.queue.put((interaction, prompt, instruct))

    @client.tree.command(name="inspirational_quote", description="Generate an inspirational quote")
    async def inspirational_quote(interaction: discord.Interaction):
        instruct = "Create an inspirational quote"

        # Acknowledge the interaction
        await interaction.response.defer()
        persona = "storyteller"
        prompt = chatbot.generate_instruct(persona, instruct)
        await client.queue.put((interaction, prompt, instruct))

    @client.tree.command(name="random_fact", description="Generate a random fact")
    async def random_fact(interaction: discord.Interaction):
        instruct = "Create a random fact"
        # Acknowledge the interaction
        await interaction.response.defer()
        persona = "sme"
        prompt = chatbot.generate_instruct(persona, instruct)
        await client.queue.put((interaction, prompt, instruct))

    @client.tree.command(name="rhyme", description="Generate a list of words that rhyme with a given word")
    async def rhyme(interaction: discord.Interaction, word: str):
        instruct = f"Generate a list of words that rhyme with {word}"
        # Acknowledge the interaction
        await interaction.response.defer()
        persona = "professional"
        prompt = chatbot.generate_instruct(persona, instruct)
        await client.queue.put((interaction, prompt, instruct))


    @client.tree.command(name="instruct", description="Provide persona and instruction")
    async def instruct(interaction: discord.Interaction, persona: str, instruct: str):
        # Acknowledge the interaction
        await interaction.response.defer()
        prompt = chatbot.generate_instruct(persona, instruct)
        await client.queue.put((interaction, prompt, instruct))

    # Start client
    client.run(key)

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

    character_persona = CharacterPersona(args.character, args.permanent_dialogue_context, args.persistent_logs)

    chatbot = ChatBotModel(args.model_name, character_persona, args.params, args.history_limit)
    main(args, chatbot)
