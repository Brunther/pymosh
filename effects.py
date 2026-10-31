import random
import math
from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageFont, ImageDraw, ImageEnhance

#TODO: numpy optimization (?)
def random_func(img, iterations=1):
    from registry import REGISTRY
    randlist = [effect["function"] for effect in REGISTRY.values() if effect.get("allowsrandom") is not False]
    
    function = random.choice(randlist)
    image = function(img)
    returnstring = function.__name__
    
    if iterations > 1:
        funcname = [returnstring]
        prev = None
        for i in range(iterations - 1):
            choices = [f for f in randlist if f is not prev]
            function = random.choice(choices)
            
            prev = function
            
            image = function(image)
            
            if iterations <= 4:
                funcname.append(function.__name__)
        
        if iterations <= 4:
            returnstring = []
            for effect in REGISTRY.values():    
                for func in funcname:
                    if effect["function"].__name__ == func:
                        returnstring.append(effect["name"][0])
            returnstring = ', '.join(returnstring)
                        
        else:           
            returnstring = f"random x{iterations}"
            
    return image, returnstring

def rgb_split(img, shift_px=6):
    
    red, green, blue = img.split()
    
    red = ImageChops.offset(red, -shift_px, 0)
    blue = ImageChops.offset(blue, shift_px, 0)
    
    return Image.merge("RGB", (red, green, blue))

def vertical_rgb_split(img, shift_px=6):
    
    red, green, blue = img.split()
    
    red = ImageChops.offset(red, 0, shift_px)
    blue = ImageChops.offset(blue, 0, -shift_px)
    
    return Image.merge("RGB", (red, green, blue))
    
def blur(img, radius=3):
    return img.filter(ImageFilter.GaussianBlur(radius=radius))

def grayscale(img):
    return img.convert("L").convert("RGB")

def noise(img, amount=1, opacity=1):
    width, height = img.size
    
    rednoise = Image.effect_noise((width, height), amount * 100)
    greennoise = Image.effect_noise((width, height), amount * 100)
    bluenoise = Image.effect_noise((width, height), amount * 100)
    
    noiselayer = Image.merge("RGB", (rednoise, greennoise, bluenoise))
    return Image.blend(img.convert("RGB"), noiselayer, alpha=(opacity * 0.1))

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
        
        shift = random.randint(-max_shift, max_shift)
        
        shifted = ImageChops.offset(image, shift, 0)
        
        slice_crop = shifted.crop((0, y_start, width, y_end))
        
        image.paste(slice_crop, (0, y_start))
    
    return image

def horizontal_shift(img, offset=10):
    return ImageChops.offset(img, offset, 0)

def vertical_shift(img, offset=10):
    return ImageChops.offset(img, 0, offset)

def solarize(img, color_threshold=128):
    return ImageOps.solarize(img, color_threshold)

def pixelate(img, pixel_size=8):
    width, height = img.size
    
    small = img.resize(
        (max(1, width // pixel_size), max(1, height // pixel_size)),
        Image.Resampling.NEAREST
    )
    return small.resize((width, height), Image.Resampling.NEAREST)

def block_corrupt(img, num_blocks=12, max_size=50):
    image = img.convert("RGB")
    width, height = image.size
    result = image.copy()
    
    for i in range(num_blocks):
        w = random.randint(5, min(max_size, width))
        h = random.randint(5, min(max_size, height))
        
        sx = random.randint(0, width - w)
        sy = random.randint(0, height - h)
        dx = random.randint(0, width - w)
        dy = random.randint(0, height - h)
        
        block = image.crop((sx, sy, sx + w, sy + h))
        result.paste(block, (dx, dy))
    return result

def jitter(img, band_height=8, max_shift=30):
    image = img.convert("RGB")
    width, height = image.size
    result = image.copy()
    
    for y in range(0, height, band_height):
        bottom = min(y + band_height, height)
        band = image.crop((0, y, width, bottom))
        
        shift = random.randint(-max_shift, max_shift)
        band = ImageChops.offset(band, shift, 0)
        
        result.paste(band, (0, y))
        
    return result

def channel_shuffle(img):
    channels = list(img.convert("RGB").split())
    random.shuffle(channels)
    return Image.merge("RGB", channels)

def pixel_spread(img, distance=10):
    return img.effect_spread(distance)

def ascii(img, font_size=15):
    og = img.convert("RGB")
    
    og = ImageEnhance.Color(og).enhance(1.2)
    og = ImageEnhance.Brightness(og).enhance(1.4)
    
    gs = og.convert("L")
    
    chars = '@#$%&?+.*-/_^:`~'
    
    font = ImageFont.truetype("misc/ascii.ttf", font_size)
    
    width, height = img.size
    
    result = Image.new("RGB", (width, height), (15, 15, 15))
    draw = ImageDraw.Draw(result)
    
    bbox = draw.textbbox((0, 0), "A", font=font)
    char_width = draw.textlength("A", font=font)
    char_height = bbox[3] - bbox[1]
    
    
    for y in range(0, height, int(char_height)):
        for x in range(0, width, max(1, int(char_width))):
            
            brightness = gs.getpixel((x, y))
            color = og.getpixel((x, y))
            
            index = brightness * (len(chars) - 1) // 255

            char = chars[index]
            
            draw.text(
                (x, y),
                char,
                font=font,
                fill=color
            )
    return result

def refactor(img, resize_factor=2):
    width, height = img.size
    
    resize_factor = abs(resize_factor)
    
    if resize_factor in (0, 1):
            return img
    
    new_width = int(width * resize_factor)
    new_height = int(height * resize_factor)
    
    if resize_factor > 1:
        method = Image.Resampling.BICUBIC
    else:
        method = Image.Resampling.LANCZOS
        
    return img.resize((new_width, new_height), resample=method)

def resize(img, width=800, height=600):
    if 0 in (width, height):
        return img
    
    oldwidth, oldheight = img.size
    
    widthdif = oldwidth / width
    heightdif = oldheight / height
    
    if widthdif / heightdif >= width / height:
        method = Image.Resampling.BICUBIC
    else:
        method = Image.Resampling.LANCZOS
    
    
    return img.resize((width, height), resample=method)
    
def waves(img, amplitude=15, frequency=5):
    image = img.convert("RGB")
    width, height = image.size
    
    result = Image.new("RGB", image.size)
    
    for y in range(height):
        offset = int(math.sin(y * frequency * 0.01) * amplitude)
        
        row = image.crop((0, y, width, y + 1))
        result.paste(ImageChops.offset(row, offset, 0), (0, y))
    return result

def halftones(img, dot_size=8, max_radius=5):
    gray = img.convert("L")
    width, height = img.size
    
    result = Image.new("RGB", img.size, (255, 255, 255))
    draw = ImageDraw.Draw(result)
    
    for y in range(0, height, dot_size):
        for x in range(0, width, dot_size):
            
            brightness = gray.getpixel((
                min(x + dot_size // 2, width - 1),
                min(y + dot_size // 2, height - 1)
            ))

            radius = (1 - brightness / 255) * max_radius
            
            if radius < 0.5:
                continue
            
            color = img.getpixel((
                min(x + dot_size // 2, width - 1),
                min(y + dot_size // 2, height - 1)
            ))
            
            center_x = x + dot_size // 2
            center_y = y + dot_size // 2
            
            draw.ellipse(
                (
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius
                ),
                fill=color
            )
    return result