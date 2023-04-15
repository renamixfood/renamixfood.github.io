import os
from jinja2 import Environment, FileSystemLoader
from collections import namedtuple
from PIL import Image, ImageOps
import re

def extract_dish_data(root_folder):
    dish_data = {}
    for category in os.listdir(root_folder):
        category_path = os.path.join(root_folder, category)
        if os.path.isdir(category_path):
            dish_data[category] = []
            for image_file in os.listdir(category_path):
                if image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) and not 'thumb' in image_file:
                    dish_data[category].append(image_file)

    return dish_data

def create_thumbnail(image_path, thumbnail_width=300, thumbnail_height=200, exact=True):
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)

    if exact:
        # Crop image to desired aspect ratio
        aspect_ratio = thumbnail_width / thumbnail_height
        img_width, img_height = img.size
        img_aspect_ratio = img_width / img_height
        if img_aspect_ratio <= aspect_ratio:
            new_width = img_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = img_height
            new_width = int(new_height * aspect_ratio)

        left = (img_width - new_width) // 2
        top = (img_height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        img = img.crop((left, top, right, bottom))

        # Resize the image to the desired thumbnail size
        img.thumbnail((thumbnail_width, thumbnail_height))
    else:
        img.thumbnail((thumbnail_width, thumbnail_height))

    thumbnail_path = os.path.splitext(image_path)[0] + "_thumb" + os.path.splitext(image_path)[1]
    img.save(thumbnail_path)

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")) and not "thumb" in file:
                image_path = os.path.join(root, file)
                create_thumbnail(image_path)

root_folder = 'menu'

process_directory(root_folder)
dish_data_raw = extract_dish_data(root_folder)

print(dish_data_raw)

Dish = namedtuple('Dish', ['name', 'price', 'descr', 'image', 'thumb'])

dish_data = {}

for category, files in sorted(dish_data_raw.items(), key=lambda x: x[0]):
    dish_data[category] = []

    for file in files:
        # extract the stuff between brackets from the filename using a regex
        cleaned = file.replace(',', ', ').replace(',  ', ', ').replace('( ', '(').replace('(', ' (').replace('  (', ' (')
        name, price = cleaned.rsplit('-', 1)
        name = name.capitalize()
        name,descr = (name.split('(') + [''])[0:2]
        name = name.replace("gedroogde fruit", "gedroogd fruit")
        descr = descr.replace(')', '')
        price = price.replace('€', '')
        price = price.strip().rsplit('.', 1)[0]
        # replace point with comma if preceded by a number
        price = re.sub(r'(\d)\.(\d)', r'\1,\2', price)
        image = f'menu/{category}/{file}'
        thumb = os.path.splitext(image)[0] + "_thumb" + os.path.splitext(image)[1]
        dish_data[category].append(Dish(name.strip(), price, descr, image, thumb))

print(dish_data)

import time

last_modified = 0

templatefile = 'template.html'

while True:
    current_modified = os.path.getmtime(templatefile)
    print(current_modified, last_modified)
    if current_modified == last_modified:
        time.sleep(1)
        continue

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(templatefile)
    output = template.render(dish_data=dish_data)

    with open('index.html', 'w') as f:
        f.write(output)

    last_modified = current_modified
    print("index.html generated successfully")