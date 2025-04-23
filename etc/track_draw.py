from PIL import Image

def change_color(img, old_color, new_color):
    
    # Get the pixels
    pixels = img.load()
    
    # Get the size of the image
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            
            # Check if the pixel matches the old color (with tolerance for minor variations)
            if pixel[:3] == old_color:  # Assuming 'old_color' is a tuple like (R, G, B)
                pixels[x, y] = new_color + (pixel[3],)  # Preserve the original alpha (transparency)
    
    # Save the modified image
    return img

def prepare_map(trains,colormap):
    """
    the trains is a dict! {trains_color:position:int} colors are in (R,g,b) format
    return a PIL image"""
    img = Image.open(image_path)
    # Convert image to RGBA if it's not already
    img = img.convert('RGBA')
    for pos,color in colormap.items():
        if not pos in trains.values():
            img=change_color(img,color,new_color)
        else:
            trainscolor=next((k for k, v in trains.items() if v == pos), None)
            img=change_color(img,color,trainscolor)
    

    #write the img
    return img
    


new_color = (0, 0, 0)  # Green color in RGB
image_path = "track.png"


