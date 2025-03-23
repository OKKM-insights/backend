import numpy as np

import io
from PIL import Image

import mysql.connector

# Config
# ------------------------------------------------------------  
OBJECTSIZE = 32 #m - Size of the object in meters (max dimension)
RESOLUTION = 2 #pixels per meter (resolution of satalite image)
OBJECTSINFRAME = 5 #number of objects that fit in the frame

PIXELSIZE = OBJECTSIZE * RESOLUTION #pixels the object takes up in image
FRAMEPIXELSIZE = PIXELSIZE * OBJECTSINFRAME #pixels per meter
# ------------------------------------------------------------  

def preprocess_image(image_np: np.ndarray) -> list[dict]:

    tiles = []
    img_height, img_width = image_np.shape[:2] #width and height

    def get_positions(total_size, frame_size):
        positions = list(range(0, total_size - frame_size + 1, frame_size))
        if total_size - positions[-1] > 0:  # if there's remaining space
            positions.append(total_size - frame_size)  # overlap with previous grid
        return positions

    x_positions = get_positions(img_width, FRAMEPIXELSIZE)
    y_positions = get_positions(img_height, FRAMEPIXELSIZE)

    for y_offset in y_positions:
        for x_offset in x_positions:
            # Core frame coordinates
            x_end = x_offset + FRAMEPIXELSIZE
            y_end = y_offset + FRAMEPIXELSIZE
            
            # Buffer zone coordinates
            x_buff_start = max(0, x_offset - PIXELSIZE)
            y_buff_start = max(0, y_offset - PIXELSIZE)
            x_buff_end = min(img_width, x_end + PIXELSIZE)
            y_buff_end = min(img_height, y_end + PIXELSIZE)
            
            full_tile = image_np[y_buff_start:y_buff_end, x_buff_start:x_buff_end].copy()
            
            # relative positions for core area in the buffered tile
            core_start_y = y_offset - y_buff_start
            core_start_x = x_offset - x_buff_start
            core_end_y = core_start_y + FRAMEPIXELSIZE
            core_end_x = core_start_x + FRAMEPIXELSIZE
            

            overlay = np.ones_like(full_tile) * [255, 100, 100] 
            mask = np.ones_like(full_tile, dtype=bool)
            mask[core_start_y:core_end_y, core_start_x:core_end_x] = False
            full_tile[mask] = full_tile[mask] * 0.5 + overlay[mask] * 0.5
            
            tiles.append({
                'tile': full_tile,
                'x_offset': x_buff_start,
                'y_offset': y_buff_start,
                'core_start': (core_start_x, core_start_y),
                'core_size': FRAMEPIXELSIZE,
                'width': x_buff_end - x_buff_start,
                'height': y_buff_end - y_buff_start
            })

    return tiles

def store_tiles(tiles: list[dict], project_id: str, original_image_id: str, cursor: mysql.connector.cursor.MySQLCursor) -> None:

    for tile_data in tiles:
        # Convert numpy array back to PIL Image
        tile_img = Image.fromarray(tile_data['tile'].astype('uint8'))
        
        img_byte_arr = io.BytesIO()
        tile_img.save(img_byte_arr, format='PNG')
        img_blob = img_byte_arr.getvalue()

        height, width = tile_data['tile'].shape[:2]

        insert_tile_query = """
            INSERT INTO Images (project_id, orig_image_id, image_width, image_height, x_offset, y_offset, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_tile_query, 
            (
                project_id,
                original_image_id,
                width,
                height,
                tile_data['x_offset'],
                tile_data['y_offset'],
                img_blob
            )
        )