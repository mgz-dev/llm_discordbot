from transformers import AutoModelForCausalLM, AutoTokenizer
import torch, os, time
from datetime import datetime
from modules.utils import load_json, clear_cache
from modules.character import CharacterPersona
from modules.text_utils import generate_history, generate_temporary_context

class ChatBotModel:
    def __init__(self, model_name, character_persona, param_name, history_limit=10):

        model_dir = os.path.join('models', model_name)
        param_dir = os.path.join('config', 'params', param_name+'.json')
        self.log_path = character_persona.log_path

        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.tokenizer.truncation_side = 'left'
        print(f'\n|| TOKENIZER INITIALIZED: {self.tokenizer}')


        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=model_dir,
            load_in_8bit=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        self.params = load_json(param_dir)
        print(f'|| \nPARAMS: {self.params}\n||\n')

        self.discord_name = ""
        self.message_history_limit = history_limit 
        self.character_persona = character_persona
        self.character_name = character_persona.char_name
        self.max_tokens = 2000


    def generate_prompt(self,
                        current_message,
                        last_message,
                        message_history):

        discord_name = self.discord_name
        char_name = self.character_persona.char_name
        tokenizer = self.tokenizer
        max_tokens = self.max_tokens
        delim = ': '

        context = self.character_persona.generate_context()
        char_greeting = self.character_persona.generate_greeting()

        permanent_dialogue_context = self.character_persona.permanent_dialogue_context

        if not permanent_dialogue_context:
            example_dialogue = self.character_persona.generate_example_dialogue()
        else:
            example_dialogue = None

        context_token_length = len(tokenizer.encode(context))

        max_history_tokens = max_tokens - context_token_length

        reversed_context_memory, remaining_tokens = generate_history(tokenizer, 
                                                                    discord_name, char_name,
                                                                    current_message,
                                                                    last_message,
                                                                    message_history,
                                                                    max_history_tokens,
                                                                    delim=delim)

        self.character_persona.add_memories(reversed_context_memory, location="Discord")
        print(f"\n|| {len(reversed_context_memory)} messages of past history utilized ||\n")

        temporary_context = generate_temporary_context(tokenizer, 
                                                       reversed_context_memory,
                                                       char_greeting, example_dialogue,
                                                       remaining_tokens, delim)

        prompt = context + "\n" + temporary_context +"\n" + f"{char_name}:"
        return prompt


    def generate_reply(self, prompt):
        start_time = time.time()
        clear_cache()
        input_ids = self.tokenizer.encode(str(prompt), return_tensors="pt").cuda()
        params = self.params
        params["inputs"] = input_ids

        print(f"\n|| Consumed Tokens: {torch.numel(input_ids)} ||\n")

        output_ids = self.model.generate(**params)[0][input_ids.shape[-1]:].cuda()
        tokens_generated = torch.numel(output_ids)
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n||Generation speed: {total_time:.1f}s, {tokens_generated} tokens, {tokens_generated/total_time:.2f} tokens/s ||\n")
        
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        response = response.strip()

        char_name = self.character_persona.char_name
        response_memory = [(char_name, response)]
        self.character_persona.add_memories(response_memory, location="Discord")
        self.character_persona.save_logs(self.log_path)
        return response
