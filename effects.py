from PIL import Image, ImageChops, ImageDraw

def rgb_split(img, shift):
    
    red, green, blue = img.split()
    
    red = ImageChops.offset(red, -shift, 0)
    blue = ImageChops.offset(blue, -shift, 0)
    
    return Image.merge("RGB", (red, green, blue))

def scanlines(img, line_gap, opacity=100, line_thickness=3):
    
    img_rgba = img.convert("RGBA")
    overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(0, img_rgba.height, line_gap):
        draw.line([(0, y), (img_rgba.width, y)], fill=(0, 0, 0, opacity), width=line_thickness)
        
        result = Image.alpha_composite(img_rgba, overlay)
    return result.convert("RGB")