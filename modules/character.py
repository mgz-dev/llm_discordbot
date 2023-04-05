from modules.utils import load_json
from modules.text_utils import replace_name_tokens
import os, json
from collections import defaultdict
from datetime import datetime

class Persona(object):
    """
    Abstract class for Personas.
    """

class CharacterPersona(Persona):
    def __init__(self, persona_json_dir: str, permanent_dialogue_context, persistent_logs):
        # Character qualities
        self.char_name = None
        self.char_persona = None
        self.world_scenario = None
        self.example_dialogue = None
        self.char_greeting = None

        # Character settings
        self.permanent_dialogue_context = permanent_dialogue_context

        # Interacting user settings
        self.user_name = "You"

        # Initialization
        self.load_persona(persona_json_dir)

        # Memories
        self.chat_history = defaultdict(list)

        if persistent_logs:
            self.log_path = os.path.join('logs', self.char_name+"_"+"persistent"+".json")
            if os.path.exists(self.log_path):
                print("\n|| Existing logs found... loading ||\n")
                logs = load_json(self.log_path)
                self.chat_history = logs['chat_history']
            else:
                print("\n|| No log found, new log will be generated ||\n")
        else:
            self.log_path = os.path.join('logs', self.char_name+"_"+datetime.now().strftime("%m%d%H%M%S")+".json")


    def load_persona(self, persona_json_dir:str):
        char_data = load_json(persona_json_dir)

        for key, value in char_data.items():
            char_data[key] = value.strip()

        # These are permanent and establish 
        char_name = char_data.get('char_name', 'ChatBot')

        char_persona = char_data.get('char_persona', None)
        if not char_persona:
            char_persona = char_data.get('description', None)

        world_scenario = char_data.get('world_scenario', None)
        if not world_scenario:
            world_scenario = char_data.get('scenario', None)

        # This is optionally permanent
        example_dialogue = char_data.get('example_dialogue', None)
        if not example_dialogue:
            example_dialogue = char_data.get('mes_example', '')

        # These are temporary and get dropped
        char_greeting = char_data.get('char_greeting', None)
        if not char_greeting:
            char_greeting = char_data.get('first_mes', None)

        self.char_name = char_name
        self.char_persona = char_persona
        self.world_scenario = world_scenario
        self.char_greeting = char_greeting
        self.example_dialogue = example_dialogue


    def generate_context(self, char_name=None, user_name=None):
        
        if not char_name:
            char_name = self.char_name
        if not user_name:
            user_name = self.user_name

        permanent_context = ""

        if self.char_persona:
            permanent_context += f"{self.char_name}'s Persona: {self.char_persona}\n"
        if self.world_scenario:
            permanent_context += f"Scenario: {self.world_scenario}\n"

        permanent_context = f"{permanent_context}\n<START>\n"

        if self.example_dialogue and self.permanent_dialogue_context:
            example_dialogue = self.generate_example_dialogue()
            permanent_context += f"{example_dialogue}"

        permanent_context = replace_name_tokens(permanent_context, char_name, user_name)

        return permanent_context


    def generate_example_dialogue(self, delim='\n', char_name=None, user_name=None):
        example_dialogue = self.example_dialogue
        if not char_name:
            char_name = self.char_name
        if not user_name:
            user_name = self.user_name

        if example_dialogue:
            if type(example_dialogue) == list:
                example_dialogue = delim.join(example_dialogue)
            example_dialogue = replace_name_tokens(example_dialogue, char_name, user_name)

        return example_dialogue


    def generate_greeting(self, delim=': ', char_name=None, user_name=None):
        char_greeting = self.char_greeting

        if not char_name:
            char_name = self.char_name
        if not user_name:
            user_name = self.user_name

        if char_greeting:
            char_greeting = replace_name_tokens(char_greeting, char_name, user_name)

            if not char_greeting.startswith(char_name):
                char_greeting = delim.join((char_name, char_greeting))

        return char_greeting

    def save_logs(self, log_path):
        with open(log_path, 'w') as f:
            json.dump(self.__dict__, f, sort_keys=False, indent=4)


    def load_logs(self, log_name):
        """current not used"""
        log_dict = load_json(os.path.join('logs', log_name))
        for key, value in log_dict.items():
            setattr(self, key, value)


    def add_message_to_history(self, message, location):
        self.chat_history[location].append(': '.join(message))


    def add_memories(self, context_memory, location):
        context_memory = [': '.join(message) for message in context_memory]
        for memory in reversed(context_memory):
            if memory not in self.chat_history[location]:
                self.chat_history[location].append(memory)
