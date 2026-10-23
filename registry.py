from effects import *

REGISTRY = {
    "1": {
        "name": "RGB Split",
        "function": rgb_split,
        "default": 10
    },
    "2": {
        "name": "Scanlines",
        "function": scanlines,
        "default": 15
    }
}

#TODO: allow code input to have multiple parameters (ie 2:10:10)


def run_effect(query, img):
    query = query.strip().lower()
    
    parts = query.split(":", 1)
    code = parts[0].strip()
    
    if code not in REGISTRY:
        for key, effect in REGISTRY.items():
            if code == effect["name"].lower():
                code = key
                break
        else:
            raise ValueError(f"Unkown effect: {code}")
    effect = REGISTRY[code]
        
    if len(parts) > 1:
        try:
            amount = int(parts[1].strip())
        except ValueError:
            raise ValueError("Paramater must be number")
    else:
        amount = effect["default"]
    
    result = effect["function"](img, amount)
    
    return result, effect["name"]