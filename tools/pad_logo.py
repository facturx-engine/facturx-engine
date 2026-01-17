from PIL import Image
import os

def add_padding(input_path, output_path, padding_factor=1.05):
    # Load image
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    
    # Calculate new size (Square + Padding)
    max_dim = max(width, height)
    new_size = int(max_dim * padding_factor)
    
    # Create new blank white image
    # For Lemon Squeezy, white background is safer than transparent for logos
    background = Image.new('RGB', (new_size, new_size), (255, 255, 255))
    
    # Calculate centering position
    x = (new_size - width) // 2
    y = (new_size - height) // 2
    
    # Paste original
    background.paste(img, (x, y), img)
    
    # Save
    background.save(output_path)
    print(f"✅ Saved padded logo to: {output_path} ({new_size}x{new_size})")

if __name__ == "__main__":
    if not os.path.exists("marketing_assets/logo.png"):
        print("Error: marketing_assets/logo.png not found")
    else:
        add_padding("marketing_assets/logo.png", "marketing_assets/logo_circular_safe.png")
