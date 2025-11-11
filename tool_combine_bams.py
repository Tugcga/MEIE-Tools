import os
import shutil
from bam_io import bam_to_file
from bam_io.bamv2 import BamV2, Frame, TextureFormat
from tool_gen_bams import helper_find_prefix 
from PIL import Image, ImageDraw, ImageFont


def one_frame_6000(image_filepath: str, 
                   center: tuple[int, int], 
                   directory: str,
                   char_name: str):
    '''Create all required bam-files for character animation type 6000

    This file combined from the one input image file, all frames are the same
    store as [char_name][...].bam files

    Content of each file and cycle does not matter
    Each cycle should contains only one frame

    A1 - A9 - 0 - 8
    CA - 0 - 71
    SA - 0 - 8
    SS - 0 - 8
    SX - 0 - 8
    G1: 9 - 17
    G11: 0 - 8
    G12: 18 - 26
    G13: 27 - 35
    G14: 36 - 44
    G15: 36 - 53
    G16: 54 - 62
    G17: 63 - 71
    G18: 72 - 80
    G19: 81 - 98

    Input:
        image_filepath - full path o the source image
        center - coordinates of the center for all frames
        directory - full path o the override directory
        char_name - animation name
    '''
    task = {
        "A1": (0, 9),
        "A2": (0, 9),
        "A3": (0, 9),
        "A4": (0, 9),
        "A5": (0, 9),
        "A6": (0, 9),
        "A7": (0, 9),
        "A8": (0, 9),
        "A9": (0, 9),
        "CA": (0, 72),
        "SA": (0, 9),
        "SS": (0, 9),
        "SX": (0, 9),
        "G1": (9, 18),
        "G11": (0, 9),
        "G12": (18, 27),
        "G13": (27, 36),
        "G14": (36, 45),
        "G15": (36, 54),
        "G16": (54, 63),
        "G17": (63, 72),
        "G18": (72, 81),
        "G19": (81, 99),
    }
    os.makedirs(directory, exist_ok=True)
    # for each key in the task dict we should crate one bam-file
    # this file should cointains non-empty cycles for value interval
    # each cycle should contains one frame
    img = Image.open(image_filepath)
    for key in task:
        interval = task[key]
        bam = BamV2()
        frame = Frame(img.width, img.height, center[0], center[1])
        frame.set_image(img)
        frame_idx = bam.add_frame(frame)
        for i in range(0, interval[0]):
            bam.add_cycle()
        for i in range(interval[0], interval[1]):
            c = bam.add_cycle()
            bam.add_frame_to_cycle(c, frame_idx)
        bam_to_file(bam, directory + char_name + key + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)


def combine_sprites(directory: str,
                    bam_name: str,
                    sprite_paths: list[str],
                    center: tuple[int, int] | None = None):
    '''Combine array of input sprites to one bam-file

    Input:
        directory - full path to override directory
        bam_name - name of the output bam-file without bam extension
        sprite_paths - list of full pathes to sprites
        center - center for each frame. If None then the center placed at the center of each frame
    '''
    out = BamV2()
    cycle = out.add_cycle()
    for sprite_path in sprite_paths:
        img = Image.open(sprite_path)
        if center is None:
            frame = Frame(img.width, img.height, img.width // 2, img.height // 2)
        else:
            frame = Frame(img.width, img.height, center[0], center[1])
        frame.set_image(img)
        frame_idx = out.add_frame(frame)
        out.add_frame_to_cycle(cycle, frame_idx)
    bam_to_file(out, directory + bam_name + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)


def combine_sprites_from_folder(directory: str,
                                bam_name: str,
                                sprites_directory: str,
                                center: tuple[int, int] | None = None):
    '''Combine all files from the input folder to one bam-file

    Input:
        directory - full path to the output override directory
        bam_name - name of the output bam-file withput bam extension
        sprites_directory - full path to the directory with source images
        center - center of each frame, if None the the center will be set at frame center
    '''
    files = os.listdir(sprites_directory)
    file_names = []
    for file in files:
        if os.path.isfile(sprites_directory + file):
            file_names.append(sprites_directory + file)
    combine_sprites(directory, bam_name, file_names, center)


def add_animation_to_bam(bam: BamV2,
                         animation_type: str,
                         frames_dict: dict[str, list[int]],
                         animation_path: str, 
                         montage: tuple[int, int, int], 
                         center: tuple[int, int]):
    '''This is helper function for combine animation functions
    '''
    if animation_type not in frames_dict:
        frame_cycles = []
        for cycle in range(0, 9):
            animation_orientation_dir = animation_path + str(cycle) + "/"
            file_names = os.listdir(animation_orientation_dir)
            file_names = file_names[montage[0]:len(file_names) if montage[1] == -1 else montage[1]:montage[2]]
            cycle_idx = bam.add_cycle()
            frame_indices = []
            for file_idx, file_name in enumerate(file_names):
                img = Image.open(animation_orientation_dir + "/" + file_name)
                frame = Frame(img.width, img.height, center[0], center[1])
                frame.set_image(img)
                frame_idx = bam.add_frame(frame)
                frame_indices.append(frame_idx)
                bam.add_frame_to_cycle(cycle_idx, frame_idx)
            frame_cycles.append(frame_indices)
        frames_dict[animation_type] = frame_cycles
    else:
        # no animation images, use frames from the dictionary
        frame_cycles = frames_dict[animation_type]
        for cycle in range(0, 9):
            cycle_idx = bam.add_cycle()
            frame_indices = frame_cycles[cycle]
            frame_indices = frame_indices[montage[0]:len(frame_indices) if montage[1] == -1 else montage[1]:montage[2]]
            for frame_idx in frame_indices:
                bam.add_frame_to_cycle(cycle_idx, frame_idx)


def combine_animations_7000_nonsplit(directory: str,
                                     bam_name: str,
                                     center: tuple[int, int],
                                     iddle_path: str = "",
                                     iddle_montage: tuple[int, int, int] = (0, -1, 1),
                                     battleiddle_path: str = "",
                                     battleiddle_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a1_path: str = "",
                                     attack_a1_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a2_path: str = "",
                                     attack_a2_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a3_path: str = "",
                                     attack_a3_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a4_path: str = "",
                                     attackt_a4_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a5_path: str = "",
                                     attack_a5_montage: tuple[int, int, int] = (0, -1, 1),
                                     getdamage_path: str = "",
                                     getdamage_montage: tuple[int, int, int] = (0, -1, 1),
                                     sleep_path: str = "",
                                     sleep_montage: tuple[int, int, int] = (0, -1, 1),
                                     getup_path: str = "",
                                     getup_montage: tuple[int, int, int] = (0, -1, 1),
                                     walk_path: str = "",
                                     walk_montage: tuple[int, int, int] = (0, -1, 1),
                                     death_path: str = "",
                                     death_montage: tuple[int, int, int] = (0, -1, 1),
                                     spell_path: str = "",
                                     spell_montage: tuple[int, int, int] = (0, -1, 1),
                                     cast_path: str = "",
                                     cast_montage: tuple[int, int, int] = (0, -1, 1)):
    '''Create non-split 7000 animation from the set of input image folders

    *_path is the path to the folder with animation frames
    each folder should contains folders 0 - 15 for different orientations
    7000 animation type used only 0 - 8 animations

    *_montage contains parameters for some preprocessing of frames
    it's start frame, end frame and frames step (to make animation with less frames)
    
    7000 without split has the following pattern:
    - G1: WK=0-8, SC=9-17, SD=18-26, GH=27-35, DE=36-44, TW=45-53, SL=54-62, GU=63-71
    - G2: A1=0-8, A2=9-17, A3=18-26, A4=27-35, A5=36-44, SP=45-53, CA=54-62
    '''
    bam_g1 = BamV2()
    # in this dictionary we store all frames, already added to the bam
    # key - the animation type
    # value - array of frame indices for each cycle of the animation
    # this dictionary can be used when we would like to add already existed frames as frames for some cycle
    # we extend this dictionary in the main helper function
    frames_dict: dict[str, list[list[int]]] = {}
    # WK
    if walk_path != "":
        print("write walk (WK) animation")
        add_animation_to_bam(bam_g1, "WK", frames_dict, walk_path, walk_montage, center)
    elif iddle_path != "":
        print("use iddle (SD) instead of walk (WK)")
        add_animation_to_bam(bam_g1, "SD", frames_dict, iddle_path, iddle_montage, center)
    else:
        raise Exception("no valid animation for walk (Wk)")

    # SC
    if battleiddle_path != "":
        print("write battle iddle (SC) animation")
        add_animation_to_bam(bam_g1, "SC", frames_dict, battleiddle_path, battleiddle_montage, center)
    elif iddle_path != "":
        print("use iddle (SD) instead if battle iddle (SC)")
        add_animation_to_bam(bam_g1, "SD", frames_dict, iddle_path, iddle_montage, center)
    else:
        raise Exception("no valid animation for battle iddle (SC)")
    
    # SD
    if iddle_path != "":
        print("write iddle (SD) animation")
        add_animation_to_bam(bam_g1, "SD", frames_dict, iddle_path, iddle_montage, center)
    else:
        raise Exception("no valid animation for iddle (SD)")

    # GH
    if getdamage_path != "":
        print("write get damage (GH) animation")
        add_animation_to_bam(bam_g1, "GH", frames_dict, getdamage_path, getdamage_montage, center)
    elif battleiddle_path != "":
        print("use battle iddle (SC) instead of get damage (GH)")
        add_animation_to_bam(bam_g1, "SC", frames_dict, "", battleiddle_montage, center)
    elif iddle_path != "":
        print("use iddle (SD) instead of get damage (GH)")
        add_animation_to_bam(bam_g1, "SD", frames_dict, "", iddle_montage, center)
    else:
        raise Exception("no valid animation for get damage (GH)")
    
    # DE
    if death_path != "":
        print("write death (DE) animation")
        add_animation_to_bam(bam_g1, "DE", frames_dict, death_path, death_montage, center)
    else:
        raise Exception("no valid animation for death (DE)")
    
    # TW
    # for TW we always use one-frame animation from the death animation
    # DE key already exist in the frames_dictionary
    # so, we should just select the last frame from this animation
    de_length = len(frames_dict["DE"][0])  # we assume that all cycles has the same number of frames
    print("write death pose (TW) animation, use death (DE) last frame")
    add_animation_to_bam(bam_g1, "DE", frames_dict, "", (de_length-2, de_length-1, 1), center)

    # SL
    if sleep_path != "":
        print("write sleep (SL) animation")
        add_animation_to_bam(bam_g1, "SL", frames_dict, sleep_path, sleep_montage, center)
    elif iddle_path != "":
        print("use iddle (SD) instead of sleep (SL)")
        add_animation_to_bam(bam_g1, "SD", frames_dict, "", sleep_montage, center)
    else:
        raise Exception("no valid animation for sleep (SL)")

    # GU
    if getup_path != "":
        print("write get up (GU) animation")
        add_animation_to_bam(bam_g1, "GU", frames_dict, getup_path, getup_montage, center)
    elif sleep_path != "":
        print("use reversed sleep (SL) instead of get up (GU)")
        sl_frames_count = len(frames_dict["SL"][0])
        # WARNING: here we lose the last frame, but here it does not matter,
        # because the last frame is the same as first frame for iddle       ->> here
        add_animation_to_bam(bam_g1, "SL", frames_dict, "", (sl_frames_count, 0, -1 * sleep_montage[2]), center)
    elif iddle_path != "":
        print("use iddle (SD) instead of get up (GU)")
        add_animation_to_bam(bam_g1, "SD", frames_dict, "", getup_montage, center)
    else:
        raise Exception("no valid animation for get up (GU)")

    bam_to_file(bam_g1, directory + bam_name + "G1" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # next the second file
    bam_g2 = BamV2()
    frames_dict.clear()
    # A1
    if attack_a1_path != "":
        print("write first attack (A1) animation")
        add_animation_to_bam(bam_g2, "A1", frames_dict, attack_a1_path, attack_a1_montage, center)
    else:
        raise Exception("no valid animation for first attack (A1)")

    # A2
    if attack_a2_path != "":
        print("write second attack (A2) animation")
        add_animation_to_bam(bam_g2, "A2", frames_dict, attack_a2_path, attack_a2_montage, center)
    elif attack_a1_path != "":
        print("use first attack (A1) instead of second attack (A2)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", attack_a1_montage, center)
    else:
        raise Exception("no valid animation for the second attack (A2)")

    # A3
    if attack_a3_path != "":
        print("write thierd attack (A3) animation")
        add_animation_to_bam(bam_g2, "A3", frames_dict, attack_a3_path, attack_a3_montage, center)
    elif attack_a1_path != "":
        print("use first attack (A1) instead of thierd attack (A3)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", attack_a1_montage, center)
    else:
        raise Exception("no valid animation for the thierd attack (A3)")

    # A4
    if attack_a4_path != "":
        print("write fourth attack (A4) animation")
        add_animation_to_bam(bam_g2, "A4", frames_dict, attack_a4_path, attack_a4_montage, center)
    elif attack_a1_path != "":
        print("use first attack (A1) instead of fourth attack (A4)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", attack_a1_montage, center)
    else:
        raise Exception("no valid animation for the fourth attack (A4)")

    # A5
    if attack_a5_path != "":
        print("write fifth attack (A5) animation")
        add_animation_to_bam(bam_g2, "A5", frames_dict, attack_a5_path, attack_a5_montage, center)
    elif attack_a1_path != "":
        print("use first attack (A1) instead of fifth attack (A5)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", attack_a1_montage, center)
    else:
        raise Exception("no valid animation for the fifth attack (A5)")

    # SP
    if spell_path != "":
        print("write spell (SP) animation")
        add_animation_to_bam(bam_g2, "SP", frames_dict, spell_path, spell_montage, center)
    elif attack_a1_path != "":
        print("use first attack (A1) instead of spell (SP)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", attack_a1_montage, center)
    else:
        raise Exception("no valid animation for the spell (SP)")

    # CA
    if cast_path != "":
        print("write cast (CA) animation")
        add_animation_to_bam(bam_g2, "CA", frames_dict, cast_path, cast_montage, center)
    elif attack_a1_path != "":
        print("use first attack (A1) instead of cast (CA)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", attack_a1_montage, center)
    else:
        raise Exception("no valid animation for the cast (CA)")

    bam_to_file(bam_g2, directory + bam_name + "G2" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)


def combine_animations_7000_split(directory: str,
                                  bam_name: str,
                                  center: tuple[int, int],
                                  iddle_path: str = "",
                                  iddle_montage: tuple[int, int, int] = (0, -1, 1),
                                  battleiddle_path: str = "",
                                  battleiddle_montage: tuple[int, int, int] = (0, -1, 1),
                                  attack_a1_path: str = "",
                                  attack_a1_montage: tuple[int, int, int] = (0, -1, 1),
                                  attack_a2_path: str = "",
                                  attack_a2_montage: tuple[int, int, int] = (0, -1, 1),
                                  attack_a3_path: str = "",
                                  attack_a3_montage: tuple[int, int, int] = (0, -1, 1),
                                  attack_a4_path: str = "",
                                  attackt_a4_montage: tuple[int, int, int] = (0, -1, 1),
                                  attack_a5_path: str = "",
                                  attack_a5_montage: tuple[int, int, int] = (0, -1, 1),
                                  getdamage_path: str = "",
                                  getdamage_montage: tuple[int, int, int] = (0, -1, 1),
                                  sleep_path: str = "",
                                  sleep_montage: tuple[int, int, int] = (0, -1, 1),
                                  getup_path: str = "",
                                  getup_montage: tuple[int, int, int] = (0, -1, 1),
                                  walk_path: str = "",
                                  walk_montage: tuple[int, int, int] = (0, -1, 1),
                                  death_path: str = "",
                                  death_montage: tuple[int, int, int] = (0, -1, 1),
                                  spell_path: str = "",
                                  spell_montage: tuple[int, int, int] = (0, -1, 1),
                                  cast_path: str = "",
                                  cast_montage: tuple[int, int, int] = (0, -1, 1)):
    '''Create splited 7000 animation from the set of input image folders

    - G1: SC=9-17
    - G11: WK=0-8
    - G12: SD=18-26
    - G13: GH=27-35
    - G14: GH=27-35 (unused), DE=36-44, TW=45-53
    - G15: TW=45-53
    - G2: A1=0-8
    - G21: A2=9-17
    - G22: A3=18-26
    - G23: A4=27-35
    - G24: A5=36-44
    - G25: SP=45-53
    - G26: CA=54-62
    '''
    def add_empty_cycles(bam: BamV2, start: int, end: int):
        for i in range(start, end):
            bam.add_cycle()

    # G1: SC=9-17
    frames_dict: dict[str, list[list[int]]] = {}
    bam_g1 = BamV2()
    add_empty_cycles(bam_g1, 0, 9)
    frames_dict.clear()
    if battleiddle_path != "":
        print("define battle iddle (SC) animation")
        add_animation_to_bam(bam_g1, "SC", frames_dict, battleiddle_path, battleiddle_montage, center)
    else:
        raise Exception("no valid battle iddle (SC) animation")
    bam_to_file(bam_g1, directory + bam_name + "G1" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # G11: WK=0-8
    bam_g11 = BamV2()
    frames_dict.clear()
    if walk_path != "":
        print("define walk (WK) animation")
        add_animation_to_bam(bam_g11, "WK", frames_dict, walk_path, walk_montage, center)
    else:
        raise Exception("no valid walk (WK) animation")
    bam_to_file(bam_g11, directory + bam_name + "G11" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # G12: SD=18-26
    bam_g12 = BamV2()
    frames_dict.clear()
    add_empty_cycles(bam_g12, 0, 18)
    if iddle_path != "":
        print("define iddle (SD) animation")
        add_animation_to_bam(bam_g12, "SD", frames_dict, iddle_path, iddle_montage, center)
    else:
        raise Exception("no valid iddle (SD) animation")
    bam_to_file(bam_g12, directory + bam_name + "G12" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # G13: GH=27-35
    bam_g13 = BamV2()
    frames_dict.clear()
    add_empty_cycles(bam_g13, 0, 27)
    if getdamage_path != "":
        print("define get damage (GH) animation")
        add_animation_to_bam(bam_g13, "GH", frames_dict, getdamage_path, getdamage_montage, center)
    else:
        raise Exception("no valid get damage (GH) animation")
    bam_to_file(bam_g13, directory + bam_name + "G13" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # G14: GH=27-35 (unused), DE=36-44, TW=45-53
    bam_g14 = BamV2()
    frames_dict.clear()
    add_empty_cycles(bam_g14, 0, 36)  # for unused GH set empty cycles
    if death_path != "":
        print("define death (DE) animation")
        add_animation_to_bam(bam_g14, "DE", frames_dict, death_path, death_montage, center)
    else:
        raise Exception("no valid death (DE) animation")

    # for the death pose (TW) use only the last frame of the (DE) animation
    de_length = len(frames_dict["DE"][0])
    print("write death pose (TW) animation, use death (DE) last frame")
    add_animation_to_bam(bam_g14, "DE", frames_dict, "", (de_length-2, de_length-1, 1), center)
    bam_to_file(bam_g14, directory + bam_name + "G14" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # G15: TW=45-53
    bam_g15 = BamV2()
    add_empty_cycles(bam_g15, 0, 45)
    # for TW use one-frame cycle, the last frame from death animation
    if death_path != "":
        print("define death pose (TW) as last frame from death animation")
        add_animation_to_bam(bam_g15, "TW", frames_dict, death_path, (-1, -1, 1), center)
    else:
        raise Exception("no valid death animation, can't create death pose (TW)")
    bam_to_file(bam_g15, directory + bam_name + "G15" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # for G2X part we can create one file with all animations, and then simply save it with different names
    # G2: A1=0-8
    bam_g2 = BamV2()
    frames_dict.clear()
    if attack_a1_path != "":
        print("define attack 1 (A1) animation")
        add_animation_to_bam(bam_g2, "A1", frames_dict, attack_a1_path, attack_a1_montage, center)
    else:
        raise Exception("no valid attack a1 (A1) animation")
    # to the same file
    # G21: A2=9-17
    if attack_a2_path != "":
        print("define attack 2 (A2) animation")
        add_animation_to_bam(bam_g2, "A2", frames_dict, attack_a2_path, attack_a2_montage, center)
    else:
        print("use attack (A1) instead of (A2)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", (0, -1, 1), center)
    # G22: A3=18-26
    if attack_a3_path != "":
        print("define attack 3 (A3) animation")
        add_animation_to_bam(bam_g2, "A3", frames_dict, attack_a3_path, attack_a3_montage, center)
    else:
        print("use attack (A1) instead of (A3)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", (0, -1, 1), center)
    # G23: A4=27-35
    if attack_a4_path != "":
        print("define attack 4 (A4) animation")
        add_animation_to_bam(bam_g2, "A4", frames_dict, attack_a4_path, attack_a4_montage, center)
    else:
        print("use attack (A1) instead of (A4)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", (0, -1, 1), center)
    # G24: A5=36-44
    if attack_a5_path != "":
        print("define attack 5 (A5) animation")
        add_animation_to_bam(bam_g2, "A5", frames_dict, attack_a5_path, attack_a5_montage, center)
    else:
        print("use attack (A1) instead of (A5)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", (0, -1, 1), center)
    # G25: SP=45-53
    if spell_path != "":
        print("define spell (SP) animation")
        add_animation_to_bam(bam_g2, "SP", frames_dict, spell_path, spell_montage, center)
    else:
        print("use attack (A1) instead of (SP)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", (0, -1, 1), center)
    # G26: CA=54-62
    if cast_path != "":
        print("define cast (CA) animation")
        add_animation_to_bam(bam_g2, "CA", frames_dict, cast_path, cast_montage, center)
    else:
        print("use attack (A1) instead of (CA)")
        add_animation_to_bam(bam_g2, "A1", frames_dict, "", (0, -1, 1), center)
    # now save the bam
    bam_to_file(bam_g2, directory + bam_name + "G2" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)
    # and copy it
    shutil.copy2(directory + bam_name + "G2" + ".bam", directory + bam_name + "G21" + ".bam")
    shutil.copy2(directory + bam_name + "G2" + ".bam", directory + bam_name + "G22" + ".bam")
    shutil.copy2(directory + bam_name + "G2" + ".bam", directory + bam_name + "G23" + ".bam")
    shutil.copy2(directory + bam_name + "G2" + ".bam", directory + bam_name + "G24" + ".bam")
    shutil.copy2(directory + bam_name + "G2" + ".bam", directory + bam_name + "G25" + ".bam")
    shutil.copy2(directory + bam_name + "G2" + ".bam", directory + bam_name + "G26" + ".bam")



def combine_animations_6000_split(directory: str,
                                     bam_name: str,
                                     center: tuple[int, int],
                                     iddle1_path: str = "",
                                     iddle1_montage: tuple[int, int, int] = (0, -1, 1),
                                     iddle2_path: str = "",
                                     iddle2_montage: tuple[int, int, int] = (0, -1, 1),
                                     iddle3_path: str = "",
                                     iddle3_montage: tuple[int, int, int] = (0, -1, 1),
                                     battleiddle1_path: str = "",
                                     battleiddle1_montage: tuple[int, int, int] = (0, -1, 1),
                                     battleiddle2_path: str = "",
                                     battleiddle2_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a1_path: str = "",
                                     attack_a1_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a2_path: str = "",
                                     attack_a2_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a3_path: str = "",
                                     attack_a3_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a4_path: str = "",
                                     attack_a4_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a5_path: str = "",
                                     attack_a5_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a6_path: str = "",
                                     attack_a6_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a7_path: str = "",
                                     attack_a7_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a8_path: str = "",
                                     attack_a8_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_a9_path: str = "",
                                     attack_a9_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_bow_path: str = "",
                                     attack_bow_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_sling_path: str = "",
                                     attack_sling_montage: tuple[int, int, int] = (0, -1, 1),
                                     attack_crossbow_path: str = "",
                                     attack_crossbow_montage: tuple[int, int, int] = (0, -1, 1),
                                     getdamage_path: str = "",
                                     getdamage_montage: tuple[int, int, int] = (0, -1, 1),
                                     sleep1_path: str = "",
                                     sleep1_montage: tuple[int, int, int] = (0, -1, 1),
                                     sleep2_path: str = "",
                                     sleep2_montage: tuple[int, int, int] = (0, -1, 1),
                                     getup_path: str = "",
                                     getup_montage: tuple[int, int, int] = (0, -1, 1),
                                     walk_path: str = "",
                                     walk_montage: tuple[int, int, int] = (0, -1, 1),
                                     death_path: str = "",
                                     death_montage: tuple[int, int, int] = (0, -1, 1),
                                     spell1_path: str = "",
                                     spell1_montage: tuple[int, int, int] = (0, -1, 1),
                                     spell2_path: str = "",
                                     spell2_montage: tuple[int, int, int] = (0, -1, 1),
                                     spell3_path: str = "",
                                     spell3_montage: tuple[int, int, int] = (0, -1, 1),
                                     spell4_path: str = "",
                                     spell4_montage: tuple[int, int, int] = (0, -1, 1),
                                     cast1_path: str = "",
                                     cast1_montage: tuple[int, int, int] = (0, -1, 1),
                                     cast2_path: str = "",
                                     cast2_montage: tuple[int, int, int] = (0, -1, 1),
                                     cast3_path: str = "",
                                     cast3_montage: tuple[int, int, int] = (0, -1, 1),
                                     cast4_path: str = "",
                                     cast4_montage: tuple[int, int, int] = (0, -1, 1)):
    '''Create splitted 6000 animation from the set of input image folders

    Example how to call:
        combine_animations_6000_split("override/",
                                      "anim",
                                      (82, 108),
                                      iddle1_path="images/idlle/",
                                      attack_a1_path="images/shot/",
                                      sleep1_path="images/deactivate/",
                                      walk_path="images/walk/",
                                      death_path="images/death/")

    - A1-A9: AX=0-8
    - SA, SS, SX: SX=0-8
    - G1: SC1=9-17 (1-h weapon)
    - G11: WK=0-8
    - G12: SD1=18-26
    - G13: SC2=27-35 (2-h weapon)
    - G14: GH=36-44
    - G15: GH=36-44, DE=45-53
    - G16: TW=54-62
    - G17: SD2=63-71
    - G18: SD3=72-80
    - G19: SL1=81-89, SL2=90-98
    - CA: CA1=0-8, SP1=9-17, CA2=18-26, SP2=27-35, CA3=36-44, SP3=45-53, CA4=54-62, SP4=63-71
    '''
    def add_or_copy(key: str,
                    src_key: str,
                    path: str, 
                    montage: tuple[int, int, int],
                    frames_dict: dict[str, list[list[int]]]):
        if path != "":
            print("define " + key + " animation")
            bam_a = BamV2()
            add_animation_to_bam(bam_a, key, frames_dict, path, montage, center)
            bam_to_file(bam_a, directory + bam_name + key + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)
        else:
            print("for " + key + " use the same resources as for " + src_key)
            shutil.copy2(directory + bam_name + src_key + ".bam", directory + bam_name + key + ".bam")

    def add_empty_cycles(bam: BamV2, start: int, end: int):
        for i in range(start, end):
            bam.add_cycle()

    def add_spell(bam: BamV2,
                  frames_dict: dict[str, list[list[int]]],
                  key: str,
                  path: str,
                  montage: tuple[int, int, int],
                  center: tuple[int, int],
                  battle_iddle_path: str,
                  battle_iddle_montage: tuple[int, int, int],
                  iddle_path: str,
                  iddle_montage: tuple[int, int, int]):
        if path != "":
            print("define (" + key + ") animation")
            add_animation_to_bam(bam, key, frames_dict, path, montage, center)
        elif battle_iddle_path != "":
            print("use battle iddle (SC) instead of (" + key + ")")
            add_animation_to_bam(bam, "SC", frames_dict, battle_iddle_path, battle_iddle_montage, center)
        elif iddle_path != "":
            print("use iddle (SD) instead of (" + key + ")")
            add_animation_to_bam(bam, "SD", frames_dict, iddle_path, iddle_montage, center)
        else:
            raise Exception("no valid (" + key + ") animation")

    frames_dict: dict[str, list[list[int]]] = {}
    bam_a1 = BamV2()
    frames_dict.clear()
    if attack_a1_path != "":
        print("define attack 1 (A1) animation")
        add_animation_to_bam(bam_a1, "A1", frames_dict, attack_a1_path, attack_a1_montage, center)
    else:
        raise Exception("no valid A1 animation")
    bam_to_file(bam_a1, directory + bam_name + "A1" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)

    # for other attack animations use specific sprites (if it defined, or reference to the same sprites as for A1)
    frames_dict.clear()
    add_or_copy("A2", "A1", attack_a2_path, attack_a2_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A3", "A1", attack_a3_path, attack_a3_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A4", "A1", attack_a4_path, attack_a4_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A5", "A1", attack_a5_path, attack_a5_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A6", "A1", attack_a6_path, attack_a6_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A7", "A1", attack_a7_path, attack_a7_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A8", "A1", attack_a8_path, attack_a8_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("A9", "A1", attack_a9_path, attack_a9_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("SA", "A1", attack_bow_path, attack_bow_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("SS", "A1", attack_sling_path, attack_sling_montage, frames_dict)
    frames_dict.clear()
    add_or_copy("SX", "A1", attack_crossbow_path, attack_crossbow_montage, frames_dict)

    # - G1: =0-8, SC1=9-17, 0=18-98
    bam_g1 = BamV2()
    add_empty_cycles(bam_g1, 0, 9)
    frames_dict.clear()
    if battleiddle1_path != "":
        print("define battle iddle 1 (SC1) animation")
        add_animation_to_bam(bam_g1, "SC1", frames_dict, battleiddle1_path, battleiddle1_montage, center)
    elif iddle1_path != "":
        print("use iddle 1 instead of battle iddle 1 (SC1)")
        add_animation_to_bam(bam_g1, "SD1", frames_dict, iddle1_path, iddle1_montage, center)
    else:
        raise Exception("no valid battle iddle (SC1) animation")
    add_empty_cycles(bam_g1, 18, 99)
    bam_to_file(bam_g1, directory + bam_name + "G1" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)
    frames_dict.clear()

    # - G11: WK=0-8, =9-98
    bam_g11 = BamV2()
    if walk_path != "":
        print("define walk (WK) animation")
        add_animation_to_bam(bam_g11, "WK", frames_dict, walk_path, walk_montage, center)
    else:
        raise Exception("no valid walk (WK) animation")
    add_empty_cycles(bam_g11, 9, 99)
    bam_to_file(bam_g11, directory + bam_name + "G11" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    frames_dict.clear()

    # - G12:  =0-17, SD1=18-26, =27-98
    bam_g12 = BamV2()
    add_empty_cycles(bam_g12, 0, 18)
    if iddle1_path != "":
        print("define iddle 1 (SD1) animation")
        add_animation_to_bam(bam_g12, "SD1", frames_dict, iddle1_path, iddle1_montage, center)
    else:
        raise Exception("no valid iddle 1 (SD1) animation")
    add_empty_cycles(bam_g12, 27, 99)
    bam_to_file(bam_g12, directory + bam_name + "G12" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    frames_dict.clear()

    # - G13:  =0-26, SC2=27-35,  =36-98
    bam_g13 = BamV2()
    add_empty_cycles(bam_g13, 0, 27)
    if battleiddle2_path != "":
        print("define battle iddle 2 (SC2) animation")
        add_animation_to_bam(bam_g13, "SC2", frames_dict, battleiddle2_path, battleiddle2_montage, center)
    elif battleiddle1_path != "":
        print("use battle iddle 1 (SC1) instead of (SC2)")
        add_animation_to_bam(bam_g13, "SC1", frames_dict, battleiddle1_path, battleiddle1_montage, center)
    elif iddle1_path != "":
        print("use iddle 1 (SD1) instead of (SC2)")
        add_animation_to_bam(bam_g13, "SD1", frames_dict, iddle1_path, iddle1_montage, center)
    else:
        raise Exception("no valid battle iddle 2 (SC2) animation")
    add_empty_cycles(bam_g13, 36, 99)
    bam_to_file(bam_g13, directory + bam_name + "G13" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    frames_dict.clear()

    # - G14:  =0-35, GH=36-44,  =45-98
    # - G15:  =0-35, GH=36-44, DE=45-53,  =54-98
    # these two bams contains hte same GH section
    # so, we can create one bam with both sections and copy it to the other name
    bam_g1415 = BamV2()
    add_empty_cycles(bam_g1415, 0, 36)
    if getdamage_path != "":
        print("define get damage (GH) animation")
        add_animation_to_bam(bam_g1415, "GH", frames_dict, getdamage_path, getdamage_montage, center)
    elif iddle1_path != "":
        print("ude iddle 1 (SD1) instead of get damage (GH)")
        add_animation_to_bam(bam_g1415, "SD1", frames_dict, iddle1_path, iddle1_montage, center)
    else:
        raise Exception("no valid get damage (GH) animation")
    if death_path != "":
        print("define death (DE) animation")
        add_animation_to_bam(bam_g1415, "DE", frames_dict, death_path, death_montage, center)
    else:
        raise Exception("no valid death (DE) animation")
    add_empty_cycles(bam_g1415, 54, 99)
    bam_to_file(bam_g1415, directory + bam_name + "G14" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    # and copy it to G15
    shutil.copy2(directory + bam_name + "G14" + ".bam", directory + bam_name + "G15" + ".bam")
    frames_dict.clear()

    # - G16:  =0-53, TW=54-62,  =63-98
    bam_g16 = BamV2()
    add_empty_cycles(bam_g16, 0, 54)
    # for TW use one-frame cycle, the last frame from death animation
    if death_path != "":
        print("define death pose (TW) as last frame from death animation")
        add_animation_to_bam(bam_g16, "TW", frames_dict, death_path, (-1, -1, 1), center)
    else:
        raise Exception("no valid death animation, can't create death pose (TW)")
    add_empty_cycles(bam_g16, 63, 99)
    bam_to_file(bam_g16, directory + bam_name + "G16" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    frames_dict.clear()

    # - G17:  =0-62, SD2=63-71,  =72-98
    bam_g17 = BamV2()
    add_empty_cycles(bam_g17, 0, 63)
    if iddle2_path != "":
        print("define iddle 2 (SD2) animation")
        add_animation_to_bam(bam_g17, "SD2", frames_dict, iddle2_path, iddle2_montage, center)
    elif iddle1_path != "":
        print("use iddle 1 (SD1) instead of (SD2)")
        add_animation_to_bam(bam_g17, "SD1", frames_dict, iddle1_path, iddle1_montage, center)
    else:
        raise Exception("no valid iddle 2 (SD2) animayion")
    add_empty_cycles(bam_g17, 72, 99)
    bam_to_file(bam_g17, directory + bam_name + "G17" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    frames_dict.clear()

    # - G18:  =0-71, SD3=72-80,  =81-98
    bam_g18 = BamV2()
    add_empty_cycles(bam_g18, 0, 72)
    if iddle3_path != "":
        print("define iddle 3 (SD3) animation")
        add_animation_to_bam(bam_g18, "SD3", frames_dict, iddle3_path, iddle3_montage, center)
    elif iddle1_path != "":
        print("use iddle 1 (SD1) instead of (SD3)")
        add_animation_to_bam(bam_g18, "SD1", frames_dict, iddle1_path, iddle1_montage, center)
    else:
        raise Exception("no valid iddle 3 (SD3) animayion")
    add_empty_cycles(bam_g18, 81, 99)
    bam_to_file(bam_g18, directory + bam_name + "G18" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)    
    frames_dict.clear()
    
    # - G19:  =0-80, SL1=81-89, SL2=90-98
    bam_g19 = BamV2()
    add_empty_cycles(bam_g19, 0, 81)
    if sleep1_path != "":
        print("define sleep 1 (SL1) animation")
        add_animation_to_bam(bam_g19, "SL1", frames_dict, sleep1_path, sleep1_montage, center)
    else:
        raise Exception("no valid sleep 1 (SL1) animation")
    if sleep2_path != "":
        print("define sleep 2 (SL2) animation")
        add_animation_to_bam(bam_g19, "SL2", frames_dict, sleep2_path, sleep2_montage, center)
    elif sleep1_path != "":
        print("use sleep 1 (SL1) instead of (SL2)")
        add_animation_to_bam(bam_g19, "SL1", frames_dict, sleep1_path, sleep1_montage, center)
    else:
        raise Exception("no valid sleep 2 (SL2) animation")
    bam_to_file(bam_g19, directory + bam_name + "G19" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)
    frames_dict.clear()

    # - CA: CA1=0-8, SP1=9-17, CA2=18-26, SP2=27-35, CA3=36-44, SP3=45-53, CA4=54-62, SP4=63-71
    bam_ca = BamV2()
    # CA1=0-8
    add_spell(bam_ca, frames_dict, "CA1", cast1_path, cast1_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # SP1=9-17
    add_spell(bam_ca, frames_dict, "SP1", spell1_path, spell1_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # CA2=18-26
    add_spell(bam_ca, frames_dict, "CA2", cast2_path, cast2_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # SP2=27-35
    add_spell(bam_ca, frames_dict, "SP2", spell2_path, spell2_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # CA3=36-44
    add_spell(bam_ca, frames_dict, "CA3", cast3_path, cast3_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # SP3=45-53
    add_spell(bam_ca, frames_dict, "SP3", spell3_path, spell3_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # CA4=54-62
    add_spell(bam_ca, frames_dict, "CA4", cast4_path, cast4_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    # SP4=63-71
    add_spell(bam_ca, frames_dict, "SP4", spell4_path, spell4_montage, center, battleiddle1_path, battleiddle1_montage, iddle1_path, iddle1_montage)
    bam_to_file(bam_ca, directory + bam_name + "CA" + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)
