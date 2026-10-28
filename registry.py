from effects import *

REGISTRY = {
    "1": {
        "name": ("horizontal rgb split", "rgb split", "horizontal rgb", "hor rgb", "hor"),
        "function": rgb_split,
        "default": 10
    },
    "2": {
        "name": ("vertical rgb split", "vertical rgb", "vert rgb", "vert"),
        "function": vertical_rgb_split,
        "default": 10
    },
    "3": {
        "name": ("gaussian blur", "blur"),
        "function": blur,
        "default": 3
    },
    "4": {
        "name": ("noise", "ns"),
        "function": noise,
        "default": 1
    },
    "5": {
        "name": ("slice", "slc"),
        "function": slice_glitch,
        "default": (10, 30)
    },
    "6": {
        "name": ("posterize", "poster"),
        "function": posterize,
        "default": 3
    },
    "7": {
        "name": ("solarize", "solar"),
        "function": solarize,
        "default": 128
    },
    "8": {
        "name": ("pixelate", "resample", "pixel"),
        "function": pixelate,
        "default": 8
    
    },
    "9": {
        "name": ("block corrupt", "corrupt"),
        "function": block_corrupt,
        "default": (12, 50)
    },
    "10": {
        "name": ("grayscale", "gs"),
        "function": grayscale,
        "default": None
    },
    "11": {
        "name": ("horizontal shift", "shift"),
        "function": horizontal_shift,
        "default": 10
    },
    "12": {
        "name": ("vertical shift", "vert shift"),
        "function": vertical_shift,
        "default": 10
    },
    
    
    "101": {
        "name": ("random", "rand"),
        "function": random_func,
        "default": 1
    }
}



def run_effect(query_parts, img):
    
    code = query_parts[0]
    
    if code not in REGISTRY:
        for key, effect in REGISTRY.items():
            if code.lower() in effect["name"]:
                code = key
                break
        else:
            raise ValueError(f"Unknown effect: {code}")
    effect = REGISTRY[code]
    defaults = effect["default"]
    
    if not isinstance(defaults, (list, tuple)):
        defaults = [defaults]
    
    amount = list(defaults)
    
    for i, param in enumerate(query_parts[1::]):
        if i >= len(amount):
            raise ValueError(f"Too many parameters. {effect["name"][0].upper()} takes only {len(amount)}.")
        if param != '':
            try:
                amount[i] = int(param)
            except ValueError:
                raise ValueError("Paramater must be number")
    
    result = effect["function"](img, *amount)
    
    return result, effect["name"][0]