from PIL import Image
import struct
import os
import zlib
import subprocess
from bam_io.bamv2 import BamV2, TextureFormat


def save_image_to_pvrz(directory: str, pvrz_prefix: int, pvrz_idx: int, image: Image.Image, txt_format: TextureFormat):
    # save each image as dds with DXT1/5 format
    # use texconv utility
    # at first we save the image in png, and then convert it to dds by the utility
    # WARNING: built-in dds in PIL save it with too deformed colors
    number_length = 3
    png_temp_file = directory + "/" + "temp_" + str(pvrz_prefix) + ("0"*number_length)[:number_length-len(str(pvrz_idx))] + str(pvrz_idx) + ".png"
    ddt_temp_file = directory + "/" + "temp_" + str(pvrz_prefix) + ("0"*number_length)[:number_length-len(str(pvrz_idx))] + str(pvrz_idx) + ".dds"
    image.save(png_temp_file)
    # next convert to dds by using texconv.exe
    command = [os.path.dirname(os.path.realpath(__file__)) + "/texconv.exe",
               "-f", "DXT1" if txt_format == TextureFormat.DXT1 else "DXT5",
               "-o", os.path.dirname(png_temp_file) + "/",
               "-y", png_temp_file]
    cmd_result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    pvrz_file = directory + "/" + "MOS" + str(pvrz_prefix) + ("0"*number_length)[:number_length-len(str(pvrz_idx))] + str(pvrz_idx) + ".pvrz"
    with open(ddt_temp_file, "rb") as dds_file:
        dds_bytes = dds_file.read()
        # skip dds header 128 bytes
        dds_code = dds_bytes[128:]
        # dds_code contains encoded image
        # next we should create pvr-file header and attach this coded data to it
        pvrz_bytes = bytearray()
        # add pvrz header
        pvrz_bytes.extend(bytearray([0x50, 0x56, 0x52, 0x03]))
        # flag
        pvrz_bytes.extend(struct.pack("I", 0))
        # pixel format
        pvrz_bytes.extend(struct.pack("Q", 7 if txt_format == TextureFormat.DXT1 else 11))
        # color space
        pvrz_bytes.extend(struct.pack("I", 0))
        # channel type
        pvrz_bytes.extend(struct.pack("I", 0))
        # height
        pvrz_bytes.extend(struct.pack("I", image.height))
        # width
        pvrz_bytes.extend(struct.pack("I", image.width))
        # texture depth
        pvrz_bytes.extend(struct.pack("I", 1))
        # num surfaces
        pvrz_bytes.extend(struct.pack("I", 1))
        # num faces
        pvrz_bytes.extend(struct.pack("I", 1))
        # num mip maps
        pvrz_bytes.extend(struct.pack("I", 1))
        # meta size
        pvrz_bytes.extend(struct.pack("I", 0))

        # next attach decoded data
        pvrz_bytes.extend(dds_code)
        # next zip this set of bytes
        pvrz_compressed = zlib.compress(pvrz_bytes)

        # create final pvrz bytes
        pvrz_final = bytearray()
        pvrz_final.extend(struct.pack("I", len(pvrz_bytes)))
        pvrz_final.extend(pvrz_compressed)

        # store the file
        with open(pvrz_file, "wb") as out_file:
            out_file.write(pvrz_final)
    # remove temp dds file
    os.remove(png_temp_file)
    os.remove(ddt_temp_file)


def export_bam_pvrz(bam: BamV2, directory: str, pvrz_prefix: int, txt_format: TextureFormat) -> list[list[tuple[int, int, int, int, int, int, int]]]:
    '''this function pack images from all frames into several pvrz files

    return array, i-th element of the array contains data for the i-th frame
    each data is array of data blocks, it contains pvrz index, src coordinates, fragment size, dst coordinates (for one block per frame always = 0, 0)
    '''
    def modulo_value(value: int, m: int) -> int:
        return ((0 if value % m == 0 else 1) + value // m) * m

    to_return = []
    pvrz_index = 0
    # this is an image to store pixels of the frames
    image_max_width = 1024
    image_max_height = 1024
    pvrz_images = []  # store here all builded images, and also both right and bottom lines
    pvrz_image = Image.new("RGBA", (image_max_width, image_max_height))
    # these borders indicate filled area in the image
    top_border = 0
    left_border = 0
    max_left_border = 0
    row_height = 0  # here we increase the height of the row - sequence of images at the same top level
    for frame_index in range(bam.get_frames_count()):
        # here for each frame we create only one data block
        # but potentially each frame can refer to several parts of the image inside pvrz pages
        # so, crate frame data as array, but l store only one value
        frame_data = []
        # at frame data store the tuple (page index, src x, src y, width, height, target x, target y)
        frame = bam.get_frame(frame_index)
        width = frame.get_width()
        height = frame.get_height()
        image = frame.get_image()
        if image and left_border + width < image_max_width and top_border + height < image_max_height:
            # insert frame image inside pvrz page
            pvrz_image.paste(image, (left_border, top_border))
            frame_data.append((pvrz_index, left_border, top_border, width, height, 0, 0))
            left_border += modulo_value(width, 4)
            max_left_border = max(max_left_border, left_border)
            row_height = max(row_height, height)
        else:
            # try to insert the image below the line
            top_border += modulo_value(row_height, 4)
            left_border = 0
            row_height = 0
            if image and left_border + width < image_max_width and top_border + height < image_max_height:
                # again insert the image
                pvrz_image.paste(image, (left_border, top_border))
                frame_data.append((pvrz_index, left_border, top_border, width, height, 0, 0))
                left_border += modulo_value(width, 4)
                max_left_border = max(max_left_border, left_border)
                row_height = max(row_height, height)
            else:
                # this image can not be inserted inside current page
                # we should create new page and insert image to it
                if top_border > 0 or left_border > 0:
                    # create new image only if it is not new image
                    pvrz_images.append((pvrz_image, max_left_border, modulo_value(top_border + row_height, 4)))
                    pvrz_index += 1
                    pvrz_image = Image.new("RGBA", (image_max_width, image_max_height))
                    top_border = 0
                    left_border = 0
                    row_height = 0
                    max_left_border = 0
                if image:
                    pvrz_image.paste(image, (left_border, top_border))
                    if image.width + left_border > image_max_width or image.height + top_border > image_max_height:
                        print("WARNING: frame", frame_index, "is greater than maximum image size", image_max_width, "x", str(image_max_height) + ".", "Pixels will be lost.")
                frame_data.append((pvrz_index, left_border, top_border, min(width, image_max_width - left_border), min(height, image_max_height - top_border), 0, 0))
                left_border += modulo_value(width, 4)
                max_left_border = max(max_left_border, left_border)
                row_height = max(row_height, height)

        to_return.append(frame_data)
    pvrz_images.append((pvrz_image, min(max_left_border, image_max_width), min(modulo_value(top_border + row_height, 4), image_max_height)))

    # crop each image
    pvrz_cropped_images = []
    for p in pvrz_images:
        p_image = p[0]
        p_width = p[1]
        p_height = p[2]
        pvrz_cropped_images.append(p_image.crop((0, 0, p_width, p_height)))
    # next we should store each cropped image as pvrz-file
    for idx, img in enumerate(pvrz_cropped_images):
        save_image_to_pvrz(directory, pvrz_prefix, idx, img, txt_format)
    return to_return
