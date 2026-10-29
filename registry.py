from effects import *

REGISTRY = {
    "1": {
        "name": ("horizontal rgb split", "rgb split", "horizontal rgb", "hor rgb", "hor", "rgb"),
        "function": rgb_split,
        "default": 10,
        "description": "Splits image into red, green, & blue layers, then shifts them horizontally. Parameter increases shift amount."
    },
    "2": {
        "name": ("vertical rgb split", "vertical rgb", "vert rgb", "vert split"),
        "function": vertical_rgb_split,
        "default": 10,
        "description": "Splits image into red, green, & blue layers, then shifts them vertically. Parameter increases shift amount."
    },
    "3": {
        "name": ("gaussian blur", "blur"),
        "function": blur,
        "default": 3,
        "description": "Blurs image by a factor of first parameter."
    },
    "4": {
        "name": ("noise", "ns"),
        "function": noise,
        "default": (1, 1),
        "description": "Adds noise to image. Parameter 1 increases amount of noise, parameter 2 increases opacity."
    },
    "5": {
        "name": ("slice", "slc"),
        "function": slice_glitch,
        "default": (10, 30),
        "description": "Seperates random portions of image into unequal horizontal slices and shifts them. Parameter 1 increases number of slices, parameter 2 increases max amount of shift."
    },
    "6": {
        "name": ("jitter", "jit"),
        "function": jitter,
        "default": (8, 30),
        "description": "Seperates entire image into equal horizontal bands and shifts them. Parameter 1 increases height of each band, parameter 2 increases max amount of shift."
    },
    "7": {
        "name": ("posterize", "poster"),
        "function": posterize,
        "default": 3,
        "description": "Reduces bit depth of image by parameter. Must be between 1 and 8."
    },
    "8": {
        "name": ("solarize", "solar"),
        "function": solarize,
        "default": 128,
        "description": "Inverts pixels in image with color values above parameter. Must be between 0 and 255."
    },
    "9": {
        "name": ("pixelate", "resample", "pixel"),
        "function": pixelate,
        "default": 8,
        "description": "pixelates image by a factor of parameter. Uses nearest neighbor sampling"
    
    },
    "10": {
        "name": ("block corrupt", "corrupt"),
        "function": block_corrupt,
        "default": (12, 50),
        "description": "Copies random portions of image to random positions. Parameter 1 increases number of portions. Parameter 2 increases max size of portion."
    },
    "11": {
        "name": ("grayscale", "gs"),
        "function": grayscale,
        "description": "Converts image to grayscale."
    },
    "12": {
        "name": ("horizontal shift", "shift"),
        "function": horizontal_shift,
        "default": 10,
        "description": "Shifts image horizontally. Parameter increases how far the image shifts."
    },
    "13": {
        "name": ("vertical shift", "vert shift"),
        "function": vertical_shift,
        "default": 10,
        "description": "Shifts image vertically. Parameter increases how far the image shifts."
    },
    "14": {
        "name": ("channel shuffle", "cshuffle", "shuffle"),
        "function": channel_shuffle,
        "description": "Seperates RGB color channels of image and randomly shuffles them."
    },
    
    "101": {
        "name": ("random", "rand", "randy"),
        "function": random_func,
        "default": 1,
        "description": "Applies a random effect (with default values) to image. Parameter increases number of effects to apply"
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
    
    defaults = effect.get("default", None)
    
    if defaults is None:
        amount = []
    elif isinstance(defaults, (list, tuple)):
        amount = list(defaults)
    else:
        amount = [defaults]
    
    for i, param in enumerate(query_parts[1::]):
        if i >= len(amount):
            raise ValueError(f"Too many parameters. {effect['name'][0].upper()} takes only {len(amount)}.")
        if param != '':
            try:
                amount[i] = int(param)
            except ValueError:
                raise ValueError("Parameter must be number")
    result = effect["function"](img, *amount) if amount else effect["function"](img)
    
    return result, effect["name"][0]