import os
import struct

def reassign_pvrz(bam_file: str,
                  target_prefix: int):
    '''Read input BAM file and reassign link to the pvrz to another one

    Аor examle, if the file contains links 2000, 2001, 2003, 2005
    and target prefix is 17, then new links will be 17000, 17001, 17003, 17005
    also rename corresponding pvrz-files

    WARNING: here we reassign all link and assume that all of them start with the same prefix

    Input:
        bam_file - full path to the bam-file
        target_prefix - new value for linked pvrz-pages
    '''
    if not os.path.exists(bam_file):
        raise FileNotFoundError("there is no file at " + bam_file)

    directory = os.path.dirname(bam_file)
    new_data = bytearray()

    with open(bam_file, "rb") as file:
        bam_data = file.read()
        signature = bam_data[0:4]
        signature_str = "".join([chr(v) for v in signature])
        if signature_str != "BAM ":
            raise Exception("signature is " + signature_str + " instead of BAM ")
        
        version = bam_data[4:8]
        version_str = "".join([chr(v) for v in version])
        if version_str != "V2  ":
            raise Exception("version is " + version_str + " instead of V2  ")

        if signature_str != "BAM " or version_str != "V2  ":
            raise Exception("unsupported header " + signature_str + " or version " + version_str)

        data_blocks_count = struct.unpack("I", bam_data[16:20])[0]
        data_entries_offset = struct.unpack("I", bam_data[28:32])[0]
        src_refs = set()
        for block_idx in range(data_blocks_count):
            ptr = data_entries_offset + 7*4 * block_idx
            pvrz_page = struct.unpack("I", bam_data[ptr:ptr+4])[0]
            src_refs.add(pvrz_page)
        src_refs_list = list(src_refs)
        src_refs_list.sort()
        # check are all these pvrz files are exists
        for ref in src_refs_list:
            ref_filename = directory + "/" + "MOS" + str(ref) + ".pvrz"
            if not os.path.exists(ref_filename):
                raise FileNotFoundError("there is no file at " + ref_filename)
        # next check that we can change refs to new prefix
        for ref in src_refs_list:
            new_ref = target_prefix * 1000 + ref % 1000
            new_ref_filename = directory + "/" + "MOS" + str(new_ref) + ".pvrz"
            if os.path.exists(new_ref_filename):
                raise FileNotFoundError("file " + new_ref_filename + " already exists")
        # ok, no intersections, repeat the process and rename files
        for ref in src_refs_list:
            old_name = directory + "/" + "MOS" + str(ref) + ".pvrz"
            new_ref = target_prefix * 1000 + ref % 1000
            new_name = directory + "/" + "MOS" + str(new_ref) + ".pvrz"
            os.rename(old_name, new_name)
        # now change data in bam_data
        # copy original bytes to the new byte array
        for i in range(len(bam_data)):
            new_data.append(bam_data[i])
        for block_idx in range(data_blocks_count):
            ptr = data_entries_offset + 7*4 * block_idx
            old_page = struct.unpack("I", new_data[ptr:ptr+4])[0]
            new_page = target_prefix * 1000 + old_page % 1000
            new_bytes = struct.pack("I", new_page)
            for i in range(4):
                new_data[ptr + i] = new_bytes[i]
    # save the file
    with open(bam_file, "wb") as file:
        file.write(new_data)


def get_linked_res(bam_file: str) -> list[int]:
    '''Return indices of linked pvrz-files

    Input:
        bam_file - full path to bam-file

    Output:
        list of indices
    '''
    src_refs_list = []
    with open(bam_file, "rb") as file:
        bam_data = file.read()
        data_blocks_count = struct.unpack("I", bam_data[16:20])[0]
        data_entries_offset = struct.unpack("I", bam_data[28:32])[0]
        src_refs = set()
        for block_idx in range(data_blocks_count):
            ptr = data_entries_offset + 7*4 * block_idx
            pvrz_page = struct.unpack("I", bam_data[ptr:ptr+4])[0]
            src_refs.add(pvrz_page)
        src_refs_list = list(src_refs)
        src_refs_list.sort()
    return src_refs_list


def delete_bam(directory: str, bam_name: str, is_log: bool = False):
    '''Remove bam-file and also all linked pvrz-files

    Input:
        directory - full path to the directory with bam-file
        bam_name - name of the bam-file without bam extension
        is_log - if True then notify in console what file was removed
    '''
    bam_file = directory + bam_name + ".bam"
    linked_pvrz = get_linked_res(bam_file)
    for idx in linked_pvrz:
        file_path = directory + "MOS" + str(idx) + ".pvrz"
        if os.path.isfile(file_path):
            if is_log:
                print("remove " + file_path)
            os.remove(file_path)
    if os.path.isfile(bam_file):
        if is_log:
            print("remove " + bam_file)
        os.remove(bam_file)


def delete_6000_split(directory: str, anim_name: str):
    '''Remove all bam-files required for splited 6000 character animation

    Splitted 6000 animation contains many files: A1 - A9, CA, G1, G11 - G19, SA, SS, SX

    Input:
        directory - full path to the override directory
        anim_name - name of the animation
    '''
    delete_bam(directory, anim_name + "A1")
    delete_bam(directory, anim_name + "A2")
    delete_bam(directory, anim_name + "A3")
    delete_bam(directory, anim_name + "A4")
    delete_bam(directory, anim_name + "A5")
    delete_bam(directory, anim_name + "A6")
    delete_bam(directory, anim_name + "A7")
    delete_bam(directory, anim_name + "A8")
    delete_bam(directory, anim_name + "A9")
    delete_bam(directory, anim_name + "CA")
    delete_bam(directory, anim_name + "G1")
    delete_bam(directory, anim_name + "G11")
    delete_bam(directory, anim_name + "G12")
    delete_bam(directory, anim_name + "G13")
    delete_bam(directory, anim_name + "G14")
    delete_bam(directory, anim_name + "G15")
    delete_bam(directory, anim_name + "G16")
    delete_bam(directory, anim_name + "G17")
    delete_bam(directory, anim_name + "G18")
    delete_bam(directory, anim_name + "G19")
    delete_bam(directory, anim_name + "SA")
    delete_bam(directory, anim_name + "SS")
    delete_bam(directory, anim_name + "SX")


def delete_7000_split(directory: str, anim_name: str):
    '''Remove all bam-files required for splited 7000 character animation

    Input:
        directory - full path to the override directory
        anim_name - name of the animation
    '''
    delete_bam(directory, anim_name + "G1")
    delete_bam(directory, anim_name + "G11")
    delete_bam(directory, anim_name + "G12")
    delete_bam(directory, anim_name + "G13")
    delete_bam(directory, anim_name + "G14")
    delete_bam(directory, anim_name + "G15")
    delete_bam(directory, anim_name + "G2")
    delete_bam(directory, anim_name + "G21")
    delete_bam(directory, anim_name + "G22")
    delete_bam(directory, anim_name + "G23")
    delete_bam(directory, anim_name + "G24")
    delete_bam(directory, anim_name + "G25")
    delete_bam(directory, anim_name + "G26")
