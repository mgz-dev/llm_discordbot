from transformers import AutoModelForCausalLM, AutoTokenizer
import torch, os
from modules.utils import load_json, clear_cache

class ChatBotModel:
    def __init__(self, model_name, character_name, param_name, history_limit=10):

        model_dir = os.path.join('models', model_name)
        param_dir = os.path.join('config', 'params', param_name+'.json')
        # character_dir = os.path.join('character', character_name+'.json')

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

        self.character_name = character_name
        self.discord_name = ""

        self.message_history_limit = history_limit 

    def generate_reply(self, prompt):
        clear_cache()
        input_ids = self.tokenizer.encode(str(prompt), return_tensors="pt").cuda()
        params = self.params
        params["inputs"] = input_ids

        output_ids = self.model.generate(**params)[0][input_ids.shape[-1]:].cuda()
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        return response

