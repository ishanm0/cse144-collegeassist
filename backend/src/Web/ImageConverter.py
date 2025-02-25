import os

from PIL import Image


class ImageConverter:
    def __init__(self, directory_path: str, new_size: tuple):
        self.directory_path = directory_path
        self.new_size = new_size

    def convert_images(self):
        for filename in os.listdir(self.directory_path):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                original_path = os.path.join(self.directory_path, filename)
                webp_path = os.path.join(self.directory_path, os.path.splitext(filename)[0] + ".webp")

                with Image.open(original_path) as img:
                    resized_img = img.resize(self.new_size, Image.Resampling.LANCZOS)
                    resized_img.save(webp_path, "WEBP")

                os.remove(original_path)
                print(f"Converted, resized, and replaced: {filename} to " f"{os.path.basename(webp_path)}")
