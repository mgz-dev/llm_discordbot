# llm_discordbot

 Connect Large Language Models to Discord Bots

 This discord bot is set up to support models which utilize the huggingface pipeline, though not all models have been tested for proper compatibility.

 Readme is a WIP

 ## Requirements
 
 Set up virtual environment with method of your choice (e.g. Anaconda)
 Install PyTorch, detailed directions here: https://pytorch.org/get-started/locally/
 
 Next clone repository and install requirements
 ```
 git clone 
 cd llm_discordbot
 pip install -r requirements.txt
 ``` 
 Note: The bitsandbytes wheel referenced in the requirements.txt file is for Windows. For WSL or Linux change to `bitsandbytes==0.37.2`

 ## Getting Started

 - Characters are stored as .json files. Prompt handling is set up to *mostly* follow popular conventions.
 {{char}} in text will automatically be replaced with character's name `char_name`
 - In conversation history, the DiscordBot's Discord Username will be replaced with `char_name` automatically when being fed into the model.

 Additional resources to make your own characters:
 - https://zoltanai.github.io/character-editor/
 - https://devkats.club/pygmalion-cct/

 TO DO: Set up ability to change tokens {{user}} to specific name for context 


## Bot commands from Discord Chat

| Commands         | Description |
|------------------|-------------|
| @mention or reply |Bot will respond |
| `!setlimit <int>`|Update the number of historical messages the bot will refer to|
| `!updateparam <param:str> <value>` |Update generation param {temperature, top_p, do_sample, etc}|
| `!updateparam <param:str>` |check current parameter value|
| `!updatecharacter <character:str>` |Swap to a different character config|


## Start up flag commands through argparse

| Flag             | Description |
|------------------|-------------|
| `-h`, `--help`   |display help msg from argparse|
| `-m`, `--model_name`|load in model from subfolder in models|
| `-c`, `--character`   |load in character.json from characters|
| `-p`, `--params`   | load in params.json from config/params|

 ## Credits
 This implementation is based on [teknium's Alpaca Discord Bot repo](https://github.com/teknium1/alpaca-roleplay-discordbot).
 Thanks for the great work!
