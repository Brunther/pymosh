import random

from PIL import Image, ImageChops, ImageFilter, ImageOps


def random_func(img, iterations):
    randlist = [rgb_split, vertical_rgb_split, blur, noise, posterize, slice_glitch, horizontal_shift, vertical_shift, solarize, pixelate, block_corrupt] ##excluding grayscale for obvious reasons
    
    function = random.choice(randlist)
    image = function(img)
    if iterations > 1:
        for i in range(iterations - 1):
            function = random.choice(randlist)
            image = function(image)
    return image

def rgb_split(img, shift=10):
    
    red, green, blue = img.split()
    
    red = ImageChops.offset(red, -shift, 0)
    blue = ImageChops.offset(blue, shift, 0)
    
    return Image.merge("RGB", (red, green, blue))

def vertical_rgb_split(img, shift=10):
    
    red, green, blue = img.split()
    
    red = ImageChops.offset(red, 0, shift)
    blue = ImageChops.offset(blue, 0, -shift)
    
    return Image.merge("RGB", (red, green, blue))
    
def blur(img, rad=3):
    return img.filter(ImageFilter.GaussianBlur(radius=rad))

def grayscale(img, amount=None):
    return img.convert("L").convert("RGB")

def noise(img, amount=1):
    width, height = img.size
    
    noiselayer = Image.effect_noise((width, height), amount * 100).convert("RGB")
    return Image.blend(img, noiselayer, alpha=0.1)

def posterize(img, bits=3):
    if not 1 <= bits <= 8:
        raise ValueError("Posterize must be between 1 and 8")
    return ImageOps.posterize(img, bits).convert("RGB")

def slice_glitch(img, num_slices=10, max_shift=30):
    image = img.copy()
    width, height = image.size
    for i in range(num_slices):
        y_start = random.randint(0, height - 20)
        y_end = min((y_start + random.randint(5, 40)), height)
        
        box = (0, y_start, width, y_end)
        slice_crop = image.crop(box)
        
        shift = random.randint(-max_shift, max_shift)
        
        image.paste(slice_crop, (shift, y_start))
    
    return image

def horizontal_shift(img, offset=10):
    return ImageChops.offset(img, offset, 0)

def vertical_shift(img, offset=10):
    return ImageChops.offset(img, 0, offset)

def solarize(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def pixelate(img, block_size=8):
    width, height = img.size
    
    small = img.resize(
        (max(1, width // block_size), max(1, height // block_size)),
        Image.Resampling.NEAREST
    )
    return small.resize((width, height), Image.Resampling.NEAREST)

def block_corrupt(img, blocks=12, max_size=50):
    image = img.convert("RGB")
    result = image.copy()
    width, height = image.size
    
    for i in range(blocks):
        w = random.randint(5, min(max_size, width))
        h = random.randint(5, min(max_size, height))
        
        sx = random.randint(0, width - w)
        sy = random.randint(0, height - h)
        dx = random.randint(0, width - w)
        dy = random.randint(0, height - h)
        
        block = image.crop((sx, sy, sx + w, sy + h))
        result.paste(block, (dx, dy))
    return result