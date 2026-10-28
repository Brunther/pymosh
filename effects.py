import random

from PIL import Image, ImageChops, ImageFilter, ImageOps


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

def randomfunc(img, iterations):
    randlist = [rgb_split, vertical_rgb_split, blur, noise, posterize, slice_glitch] ##excluding grayscale for obvious reasons
    
    function = random.choice(randlist)
    image = function(img)
    if iterations > 1:
        for i in range(iterations):
            function = random.choice(randlist)
            image = function(image)
    return image

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