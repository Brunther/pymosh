
from PIL import Image, ImageChops, ImageFilter


def rgb_split(img, shift):
    
    red, green, blue = img.split()
    
    red = ImageChops.offset(red, -shift, 0)
    blue = ImageChops.offset(blue, -shift, 0)
   # print("Ran RGB Split")
    
    return Image.merge("RGB", (red, green, blue))

def blur(img, rad):
    return img.filter(ImageFilter.GaussianBlur(radius=rad))

def grayscale(img, amount):
    return img.convert("L").convert("RGB")

