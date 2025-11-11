from PIL import Image
import os


def rewrite_area_sr(sr_path: str,
                    sr_temp_path: str,
                    navmesh_bmp: str,
                    location_key: int):
    '''Rewrite area image which contains walkable zones information
    It use black-white image to define walkable zones in the area map

    Input:
        sr_path - full path to ...SR.bmp file
        sr_temp_path - full path the the temp file
        navmesh_bmp - full path to bmp file with navigation information
        location_key - integer with ground type (4 for the stone, for example)
    '''
    def clamp(value: int, min_value: int, max_value: int) -> int:
        if value < min_value:
            return min_value
        elif value > max_value:
            return max_value
        return value

    navmesh_img = Image.open(navmesh_bmp)
    navmesh_width = navmesh_img.width
    navmesh_height = navmesh_img.height
    
    area_img = Image.open(sr_path)
    width = area_img.width
    height = area_img.height
    x_size = 1.0 / width
    y_size = 1.0 / height
    for y in range(height):
        for x in range(width):
            x_pos = x * x_size + x_size / 2.0
            y_pos = y * y_size + y_size / 2.0
            # select pixel from navmesh image
            nm_x = clamp(int(x_pos * navmesh_width), 0, navmesh_width - 1)
            nm_y = clamp(int(y_pos * navmesh_height) + 50, 0, navmesh_height - 1)
            navmesh_pixel = navmesh_img.getpixel((nm_x, nm_y))
            if navmesh_pixel[0] >= 128:
                area_img.putpixel((x, y), location_key)
            else:
                area_img.putpixel((x, y), 0)
    area_img.save(sr_temp_path)


def build_searchmap(override_directory: str,
                    area_name: str,
                    navmesh_bmp: str,
                    location_key: int):
    '''Rewrite area image which contains walkable zones information
    It use black-white image to define walkable zones in the area map

    Inputs:
        override_directory - full path to override directory
        area_name - name of the area
        navmesh_bmp - full path to bmp file with navigation information
        location_key - integer with ground type (4 for the stone, for example)
    '''
    sr_path = override_directory + area_name + "SR.BMP"
    sr_temp_path = override_directory + area_name + "SR_temp.BMP"
    rewrite_area_sr(sr_path, sr_temp_path, navmesh_bmp, location_key)
    os.remove(sr_path)
    os.rename(sr_temp_path, sr_path)
