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

| Flag             | Description |
|------------------|-------------|
| `-h`, `--help`   |display help msg from argparse|
| `-m`, `--model_name`|load in model from subfolder in models|
| `-c`, `--character`   |load in character.json from characters|
| `-p`, `--params`   | load in params.json from config/params|

 ## Credits
 This implementation is based on [teknium's Alpaca Discord Bot repo](https://github.com/teknium1/alpaca-roleplay-discordbot).
 Thanks for the great work!
