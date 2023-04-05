import json, gc, torch, os

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)
    return json_dict

def clear_cache():
    gc.collect()
    torch.cuda.empty_cache()
