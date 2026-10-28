from effects import *

REGISTRY = {
    "1": {
        "name": ("horizontal rgb split", "rgb split", "horizontal rgb", "hor rgb", "hor"),
        "function": rgb_split,
        "default": (10,)
    },
    "2": {
        "name": ("vertical rgb split", "vertical rgb", "vert rgb", "vert"),
        "function": vertical_rgb_split,
        "default": (10,)
    },
    "3": {
        "name": ("gaussian blur", "blur"),
        "function": blur,
        "default": (3,)
    },
    "4": {
        "name": ("noise", "ns"),
        "function": noise,
        "default": (1,)
    },
    "5": {
        "name": ("slice", "slc"),
        "function": slice_glitch,
        "default": (10, 30)
    },
    "6": {
        "name": ("posterize", "poster"),
        "function": posterize,
        "default": (3,) 
    },
    "9": {
        "name": ("grayscale", "gs"),
        "function": grayscale,
        "default": (None,)
    },
    
    "101": {
        "name": ("random", "rand"),
        "function": randomfunc,
        "default": (1,)
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
        
    if len(query_parts) > 1:
        try:
            amount = (int(i) for i in query_parts[1::])
        except ValueError:
            raise ValueError("Paramater must be number")
    else:
        amount = effect["default"]
        
    result = effect["function"](img, *amount)
    
    return result, effect["name"][0]