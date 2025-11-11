import os
import zlib
import struct
from enum import Enum
import texture2ddecoder
from PIL import Image


class Flags(Enum):
    NONE = 0
    PRE_MULTIPLIED = 1


class ColorSpace(Enum):
    RGB = 0
    SRGB = 1


class PixelFormat(Enum):
    DXT1 = 7
    DXT5 = 11


class ChannelType(Enum):
    UBYTE_NORM = 0


def load_pvrz_page(input_directory: str,
                   page: int) -> Image.Image:
    '''load pixels data from the input page (file [input_directory]/MOS[page].pvrz)

    return PIL image object
    '''
    pvrz_file = input_directory + "/" + "MOS" + str(page) + ".pvrz"
    if not os.path.exists(pvrz_file):
        raise FileNotFoundError("there is no pvrz file " + pvrz_file)

    with open(pvrz_file, "rb") as file:
        input_pvrz = file.read()
        # may be this is inpucked pvr
        header = input_pvrz[0:4]
        is_pvr = header[0] == 0x50 and header[1] == 0x56 and header[2] == 0x52 and header[3] == 0x03
        buffer = None
        if not is_pvr:
            size = struct.unpack("I", input_pvrz[0:4])[0]
            buffer = zlib.decompress(input_pvrz[4:])
        else:
            buffer = input_pvrz[:]
        # buffer contains bytes with unpacked pvr data
        buffer_size = len(buffer)
        if buffer_size <= 0x34:
            raise Exception("invalid or incomplete PVR input data")

        # read header data
        # check the header
        signature = struct.unpack("I", buffer[0:4])[0]
        if signature != 0x03525650:
            raise Exception("no PVR signature found")
        
        flag_code = struct.unpack("I", buffer[4:8])[0]
        if flag_code != 0 and flag_code != 1:
            raise Exception("unsupported PVR flags " + str(flag_code))
        flags = Flags.NONE if flag_code == 0 else Flags.PRE_MULTIPLIED

        pixel_format_code = struct.unpack("Q", buffer[8:16])[0]
        if pixel_format_code & 0xffffffff00000000 != 0:
            # custom pixel format
            raise Exception("custom pixel format not supported")
        else:
            if pixel_format_code != 7 and pixel_format_code != 11:
                raise Exception("unsupported pixel format " + str(pixel_format_code) + ". Support only DXT1(7) and DXT5(11)")
        pixel_format = PixelFormat.DXT1 if pixel_format_code == 7 else PixelFormat.DXT5
        bits_per_input_pixel = 4 if pixel_format_code == 7 else 8
        color_depth = 16

        color_space_code = struct.unpack("I", buffer[16:20])[0]
        if color_space_code != 0 and color_space_code != 1:
            raise Exception("unsupported color space " + str(color_space_code))
        color_space = ColorSpace.RGB if color_space_code == 0 else ColorSpace.SRGB

        channel_type_code = struct.unpack("I", buffer[20:24])[0]
        if not (channel_type_code >= 0 and channel_type_code <= 12):
            raise Exception("unsupported channel type " + str(channel_type_code))
        if channel_type_code != 0:
            raise Exception("support only UBYTE_NORM(0) channel type")
        channel_type = ChannelType.UBYTE_NORM

        height = struct.unpack("I", buffer[24:28])[0]
        width = struct.unpack("I", buffer[28:32])[0]
        texture_depth = struct.unpack("I", buffer[32:36])[0]
        num_surfaces = struct.unpack("I", buffer[36:40])[0]
        num_faces = struct.unpack("I", buffer[40:44])[0]
        num_mip_maps = struct.unpack("I", buffer[44:48])[0]
        meta_size = struct.unpack("I", buffer[48:52])[0]

        if meta_size > 0 and meta_size + 0x34 > buffer_size:
            raise Exception("input buffer too small")

        meta_data = bytes() if meta_size == 0 else buffer[52:52+meta_size]
        header_size = 0x34 + meta_size
        
        data = buffer[header_size:header_size+buffer_size-header_size]
        decoded_data = None
        
        if pixel_format == PixelFormat.DXT1:
            decoded_data = texture2ddecoder.decode_bc1(data, width, height)
        elif pixel_format == PixelFormat.DXT5:
            decoded_data = texture2ddecoder.decode_bc3(data, width, height)
        if decoded_data is None:
            raise Exception("fail to decode texture data")
        
        img = Image.frombytes("RGBA", (width, height), decoded_data, 'raw', ("BGRA"))
        return img
    return None


def read_image_from_pvrzs(page_to_image: dict[int, Image.Image],
                          input_directory: str, 
                          input_data: bytes, 
                          data_ptr: int, 
                          blocks_cout: int,
                          frame_width: int,
                          frame_height: int) -> Image.Image:
    '''create and return PIL.Image from all required for the frame data blocks and return array with these pixels

    page_to_image is a dictionary with already loaded pages
    data_ptr point to the start of the data blocks in input binary data
    '''
    frame_image = Image.new("RGBA", (frame_width, frame_height))
    for block_index in range(blocks_cout):
        ptr = data_ptr + 7 * 4 * block_index
        # page is simpy a number
        # the file name is MOSxxxx.PVRZ
        pvrz_page = struct.unpack("I", input_data[ptr:ptr+4])[0]
        source_x = struct.unpack("I", input_data[ptr+4:ptr+8])[0]
        source_y = struct.unpack("I", input_data[ptr+8:ptr+12])[0]
        width = struct.unpack("I", input_data[ptr+12:ptr+16])[0]
        height = struct.unpack("I", input_data[ptr+16:ptr+20])[0]
        target_x = struct.unpack("I", input_data[ptr+20:ptr+24])[0]
        target_y = struct.unpack("I", input_data[ptr+24:ptr+28])[0]
        # width and height are sizes of the block
        # source is the point where the frame pixels start in this page
        # target is the where these pixels are in the frame
        # check is the page already loaded
        if pvrz_page not in page_to_image:
            # decode pixels data
            page_to_image[pvrz_page] = load_pvrz_page(input_directory, pvrz_page)

        # write block pixels to the output array
        # we should select from the page pixels required rect and write it to the output
        page_image = page_to_image[pvrz_page]
        region = page_image.crop((source_x, source_y, source_x + width, source_y + height))
        frame_image.paste(region, (target_x, target_y))
        
    return frame_image
