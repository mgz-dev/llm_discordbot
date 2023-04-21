# llm_discordbot

 Connect Large Language Models to Discord Bots

 This discord bot is set up to support models which utilize the huggingface pipeline, though not all models have been tested for proper compatibility.

 Readme is a WIP

 ## Requirements
 
 Set up virtual environment with method of your choice (e.g. Anaconda)
 Install PyTorch, detailed directions here: https://pytorch.org/get-started/locally/
 
 Next clone repository and install requirements
 ```
 git clone https://github.com/mgz-dev/llm_discordbot
 cd llm_discordbot
 pip install -r requirements.txt
 ``` 
 Note: The bitsandbytes wheel referenced in the requirements.txt file is for Windows. For WSL or Linux change to `bitsandbytes==0.37.2`

 ## Getting Started

 - Characters are stored as .json files. Prompt handling is set up to *mostly* follow popular conventions.
 {{char}} in text will automatically be replaced with character's name `char_name`
 - In conversation history, the DiscordBot's Discord Username will be replaced with `char_name` automatically when being fed into the model.
 - Configure your bot and discord server settings under `config/config.json`

 Additional resources to make your own characters:
 - https://zoltanai.github.io/character-editor/
 - https://devkats.club/pygmalion-cct/


## Bot commands from Discord Chat

| Commands         | Description |
|------------------|-------------|
| @mention or reply |Bot will respond |
| `/setlimit <int>`|Update the number of historical messages the bot will refer to|
| `/updateparam <param:str> <value>` |Update generation param {temperature, top_p, do_sample, etc}|
| `/printparam <param:str>` |check current parameter value|
| `/updatecharacter <character:str>` |Swap to a different character config|
| `/reset_channel` | Delete and recreate current channel |
| `/instruct <persona:str> <instruction:str>` | Provide persona and instruction|
| `/trivia` | Generate a trivia question|
| `/conversation_starter<topic:str>`| Start a conversation|
| `/inspirational_quote`|Write an inspirational quote|
| `/random_fact`|Write a random fact|
| `/rhyme <word:str>`|Rhyme word|

instruct personas = ["casual", "professional", "storyteller", "sme", "ai"]

## Start up flag commands through argparse

| Flag             | Description |
|------------------|-------------|
| `-h`, `--help`   |display help msg from argparse|
| `-m`, `--model_name`|load in model from subfolder in models|
| `-c`, `--character`   |load in character.json from characters|
| `-p`, `--params`   | load in params.json from config/params|
| `-pl`, `--persistent_logs`| save to a persistent character log | 
| `-hl`, `--history_limit`   | limit lookback history in chat for bot |
  `-p`, `--permanent_dialogue` | make example dialogue in character card permanent context |


## Changelog

### (4/20)
- Migrated to slash commands and Client chatbot
- Added new slash commands for prompting
- Migrated configs and key into config.json

### (4/5) 
- Added logging for chats
- Refactored into character class method


## To-Do
- Implement cogs
- Add model download instructions
- Add support for quantized models
- Add support for LoRA
- Add support for Adapters


 ## Credits
 The discord interface implementation is based on [teknium's Alpaca Discord Bot repo](https://github.com/teknium1/alpaca-roleplay-discordbot)
 bitsandbytes windows conversion credit to [Adrian Popescu](https://github.com/acpopescu/bitsandbytes/tree/cmake_windows) and compiled by [jllllll](https://github.com/jllllll/bitsandbytes-windows-webui)