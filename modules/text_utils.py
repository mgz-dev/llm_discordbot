import re

def replace_name_tokens(text, char_name, user_name):
    text = text.replace('{{user}}', user_name).replace('<USER>', user_name)
    text = text.replace('{{char}}', char_name).replace('<BOT>', char_name)
    return text


def clean_messages(messages, discord_name, char_name):
    is_tuple = False

    if type(messages) == tuple:
        is_tuple = True
        messages = [messages]
    fixed_messages = []
    for username, message in messages:
        fixed_username, fixed_message = replace_discord_names(username, message, discord_name, char_name)
        fixed_message = clean_emoji_numbers(fixed_message)
        fixed_messages.append((fixed_username, fixed_message))

    if is_tuple:
        return fixed_messages[0]
    else:
        return fixed_messages

def clean_emoji_numbers(message):
    pattern = r'<a?(:\w+):\d+>'
    cleaned_message = re.sub(pattern, r'\1:', message)
    return cleaned_message

def replace_discord_names(username, message, discord_name, char_name):
    fixed_message = message.replace(discord_name, char_name)
    fixed_username = username.replace(discord_name, char_name)
    return fixed_username, fixed_message


def generate_history(tokenizer, 
                     discord_name, char_name,
                     current_message,
                     last_message,
                     message_history,
                     max_tokens,
                     delim = ': '):

    consumed_tokens = 0

    reversed_context_memory = []  # This is from most recent to oldest

    # Pre-allocate tokens for current_message and last_message if present
    if current_message:
        current_message = clean_messages(current_message, discord_name, char_name)
        consumed_tokens += len(tokenizer.encode(delim.join(current_message)))

    if last_message:
        last_message = clean_messages(last_message, discord_name, char_name)
        consumed_tokens += len(tokenizer.encode(delim.join(last_message)))

    if message_history:
        message_history = clean_messages(message_history, discord_name, char_name)

        for past_message in message_history:
            # If last_message is in history then set last_message to None 
            if (last_message and (last_message==past_message)):
                last_message = None
                message_tokens = 0
            elif past_message==current_message:
                print("skipping current message in history")
                continue
            else:
                message_tokens = len(tokenizer.encode(delim.join(past_message)))

            if (consumed_tokens + message_tokens) > max_tokens:
                break
            else:
                reversed_context_memory.append(past_message)
                consumed_tokens += message_tokens + 1

    remaining_tokens = max_tokens - consumed_tokens
    # Append last_message and current_message
    if last_message:
        reversed_context_memory.insert(0, last_message)
    if current_message:
        reversed_context_memory.insert(0, current_message)
    
    return reversed_context_memory, remaining_tokens


def generate_temporary_context(tokenizer, 
                               reversed_context_memory,
                               char_greeting, example_dialogue,
                               max_tokens, delim = ': '):
    consumed_tokens = 0

    reversed_context_messages = [delim.join(message) for message in reversed_context_memory]

    if char_greeting:
        char_message_tokens = len(tokenizer.encode(char_greeting))
        if (consumed_tokens + char_message_tokens) > max_tokens:
            pass
        else:
            consumed_tokens += char_message_tokens + 1
            reversed_context_messages.append(char_greeting)

    if example_dialogue:
        example_tokens = len(tokenizer.encode(example_dialogue))
        if (consumed_tokens + example_tokens) > max_tokens:
            pass
        else:
            consumed_tokens += example_tokens + 1
            reversed_context_messages.append(example_dialogue)

    temporary_context = '\n'.join(reversed(reversed_context_messages))
    return temporary_context

def fetch_instruct_preprompt(persona: str):
    if persona == "casual":
        context = "Imagine you are a friendly and casual person, eager to help others in a laid-back manner. Answer the following question or request while maintaining a lighthearted tone."
    elif persona == "professional":
        context = "As a professional with a deep understanding of the subject matter, provide a concise and well-organized response to the following question or request:"
    elif persona == "storyteller":
        context = "Picture yourself as a storyteller who enjoys weaving engaging narratives. When answering the following question or request, craft your response as an interesting story that captivates the reader."
    elif persona == "sme":
        context = "Assume you are an expert in the relevant field, and you're explaining the concept to someone new to the subject. Offer a clear, informative response to the following question or request, using analogies or examples where appropriate."
    else:
        context = "Imagine you are an advanced state-of-the-art language model capable of understanding and analyzing complex topics with ease. Provide a comprehensive and insightful response to the following query or request, demonstrating your deep knowledge and critical thinking skills."
    print(f"Personality: {context}")
    return context