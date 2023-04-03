import json, gc, torch, os

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)
    return json_dict

def clear_cache():
    gc.collect()
    torch.cuda.empty_cache()

def ensure_path(obj_path, name, ext_list=None):

    if obj_path is None:
        print(f"Path cannot be None for {name}")
        raise Exception("None Path object received")

    is_dir = os.path.isdir(obj_path)
    is_file = os.path.isfile(obj_path)

    if ext_list and not is_file:
        # raise Exception("Path is not valid file")
        return False
    elif not ext_list and not is_dir:
        # raise Exception("Path is not valid folder")
        return False
    return True

