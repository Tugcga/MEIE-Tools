import os
import struct
from PIL import Image
from bam_io.bamv2 import BamV2, Frame, TextureFormat
from bam_io.util_pvrz_in import read_image_from_pvrzs
from bam_io.util_pvrz_out import export_bam_pvrz


def bam_from_file(file_path: str) -> BamV2:
    '''create bam-object by using file from the input file_path
    '''
    def get_index(array, element):
        '''return index of the element in the array, -1 if it fails to find
        '''
        for index, value in enumerate(array):
            if value == element:
                return index
        return -1

    if not os.path.exists(file_path):
        raise FileNotFoundError("there is no file at " + file_path)

    with open(file_path, "rb") as file:
        input_data = file.read()
        signature = input_data[0:4]
        signature_str = "".join([chr(v) for v in signature])
        if signature_str != "BAM ":
            raise Exception("signature is " + signature_str + " instead of BAM ")
        
        version = input_data[4:8]
        version_str = "".join([chr(v) for v in version])
        if version_str != "V2  ":
            raise Exception("version is " + version_str + " instead of V2  ")

        # create output object
        output_bam = BamV2()

        # total number of frames in all cycles
        frame_entries = struct.unpack("I", input_data[8:12])[0]

        # the number of cycles
        cycle_entries = struct.unpack("I", input_data[12:16])[0]

        # the number of different blocks for all frames
        # each frame can use several data blocks
        data_blocks_count = struct.unpack("I", input_data[16:20])[0]

        frame_entries_offset = struct.unpack("I", input_data[20:24])[0]
        cycles_entries_offset = struct.unpack("I", input_data[24:28])[0]
        data_entries_offset = struct.unpack("I", input_data[28:32])[0]

        # read each frame entry
        # store unique frames in the list
        frames_params: list[tuple[int, int, int, int, int, int]] = []
        # map from frame entry to unique frame index in the list
        frames_map = {}
        page_to_image: dict[int, Image.Image] = {}  # store here pixels from each loaded page
        # key - page name, value - PIL image
        for frame_idx in range(frame_entries):
            # each frame data is 12 bytes (2 bytes x 6)
            ptr = frame_entries_offset + frame_idx * 12
            width = struct.unpack("h", input_data[ptr:ptr+2])[0]
            height = struct.unpack("h", input_data[ptr+2:ptr+4])[0]
            center_x = struct.unpack("h", input_data[ptr+4:ptr+6])[0]
            center_y= struct.unpack("h", input_data[ptr+6:ptr+8])[0]
            data_index = struct.unpack("h", input_data[ptr+8:ptr+10])[0]
            frame_blocks = struct.unpack("h", input_data[ptr+10:ptr+12])[0]
            # try to find this set of data in frames_params
            params = (width, height, center_x, center_y, data_index, frame_blocks)
            index = get_index(frames_params, params)
            if index == -1:
                frames_map[frame_idx] = len(frames_params)
                frames_params.append(params)
                new_frame = Frame(width, height, center_x, center_y)
                # each data block use 7 * 4 bytes
                frame_image = read_image_from_pvrzs(page_to_image,
                                                    os.path.dirname(file_path),
                                                    input_data, 
                                                    data_entries_offset + 7* 4 * data_index, 
                                                    frame_blocks,
                                                    width,
                                                    height)
                new_frame.set_image(frame_image)
                output_bam.add_frame(new_frame)
            else:
                frames_map[frame_idx] = index
        # next cycles
        for cycle_idx in range(cycle_entries):
            # each cycles use 4 bytes (2 bytes x 2)
            ptr = cycles_entries_offset + cycle_idx * 4
            frames_count = struct.unpack("h", input_data[ptr:ptr+2])[0]
            start_frames_index = struct.unpack("h", input_data[ptr+2:ptr+4])[0]
            # add cycle data to the bam
            cycle_index = output_bam.add_cycle()
            for f in range(frames_count):
                frame_index = start_frames_index + f
                output_bam.add_frame_to_cycle(cycle_index, frames_map[frame_index])

        return output_bam
    raise Exception("fail to read bam data from the file " + file_path)


def bam_to_file(bam: BamV2, output_path: str, pvrz_prefix: int, txt_format: TextureFormat):
    '''save input bam-object as bam-file, stored at output_path

    pvrz_prefix define the start number of the pvrz-file
    for example, if prefix is 17, then files will be MOS17000.pvrz, MOS17001.pvrz and so on
    '''
    directory = os.path.dirname(output_path)
    os.makedirs(directory, exist_ok=True)
    
    to_write = bytearray()
    # header
    to_write.extend(b"BAM ")
    to_write.extend(b"V2  ")
    
    # next total number of frames (sum of length of all cycles)
    total_frames = 0
    for cyc_idx in range(bam.get_cycles_count()):
        total_frames += bam.get_cycle_frames_count(cyc_idx)
    to_write.extend(struct.pack("I", total_frames))

    # cycles count
    to_write.extend(struct.pack("I", bam.get_cycles_count()))

    # next we should write the total count of data blocks
    # each frame can use several data blocks
    # actual data blocks stored at the end of the file
    # so, here is the place
    frames_data = export_bam_pvrz(bam, directory, pvrz_prefix, txt_format)
    # count the total number of data blocks
    # simply sum the length of arrays for each frame
    total_blocks_count = 0
    for frame_array in frames_data:
        total_blocks_count += len(frame_array)
    # write it
    to_write.extend(struct.pack("I", total_blocks_count))

    # next address of the frames entries segment
    # it starts after the header, so, after 8 x 4 bytes
    to_write.extend(struct.pack("I", 32))
    # cycles entries segment starts after frames
    # each frame entry spend 6 x 2 bytes
    to_write.extend(struct.pack("I", 32 + 12 * total_frames))
    # address of the data blocks start
    # each cycle spend 2 x2 bytes
    to_write.extend(struct.pack("I", 32 + 12 * total_frames + 4 * bam.get_cycles_count()))

    # write frame entries segments
    # each frame entry is a frame in the cycle
    # so, iterate throw cycles and write data about each frame
    for cyc_idx in range(bam.get_cycles_count()):
        cycle_frames = bam.get_cycle_frames(cyc_idx)
        for frame_idx in cycle_frames:
            frame = bam.get_frame(frame_idx)
            to_write.extend(struct.pack("h", frame.get_width()))
            to_write.extend(struct.pack("h", frame.get_height()))
            to_write.extend(struct.pack("h", frame.get_center_x()))
            to_write.extend(struct.pack("h", frame.get_center_y()))
            # next we should write start index of the data block and the number of data blocks for this frame
            # for this we should count the number of data blocks before the current frame in frames_data
            block_start = 0
            for i in range(frame_idx):
                frame_array = frames_data[i]
                block_start += len(frame_array)
            to_write.extend(struct.pack("h", block_start))
            to_write.extend(struct.pack("h", len(frames_data[frame_idx])))
    # cycles entires
    frames_ptr = 0
    for cyc_idx in range(bam.get_cycles_count()):
        cycle_frames = bam.get_cycle_frames(cyc_idx)
        to_write.extend(struct.pack("h", len(cycle_frames)))
        to_write.extend(struct.pack("h", frames_ptr))
        frames_ptr += len(cycle_frames)
    # and finally - data blocks entries
    for frame_array in frames_data:
        for data in frame_array:
            # pvrz page
            to_write.extend(struct.pack("I", pvrz_prefix * 1000 + data[0]))
            # source x, y coordinates
            to_write.extend(struct.pack("I", data[1]))
            to_write.extend(struct.pack("I", data[2]))
            # width and height
            to_write.extend(struct.pack("I", data[3]))
            to_write.extend(struct.pack("I", data[4]))
            # target x, y coordinates
            to_write.extend(struct.pack("I", data[5]))
            to_write.extend(struct.pack("I", data[6]))
    # write the output file
    with open(output_path, "wb") as out_file:
        out_file.write(to_write)
