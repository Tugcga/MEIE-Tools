import os
from bam_io import bam_to_file
from bam_io.bamv2 import BamV2, Frame, TextureFormat
from PIL import Image, ImageDraw, ImageFont

'''
- A1 → SEQ_SLASH
- A2 → SEQ_BACKSLASH
- A3 → SEQ_JAB / SEQ_SHOOT
- S1 → SEQ_SHOOT
- CA - finish cast, switch to iddle (battle or neutral)
- DE - die process, switch to TW
- GH - get damage
- GU - get up (after sleep), switch to iddle (battle or neutral)
- SC  - battle iddle
- SD - iddle
- SL - sleep animation, last is freeze
- SP - cast spell, repeat several times, then switch to CA
- TW - dead pose
- WK - walk
'''

def helper_find_prefix(directory: str) -> int:
    '''enumerate all MOS[...].pvrz files and find the smallest free prefix

    for example, if there are files mos2001.pvrz, mos1000.pvrz, then it should return 3
    '''
    exist_heads = set()
    for file_name in os.listdir(directory):
        name = ".".join(file_name.split(".")[:-1])
        ext = file_name.split(".")[-1]
        if (ext == "pvrz" or ext == "PVRZ") and name.startswith("MOS"):
            number_str = name[3:]
            if number_str.isnumeric():
                number = int(number_str)
                number_head = number // 1000
                exist_heads.add(number_head)
    exist_heads_array = list(exist_heads)
    exist_heads_array.sort()
    if len(exist_heads_array) == 0:
        return 1
    for i in range(1, exist_heads_array[-1] + 2):
        if i not in exist_heads_array:
            return i

def gen_one_frame(anim_key: str, 
                  dir_index: int, 
                  frame: int, 
                  anim_frames: int, 
                  img: Image.Image, 
                  font, 
                  font_size: int,
                  text_color: tuple[int, int, int],
                  width: int, height: int):
    img_draw = ImageDraw.Draw(img)
    messages = [anim_key, str(dir_index)]
    messages.extend([str(frame + 1) + "/" + str(anim_frames)])
    for index, message in enumerate(messages):
        _, _, w, h = img_draw.textbbox((0, 0), message, font=font)
        img_draw.text(((width - w)/2, height / 2 - font_size * 1.2 * len(messages) / 2 + index * font_size * 1.2), message, fill=text_color, font=font)

def fill_cycle(bam: BamV2, anim_frames: int, text: str, direction: int,
               image_size: tuple[int, int],
               bg_color: tuple[int, int, int],
               font, font_size: int,
               text_color: tuple[int, int, int]):
    c = bam.add_cycle()
    for frame in range(anim_frames):
        img = Image.new("RGB", image_size, bg_color)
        width, height = image_size
        gen_one_frame(text, direction, frame, anim_frames, img, font, font_size, text_color, width, height)
        bam_frame = Frame(width, height, width // 2, height)
        bam_frame.set_image(img)
        f = bam.add_frame(bam_frame)
        bam.add_frame_to_cycle(c, f)

def generate_a000(directory: str, char_name: str, 
                  anim_frames: int = 12,
                  image_size: tuple[int, int] = (64, 128),
                  bg_color: tuple[int, int, int] = (72, 73, 77),
                  text_color: tuple[int, int, int] = (207, 207, 207),
                  font_size: int = 18):
    '''
    - G1: WK=0-9
    - G1E: WK=10-15
    - G2: SD=0-9, SC=16-25, GH=32-41, DE=48-57, TW=64-73
    - G2E: SD=10-15, SC=26-31, GH=42-47, DE=58-63, TW=74-79
    - G3: A1=0-9, A2=16-25, A3=32-41
    - G3E: A1=10-15, A2=26-31, A3=42-47

    support: walk, iddle, battle iddle, get damage, death, 3 types of attack
    not support: cast spell and finish cast, sleep, get up, shoot attack

    contains 16 non-mirrored animations

    in each card we write animation, direction, frame
    '''
    os.makedirs(directory, exist_ok=True)
    font = ImageFont.truetype("verdanab.ttf", font_size)
    width, height = image_size

    # G1: WK=0-9
    g1 = BamV2()
    for dir_index in range(10):
        fill_cycle(g1, anim_frames, "WK", dir_index, image_size, bg_color, font, font_size, text_color)
    bam_to_file(g1, directory + char_name + "G1.bam", 1, TextureFormat.DXT1)

    # G1E: WK=10-15
    g1e = BamV2()
    for dir_index in range(10):
        g1e.add_cycle()
    for dir_index in range(10, 16):
        fill_cycle(g1e, anim_frames, "WK", dir_index, image_size, bg_color, font, font_size, text_color)
    bam_to_file(g1e, directory + char_name + "G1E.bam", 2, TextureFormat.DXT1)

    # G2: SD=0-9, SC=16-25, GH=32-41, DE=48-57, TW=64-73
    g2 = BamV2()
    for dir_index in range(0, 10):
        fill_cycle(g2, anim_frames, "SD", dir_index - 0, image_size, bg_color, font, font_size, text_color)
    for _ in range(10, 16):
        g2.add_cycle()
    for dir_index in range(16, 26):
        fill_cycle(g2, anim_frames, "SC", dir_index - 16, image_size, bg_color, font, font_size, text_color)
    for _ in range(26, 32):
        g2.add_cycle()
    for dir_index in range(32, 42):
        fill_cycle(g2, anim_frames, "GH", dir_index - 32, image_size, bg_color, font, font_size, text_color)
    for _ in range(42, 48):
        g2.add_cycle()
    for dir_index in range(48, 58):
        fill_cycle(g2, anim_frames, "DE", dir_index - 48, image_size, bg_color, font, font_size, text_color)
    for _ in range(58, 64):
        g2.add_cycle()
    for dir_index in range(64, 74):
        fill_cycle(g2, anim_frames, "TW", dir_index - 64, image_size, bg_color, font, font_size, text_color)
    bam_to_file(g2, directory + char_name + "G2.bam", 3, TextureFormat.DXT1)

    # G2E: SD=10-15, SC=26-31, GH=42-47, DE=58-63, TW=74-79
    g2e = BamV2()
    for _ in range(0, 10):
        g2e.add_cycle()
    for i in range(10, 16):
        fill_cycle(g2e, anim_frames, "SD", i - 0, image_size, bg_color, font, font_size, text_color)
    for _ in range(16, 26):
        g2e.add_cycle()
    for i in range(26, 32):
        fill_cycle(g2e, anim_frames, "SC", i - 16, image_size, bg_color, font, font_size, text_color)
    for _ in range(32, 42):
        g2e.add_cycle()
    for i in range(42, 48):
        fill_cycle(g2e, anim_frames, "GH", i - 32, image_size, bg_color, font, font_size, text_color)
    for _ in range(48, 58):
        g2e.add_cycle()
    for i in range(58, 64):
        fill_cycle(g2e, anim_frames, "DE", i - 48, image_size, bg_color, font, font_size, text_color)
    for _ in range(64, 74):
        g2e.add_cycle()
    for i in range(74, 80):
        fill_cycle(g2e, anim_frames, "TW", i - 64, image_size, bg_color, font, font_size, text_color)
    bam_to_file(g2e, directory + char_name + "G2E.bam", 4, TextureFormat.DXT1)

    # G3: A1=0-9, A2=16-25, A3=32-41
    g3 = BamV2()
    for i in range(0, 10):
        fill_cycle(g3, anim_frames, "A1", i - 0, image_size, bg_color, font, font_size, text_color)
    for _ in range(10, 16):
        g3.add_cycle()
    for i in range(16, 26):
        fill_cycle(g3, anim_frames, "A2", i - 16, image_size, bg_color, font, font_size, text_color)
    for _ in range(26, 32):
        g3.add_cycle()
    for i in range(32, 42):
        fill_cycle(g3, anim_frames, "A3", i - 32, image_size, bg_color, font, font_size, text_color)
    bam_to_file(g3, directory + char_name + "G3.bam", 5, TextureFormat.DXT1)

    # G3E: A1=10-15, A2=26-31, A3=42-47
    g3e = BamV2()
    for _ in range(0, 10):
        g3e.add_cycle()
    for i in range(10, 16):
        fill_cycle(g3e, anim_frames, "A1", i - 0, image_size, bg_color, font, font_size, text_color)
    for _ in range(16, 26):
        g3e.add_cycle()
    for i in range(26, 32):
        fill_cycle(g3e, anim_frames, "A2", i - 16, image_size, bg_color, font, font_size, text_color)
    for _ in range(32, 42):
        g3e.add_cycle()
    for i in range(42, 48):
        fill_cycle(g3e, anim_frames, "A3", i - 32, image_size, bg_color, font, font_size, text_color)
    bam_to_file(g3e, directory + char_name + "G3E.bam", 6, TextureFormat.DXT1)


def process_bam_task(task: dict[str, dict[tuple[int, int], str]],
                     directory: str, char_name: str,
                     anim_frames: int,
                     image_size: tuple[int, int],
                     bg_color: tuple[int, int, int],
                     font, font_size: int,
                     text_color: tuple[int, int, int]):
    '''signature of the task:
        key - output file postfix,
        value - dictionary with cycles names:
            key - tuple, define cycle interval, (A, B) means that this should be cycles A, A + 1, ..., B - 1
            value - cycle name, empty name means that this cycle has no frames
            we suppose that intervals cover the whole timeline
            empty cycles should be placed in the task
    '''
    for key in task:
        key_bam = BamV2()
        key_data = task[key]
        for interval in key_data:
            cycle_name = key_data[interval]
            if cycle_name == "":
                for c in range(interval[0], interval[1]):
                    key_bam.add_cycle()
            else:
                for c in range(interval[0], interval[1]):
                    fill_cycle(key_bam, anim_frames, cycle_name, c - interval[0], image_size, bg_color, font, font_size, text_color)

        bam_to_file(key_bam, directory + char_name + key + ".bam", helper_find_prefix(directory), TextureFormat.DXT1)


def generate_6000_no_split(directory: str, char_name: str,
                           anim_frames: int = 12,
                           image_size: tuple[int, int] = (64, 128),
                           bg_color: tuple[int, int, int] = (72, 73, 77),
                           text_color: tuple[int, int, int] = (207, 207, 207),
                           font_size: int = 18):
    '''
    - G1: WK=0-8, SC1=9-17, SD1=18-26, SC2=27-35 (with 2-h weapon?), GH=36-44, DE=45-53, TW=54-62, SD2=63-71, SD3=72-80, SL1=81-89, SL2=90-98
    - CA: CA1=0-8, SP1=9-17, CA2=18-26, SP2=27-35, CA3=36-44, SP3=45-53, CA4=54-62, SP4=63-71
    '''
    task = {
        "A1": {(0, 9): "A1"},
        "A2": {(0, 9): "A2"},
        "A3": {(0, 9): "A3"},
        "A4": {(0, 9): "A4"},
        "A5": {(0, 9): "A5"},
        "A6": {(0, 9): "A6"},
        "A7": {(0, 9): "A7"},
        "A8": {(0, 9): "A8"},
        "A9": {(0, 9): "A9"},
        "CA": {(0, 9): "CA1",
               (9, 18): "SP1",
               (18, 27): "CA2",
               (27, 36): "SP2",
               (36, 45): "CA3",
               (45, 54): "SP3",
               (54, 63): "CA4",
               (63, 72): "SP4"},
        "SA": {(0, 9): "SA"},
        "SS": {(0, 9): "SS"},
        "SX": {(0, 9): "SX"},
        "G1": {
            (0, 9): "WK",
            (9, 18): "SC1",
            (18, 27): "SD1",
            (27, 36): "SC2",
            (36, 45): "GH",
            (45, 54): "DE",
            (54, 63): "TW",
            (63, 72): "SD2",
            (72, 81): "SD3",
            (81, 90): "SL1",
            (90, 99): "SL2"
        },
        "CA": {
            (0, 9): "CA1",
            (9, 18): "SP1",
            (18, 27): "CA2",
            (27, 36): "SP2",
            (36, 45): "CA3",
            (45, 54): "SP3",
            (54, 63): "CA4",
            (63, 72): "SP4"
        }
    }
    os.makedirs(directory, exist_ok=True)
    font = ImageFont.truetype("verdanab.ttf", font_size)
    process_bam_task(task, directory, char_name, anim_frames, image_size, bg_color, font, font_size, text_color)


def generate_6000(directory: str, char_name: str,
                  anim_frames: int = 12,
                  image_size: tuple[int, int] = (64, 128),
                  bg_color: tuple[int, int, int] = (72, 73, 77),
                  text_color: tuple[int, int, int] = (207, 207, 207),
                  font_size: int = 18):
    '''this scheme required many files, different names contains different types of animation
    support only 9 orientations, other 7 are wirrored

    A1 - A9 - each has only 9 cycles (for orientations), corresponds to different weapon attacks
    CA - cast animation:
        CA1=0-8, SP1=9-17, CA2=18-26, SP2=27-35, CA3=36-44, SP3=45-53, CA4=54-62, SP4=63-71
    SA - bow shoot (9 cycles)
    SS - sling shoot (9 cycles)
    SX - crossbow shoot (also 9 cycles)
    other are general animations in files G1, G11 - G19
        - G1: SC1=9-17 (1-h weapon), battle iddle
        - G11: WK=0-8, walk
        - G12: SD1=18-26, neutral iddle
        - G13: SC2=27-35 (2-h weapon), battle iddle
        - G14: GH=36-44, get hit
        - G15: GH=36-44, DE=45-53, also get hit and die
        - G16: TW=54-62, dead pose
        - G17: SD2=63-71, neutral iddle
        - G18: SD3=72-80, neutral iddle
        - G19: SL1=81-89, SL2=90-98, sleep

    this aimation contanis: attack, cast, shot, walk, battel and neutral iddle, get hit, death, sleep
    no special det up animation
    '''
    task = {
        "A1": {(0, 9): "A1"},
        "A2": {(0, 9): "A2"},
        "A3": {(0, 9): "A3"},
        "A4": {(0, 9): "A4"},
        "A5": {(0, 9): "A5"},
        "A6": {(0, 9): "A6"},
        "A7": {(0, 9): "A7"},
        "A8": {(0, 9): "A8"},
        "A9": {(0, 9): "A9"},
        "CA": {(0, 9): "CA1",
               (9, 18): "SP1",
               (18, 27): "CA2",
               (27, 36): "SP2",
               (36, 45): "CA3",
               (45, 54): "SP3",
               (54, 63): "CA4",
               (63, 72): "SP4"},
        "SA": {(0, 9): "SA"},
        "SS": {(0, 9): "SS"},
        "SX": {(0, 9): "SX"},
        "G1": {(0, 9): "",
               (9, 18): "SC1",
               (18, 99): ""},
        "G11": {(0, 9): "WK",
                (9, 99): ""},
        "G12": {(0, 18): "",
                (18, 27): "SD1",
                (27, 99): ""},
        "G13": {(0, 27): "",
                (27, 36): "SC2",
                (36, 99): ""},
        "G14": {(0, 36): "",
                (36, 45): "GH",
                (45, 99): ""},
        "G15": {(0, 36): "",
                (36, 45): "GHO",
                (45, 54): "DE",
                (54, 99): ""},
        "G16": {(0, 54): "",
                (54, 63): "TW",
                (63, 99): ""},
        "G17": {(0, 63): "",
                (63, 72): "SD2",
                (72, 99): ""},
        "G18": {(0, 72): "",
                (72, 80): "SD3",
                (80, 99): ""},
        "G19": {(0, 81): "",
                (81, 90): "SL1",
                (90, 99): "SL2"}
    }
    os.makedirs(directory, exist_ok=True)
    font = ImageFont.truetype("verdanab.ttf", font_size)
    process_bam_task(task, directory, char_name, anim_frames, image_size, bg_color, font, font_size, text_color)


def generate_7000_no_split(directory: str, char_name: str,
                  anim_frames: int = 12,
                  image_size: tuple[int, int] = (64, 128),
                  bg_color: tuple[int, int, int] = (72, 73, 77),
                  text_color: tuple[int, int, int] = (207, 207, 207),
                  font_size: int = 18):
    '''
    - G1: WK=0-8, SC=9-17, SD=18-26, GH=27-35, DE=36-44, TW=45-53, SL=54-62, GU=63-71
    - G2: A1=0-8, A2=9-17, A3=18-26, A4=27-35, A5=36-44, SP=45-53, CA=54-62
    '''
    task = {
        "G1": {
            (0, 9): "WK",
            (9, 18): "SC",
            (18, 27): "SD",
            (27, 36): "GH",
            (36, 45): "DE",
            (45, 54): "TW",
            (54, 63): "SL",
            (63, 72): "GU"
        },
        "G2": {
            (0, 9): "A1",
            (9, 18): "A2",
            (18, 27): "A3",
            (27, 36): "A4",
            (36, 45): "A5",
            (45, 54): "SP",
            (54, 63): "CA"
        }
    }
    os.makedirs(directory, exist_ok=True)
    font = ImageFont.truetype("verdanab.ttf", font_size)
    process_bam_task(task, directory, char_name, anim_frames, image_size, bg_color, font, font_size, text_color)


def generate_7000(directory: str, char_name: str,
                  anim_frames: int = 12,
                  image_size: tuple[int, int] = (64, 128),
                  bg_color: tuple[int, int, int] = (72, 73, 77),
                  text_color: tuple[int, int, int] = (207, 207, 207),
                  font_size: int = 18):
    '''another 9-orientation animations, all animations splitted into 13 files: G1, G11-G15, G2, G21-G26

    - G1: SC=9-17 attack iddle
    - G11: WK=0-8 walk
    - G12: SD=18-26 neutral iddle
    - G13: GH=27-35 get hit
    - G14: GH=27-35 (unused), DE=36-44, TW=45-53, dead and dead pose
    - G15: TW=45-53 another dead pose
    - G2: A1=0-8 different attack animations
    - G21: A2=9-17
    - G22: A3=18-26
    - G23: A4=27-35
    - G24: A5=36-44
    - G25: SP=45-53 spell casting
    - G26: CA=54-62 finish cast

    this is split-bam version of the 7000 animation set
    non-split bam version of this animation set contains separate SL (sleep) and GU (get up0 animation
    '''
    os.makedirs(directory, exist_ok=True)
    font = ImageFont.truetype("verdanab.ttf", font_size)
    task = {
        "G1": {(0, 9): "",
               (9, 18): "SC"},
        "G11": {(0, 9): "WK"},
        "G12": {(0, 18): "",
                (18, 27): "SD"},
        "G13": {(0, 27): "",
                (27, 36): "GH"},
        "G14": {(0, 27): "",
                (27, 36): "GHO",
                (36, 45): "DE",
                (45, 54): "TW"},
        "G15": {(0, 45): "",
                (45, 54): "TW"},
        "G2": {(0, 9): "A1"},
        "G21": {(0, 9): "",
                (9, 18): "A2"},
        "G22": {(0, 18): "",
                (18, 27): "A3"},
        "G23": {(0, 27): "",
                (27, 36): "A4"},
        "G24": {(0, 36): "A5p",
                (36, 45): "A5"},
        "G25": {(0, 45): "",
                (45, 54): "SP"},
        "G26": {(0, 54): "",
                (54, 63): "CA"}
    }
    process_bam_task(task, directory, char_name, anim_frames, image_size, bg_color, font, font_size, text_color)


def generate_circle(directory: str,
                    bam_name: str,
                    width: int,
                    height: int,
                    frames_count: int,
                    color: tuple[int, int, int] = (32, 32, 32),
                    text_color: tuple[int, int, int] = (192, 192, 192)):
    '''generate bam with circle at the center of the frame with frame number
    frames_count is the number of frames in one cycle
    bam_name is the name without *.bam
    '''
    font_size = min(width // 1.2, height // 1.2)
    font = ImageFont.truetype("verdanab.ttf", font_size)
    bam = BamV2()
    cycle = bam.add_cycle()
    for frame in range(frames_count):
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, width, height), fill=color)
        _, _, w, h = draw.textbbox((0, 0), str(frame), font=font)
        draw.text(((width - w)/2, height / 2 - font_size/2.0 - 3), str(frame), fill=text_color, font=font)
        
        new_frame = Frame(width, height, width // 2, height // 2)
        new_frame.set_image(img)
        frame_idx = bam.add_frame(new_frame)
        bam.add_frame_to_cycle(cycle, frame_idx)

    bam_to_file(bam, directory + bam_name + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)


def generate_square(directory: str,
                    bam_name: str,
                    width: int, height: int,
                    frames_count: int,
                    color: tuple[int, int, int] = (32, 32, 32),
                    text_color: tuple[int, int, int] = (192, 192, 192),
                    font_size: int = 16):
    font = ImageFont.truetype("verdanab.ttf", font_size)
    bam = BamV2()
    cycle = bam.add_cycle()
    for frame in range(frames_count):
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, width, height), fill=color)
        text = str(frame) + "/" + str(frames_count)
        _, _, w, h = draw.textbbox((0, 0), text, font=font)
        draw.text(((width - w)/2, height / 2 - font_size/2.0 - 3), text, fill=text_color, font=font)
        
        new_frame = Frame(width, height, width // 2, height // 2)
        new_frame.set_image(img)
        frame_idx = bam.add_frame(new_frame)
        bam.add_frame_to_cycle(cycle, frame_idx)

    bam_to_file(bam, directory + bam_name + ".bam", helper_find_prefix(directory), TextureFormat.DXT5)
