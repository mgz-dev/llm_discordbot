import os, torch
from modules.utils import load_json


def generate_character(char_filename="default_character", user_name = "John"):
    json_path = os.path.join("characters", f"{char_filename}.json")
    char_data = load_json(json_path)

    # These are permenant and establish 
    char_name = char_data.get('char_name', 'ChatBot').strip()

    char_persona = char_data.get('char_persona', None)
    if not char_persona:
        char_persona = char_data.get('description', None)

    world_scenario = char_data.get('world_scenario', None)
    if not world_scenario:
        world_scenario = char_data.get('scenario', None)

    # These are temporary and get dropped
    char_greeting = char_data.get('char_greeting', None)
    if not char_greeting:
        char_greeting = char_data.get('first_mes', None)

    example_dialogue = char_data.get('example_dialogue', None)
    if not example_dialogue:
        example_dialogue = char_data.get('mes_example', '')

    context = ""

    if char_persona:
        context += f"{char_name}'s Persona: {char_persona.strip()}\n"
    if world_scenario:
        context += f"Scenario: {world_scenario.strip()}\n"

    context = f"{context.strip()}\n<START>\n"

    if example_dialogue:
        context += f"{example_dialogue.strip()}\n"

    if char_greeting:
        char_greeting = char_greeting.strip().replace('{{user}}', user_name).replace('{{char}}', char_name)
        char_greeting = char_greeting.strip().replace('<USER>', user_name).replace('<BOT>', char_name)

    context = context.replace('{{user}}', user_name).replace('{{char}}', char_name)
    context = context.replace('<USER>', user_name).replace('<BOT>', char_name)

    return context, char_greeting, char_name


def fix_bot_names_in_messages(discord_name, char_name, messages):
    if type(messages) == str:
        messages = [messages]
    fixed_messages = []
    for message in messages:
        fixed_message = message.replace(discord_name, char_name)
        fixed_messages.append(fixed_message)

    if len(fixed_messages) == 1:
        return fixed_messages[0]
    else:
        return fixed_messages


def generate_history(tokenizer, discord_name, char_name,
                     char_greeting,
                     current_message_clean,
                     last_message_clean,
                     message_history_clean,
                     max_history_tokens):

    consumed_tokens = 0
    history_text = ""

    # Pre-allocate tokens for current_message and last_message if present
    if current_message_clean:
        current_message_clean = fix_bot_names_in_messages(discord_name, char_name, current_message_clean)
        consumed_tokens += len(tokenizer.encode(current_message_clean))

    if last_message_clean:
        last_message_clean = fix_bot_names_in_messages(discord_name, char_name, last_message_clean)
        consumed_tokens += len(tokenizer.encode(last_message_clean))

    if message_history_clean:
        message_history_clean = fix_bot_names_in_messages(discord_name, char_name, message_history_clean)

        if type(message_history_clean) == str:
            message_history_clean = [message_history_clean]

        for past_message_text in message_history_clean:
            # If last_message is in history then set last_message to None 
            if (last_message_clean and (last_message_clean==past_message_text)):
                last_message_clean = None
                message_tokens = 0
            elif past_message_text.strip()==current_message_clean.strip():
                print("skipping current message in history")
                continue
            else:
                message_tokens = len(tokenizer.encode(past_message_text))

            if (consumed_tokens + message_tokens) > max_history_tokens:
                break
            else:
                history_text = past_message_text + '\n' + history_text
                consumed_tokens += message_tokens

    if char_greeting:
        char_greeting_tokens = len(tokenizer.encode(char_greeting))
        if (consumed_tokens + char_greeting_tokens) > max_history_tokens:
            pass
        else:
            consumed_tokens+= char_greeting_tokens
            history_text = char_greeting + '\n' + history_text

    history_text = history_text.strip()

    # Append last_message and current_message
    if last_message_clean:
        history_text = history_text + '\n' + last_message_clean
    if current_message_clean:
        history_text = history_text + '\n' + current_message_clean

    
    print(f"\n|| APPROXIMATE CONSUMED TOKENS FOR HISTORY: {consumed_tokens}\n")

    return history_text  + '\n'

def generate_prompt(chatbot, 
                    current_message_clean,
                    last_message_clean,
                    message_history_clean):
    character_name = chatbot.character_name
    discord_name = chatbot.discord_name

    context, char_greeting, char_name = generate_character(character_name)
    max_tokens = 2000
    tokenizer = chatbot.tokenizer
    context_token_length = len(tokenizer.encode(context))
    max_history_tokens = max_tokens - context_token_length

    
    history = generate_history(tokenizer, discord_name, char_name,
                               char_greeting,
                               current_message_clean,
                               last_message_clean,
                               message_history_clean,
                               max_history_tokens)

    prompt = context + history + f"\n{char_name}:".strip()
    return prompt
