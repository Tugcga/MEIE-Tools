from PIL import Image
from enum import Enum
import os


class TextureFormat(Enum):
    DXT1 = 1
    DXT5 = 2


class Frame:
    def __init__(self, in_width: int,
                       in_height: int,
                       in_center_x: int,
                       in_center_y: int):
        self._width = in_width
        self._height = in_height
        self._center_x = in_center_x
        self._center_y = in_center_y
        self._image: None | Image.Image = None

    def get_width(self) -> int:
        return self._width

    def get_height(self) -> int:
        return self._height

    def get_size(self) -> tuple[int, int]:
        return (self._width, self._height)

    def get_center(self) -> tuple[int, int]:
        return (self._center_x, self._center_y)
    
    def get_center_x(self) -> int:
        return self._center_x
    
    def get_center_y(self) -> int:
        return self._center_y

    def set_image(self, in_image: Image.Image):
        self._image = in_image

    def get_image(self) -> Image.Image | None:
        return self._image


class BamV2:
    def __init__(self):
        self._frames: list[Frame] = []
        # each cycles is just array with frame indices
        self._cycles: list[list[int]] = []

    def add_cycle(self) -> int:
        '''create empty cycles in the bam

        and return index of this cycle
        '''
        self._cycles.append([])
        return len(self._cycles) - 1

    def add_frame(self, frame: Frame) -> int:
        '''add frame to the bam

        and return index of this frame in the bam frames list
        '''
        self._frames.append(frame)
        return len(self._frames) - 1

    def get_frames_count(self) -> int:
        '''return the number of different frames in the bam
        '''
        return len(self._frames)

    def get_frame(self, frame_index: int) -> Frame:
        return self._frames[frame_index]
    
    def get_cycle_frames(self, cycle_index: int) -> list[int]:
        '''return frame indices of the input frame
        '''
        return self._cycles[cycle_index]

    def add_frame_to_cycle(self, cycle_index: int, frame_index: int):
        self._cycles[cycle_index].append(frame_index)

    def get_cycles_count(self) -> int:
        return len(self._cycles)

    def get_cycle_frames_count(self, cycle_index: int) -> int:
        '''return the number of frames in the input cycle
        '''
        return len(self._cycles[cycle_index])

    def save_frames(self, directory: str, name_prefix: str = "frame_", ext: str = "png"):
        has_slash = (directory[-1] == "/" or directory[-1] == "\\")
        os.makedirs(directory, exist_ok=True)
        for idx, frame in enumerate(self._frames):
            frame.get_image().save(directory + ("" if has_slash else "/") + name_prefix + str(idx) + "." + ext)

    def __str__(self):
        to_return = "bam V2"
        to_return += "\n" + str(len(self._frames)) + " frames"
        for frame in self._frames:
            to_return += "\n\t" + "size " + str(frame.get_size()) + " center " + str(frame.get_center())
        to_return += "\n" + str(len(self._cycles)) + " cycles"
        for cyc in self._cycles:
            to_return += "\n\t" + str(cyc)
        return to_return
