import os
from PIL import Image, ImageFont, ImageDraw
from bam_io import bam_to_file
from bam_io.bamv2 import BamV2, Frame, TextureFormat
from tool_gen_bams import helper_find_prefix 
from infinity.bam_composer import BAMComposer
from infinity import stream

def generate_font_bam(output_directory: str,
                      output_bam: str,
                      font_path: str,
                      font_size: int,
                      space_size: int = 4,
                      kerning: int = 1,
                      margin: int = 1,
                      bam_version: int = 1):
    '''Create bam-file with font glyphs fo using it as raster font
    Create english and russian glyphs, should be used with texts encoded in cp1251 
    Use infinity python module from GemRB developers, because it allows to store bam in V1 format

    Input:
        output_directory - full path to the override directory
        output_bam - name of the output file, without bam extension
        font_path - full path to the ttf-font file
        font_size - size of the font
        space_size - size  (in pixels) of the space glyph
        kerning - distance (in pixels) between letter in the text
        margin - size (in pixels) of empty space above all glyphs
        bam_version - set 1 for V1, 2 (or any other) for V2
    '''
    def differ_from_white(pixel: tuple[int, int, int, int]):
        return pixel[0] != 255 or pixel[1] != 255 or pixel[2] != 255

    font = ImageFont.truetype(font_path, font_size)
    width = font_size * 3
    height = font_size * 3

    ids: list[int | None] = [None for i in range(0, 31)]
    # at start skip 0-30
    # 31 is a space
    ids.append(None)
    symbols = "!\"#%$&'()*+,-./"  # may be , should be at another place, 32-46
    ids += [i for i in range(32, 47)]
    symbols += "0123456789:;<=>?@"  # 47-63
    ids += [i for i in range(47, 64)]
    symbols += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 64-89
    ids += [i for i in range(64, 90)]
    symbols += "[\\]^_'"  # may be here, 90-95
    ids += [i for i in range(90, 96)]
    symbols += "abcdefghijklmnopqrstuvwxyz"  # 96-121
    ids += [i for i in range(96, 122)]
    symbols += "{|}~"  # 122, 123, 124, 125
    ids += [122, 123, 124, 125]
    ids += [None for i in range(126, 170)]
    symbols += "«"  # 170
    ids += [170]
    ids += [None for i in range(171, 186)]
    symbols += "»"  # 186
    ids += [186]
    ids += [None for i in range(187, 191)]
    symbols += "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"  # 191-222
    ids += [i for i in range(191, 223)]
    symbols += "абвгдежзийклмнопрстуфхцчшщъыьэюя"  # 223-254
    ids += [i for i in range(223, 255)]
    symbol_iterator = 0
    glyph_imgs: list[Image.Image | None] = []
    for i in range(len(ids)):
        id_value = ids[i]
        if id_value is None:
            glyph_imgs.append(None)
            continue

        s = symbols[symbol_iterator]
        symbol_iterator += 1
        if s.isprintable():
            img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
            img_draw = ImageDraw.Draw(img)
            _, _, w, h = img_draw.textbbox((0, 0), s, font=font)
            new_width = int(w)
            img = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))
            img_draw = ImageDraw.Draw(img)
            img_draw.text((0, 0), s, fill=(0, 0, 0), font=font)
            glyph_imgs.append(img)

    glyph_sizes_aray = []  # key is index, value is a bounding box
    symbol_iterator = 0
    for img in glyph_imgs:
        if img is None:
            continue
        pixels = list(img.getdata())
        img_width, img_height = img.size
        min_x = img_width + 1
        min_y = img_height + 1
        max_x = -1
        max_y = -1
        for y in range(img_height):
            for x in range(img_width):
                p = pixels[y * img_height + x]
                if differ_from_white(p):
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
                    if y < min_y:
                        min_y = y
                    if y > max_y:
                        max_y = y
                else:
                    img.putpixel((x, y), (0, 0, 0, 0))
        # the non-empty pixels between min/max_x and min/max_y
        glyph_sizes_aray.append((min_x, max_x, min_y, max_y))
    total_y_min = 9999
    total_y_max = -1
    for size in glyph_sizes_aray:
        if size[2] < total_y_min:
            total_y_min = size[2]
        if size[3] > total_y_max:
            total_y_max = size[3]
    index = 0
    croped_images: list[Image.Image | None] = []
    for img in glyph_imgs:
        if img is None:
            croped_images.append(None)
            continue
        size = glyph_sizes_aray[index]
        img_crop = img.crop((size[0], total_y_min - margin, size[1] + 1 + kerning, total_y_max + 1))
        croped_images.append(img_crop)
        index += 1
    # create empty image
    images_height = total_y_max - total_y_min + 1 + margin
    empty_img = Image.new("RGBA", (font_size, images_height))
    empty_draw = ImageDraw.Draw(empty_img)  
    empty_draw.rectangle([(0, margin), (font_size - kerning - 1, total_y_max - total_y_min)], fill ="black")
    space_img = Image.new("RGBA", (space_size, images_height), (0, 0, 0, 0))

    if bam_version == 1:
        # use infinity module to save bam V1
        composer = BAMComposer()
        # at first add frame for empty glyph
        composer.frames.append({
            "name": "empty",
            "transparent": "1",
            "x": empty_img.width // 2,
            "y": empty_img.height,
            "image": empty_img
        })        
        composer.names["empty"] = 0
        frame_index = 1
        for img_index, img in enumerate(croped_images):
            if img_index == 31:
                # space symbol
                composer.frames.append({
                    "name": "space",
                    "transparent": "1",
                    "x": space_img.width // 2,
                    "y": space_img.height,
                    "image": space_img
                })
                composer.names["space"] = frame_index
                frame_index += 1
                composer.cycle_lines.append((str(img_index), ["space"])) 
            else:
                if img is None:
                    # add empty glyph
                    composer.cycle_lines.append((str(img_index), ["empty"])) 
                else:
                    composer.frames.append({
                        "name": str(img_index),
                        "transparent": "1",
                        "x": img.width // 2,
                        "y": img.height,
                        "image": img
                    })
                    composer.names[str(img_index)] = frame_index
                    frame_index += 1
                    composer.cycle_lines.append((str(img_index), [str(img_index)])) 

        composer.palette_file = "auto"

        bam = composer.create_bam()
        out_stream = stream.FileStream().open(output_directory + output_bam + ".bam", "wb")  
        bam.write(out_stream)
        out_stream.close()
    else:
        # store output in bam V2
        font_bam = BamV2()
        # add frame for empty glyph
        empty_frame = Frame(empty_img.width, empty_img.height, empty_img.width // 2, empty_img.height)
        empty_frame.set_image(empty_img)
        empty_frame_idx = font_bam.add_frame(empty_frame)
        for img_index, img in enumerate(croped_images):
            if img_index == 31:
                # this is the space
                cycle_index = font_bam.add_cycle()
                frame = Frame(space_size, images_height, space_size // 2, images_height)
                frame.set_image(space_img)
                frame_index = font_bam.add_frame(frame)
                font_bam.add_frame_to_cycle(cycle_index, frame_index)
            else:
                if img is None:
                    # for None image add to the bam empty frame
                    cycle_index = font_bam.add_cycle()
                    font_bam.add_frame_to_cycle(cycle_index, empty_frame_idx)
                else:
                    cycle_index = font_bam.add_cycle()
                    frame = Frame(img.width, img.height, img.width // 2, img.height)
                    frame.set_image(img)
                    frame_index = font_bam.add_frame(frame)
                    font_bam.add_frame_to_cycle(cycle_index, frame_index)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        bam_to_file(font_bam, output_directory + output_bam + ".bam", helper_find_prefix(output_directory), TextureFormat.DXT5)
