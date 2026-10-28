from effects import *

REGISTRY = {
    "1": {
        "name": ("rgb split", "rgb"),
        "function": rgb_split,
        "default": 10
    },
    "2": {
        "name": ("gaussian blur", "blur"),
        "function": blur,
        "default": 5
    },
    "3": {
        "name": ("grayscale", "gs"),
        "function": grayscale,
        "default": 1
    }
}

#TODO: allow code input to have multiple parameters (ie 2:10:10)


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
            amount = int(query_parts[1].strip())
        except ValueError:
            raise ValueError("Paramater must be number")
    else:
        amount = effect["default"]
    
    result = effect["function"](img, amount)
    
    return result, effect["name"][0]