import requests  # type: ignore
import os
import time
import ast

def export_animations(pcc_folder: str, pcc_file: str):
    '''export to txt-files all animation sequence, stored in the input pcc-file
    '''
    req = requests.get("http://localhost:5000/api/animations?pcc=" + pcc_folder + pcc_file)
    output = req.text
    # $ separate animation name and data
    animation_parts = output.split("$")
    animations_count = len(animation_parts) // 2
    print("\tfind", animations_count, "animations")
    for anim_index in range(animations_count):
        animation_dict = {}

        anim_name = animation_parts[2 * anim_index]
        print("\t" + str(anim_index) + ":", anim_name)
        data = animation_parts[2 * anim_index + 1]
        # split data by %, it separate different bones
        bones_parts = data.split("%")
        bones_count = len(bones_parts) - 1
        bone_names = []
        bones_tfms = {}  # key - bone name, value - array of tuples
        for bone_index in range(0, bones_count):
            bone_data = bones_parts[bone_index]
            # split by #
            bone_data_parts = bone_data.split("#")[:-1]
            # first value is the bone name
            bone_name = bone_data_parts[0]
            bone_names.append(bone_name)
            # next is frames, each frame contains 8 numbers (frame, pos xyz and quaternion wxyz)
            frames_count = (len(bone_data_parts) - 1) // 8
            frames_array = []
            for frame in range(frames_count):
                frame_value = int(bone_data_parts[8*frame + 1])
                pos_x = float(bone_data_parts[8*frame + 1 + 1])
                pos_y = float(bone_data_parts[8*frame + 2 + 1])
                pos_z = float(bone_data_parts[8*frame + 3 + 1])
                rot_w = float(bone_data_parts[8*frame + 4 + 1])
                rot_x = float(bone_data_parts[8*frame + 5 + 1])
                rot_y = float(bone_data_parts[8*frame + 6 + 1])
                rot_z = float(bone_data_parts[8*frame + 7 + 1])
                frames_array.append((frame_value, (pos_x, pos_y, pos_z), (rot_w, rot_x, rot_y, rot_z)))
            bones_tfms[bone_name] = frames_array
        animation_dict["bones"] = bone_names
        animation_dict["tfms"] = bones_tfms
        
        # write animation dictionary to the file
        with open("animations\\" + anim_name + ".txt", "w") as file:
            file.write(str(animation_dict))


def export_all_animations(pcc_folder: str):
    # no input path, we parse all pcc-files and export animations from it
    for entry in os.listdir(pcc_folder):
        full_path = os.path.join(pcc_folder, entry)
        if os.path.isfile(full_path):
            ext = entry.split(".")[-1]
            if ext == "pcc":
                print(entry)
                export_animations(entry, pcc_folder)


def find_compatible_animations(actor: str):
    '''for input actor find animations with the same set of bones
    '''
    def is_sublist(a, b):
        '''return True if a is sublist of b
        '''
        for v in a:
            if v not in b:
                return False
        return True

    actor_bones = []
    with open("bones\\" + actor + ".txt", "r") as file:
        actor_bones = eval(file.read())
    to_return = []
    step = 0
    start_time = time.time()
    log_step = 1
    for entry in os.listdir("animations"):
        with open("animations\\" + entry, "r", encoding='utf-8') as file:
            file_content = file.read()
            anim_data = ast.literal_eval(file_content)
            anim_bones = anim_data["bones"]
            # we should check are all bones from animation exists in the actor bones list
            if is_sublist(anim_bones, actor_bones) and is_sublist(actor_bones, anim_bones):
                to_return.append(entry)

            if time.time() - start_time > 5.0 * log_step:
                log_step += 1
                print("Check", step, "files. Find", len(to_return), "animations. Spend", time.time() - start_time, "seconds")
        step += 1
    # save file names into separate file
    with open("bones\\" + actor + "_compat_anims.txt", "w") as file:
        file.write(str(to_return))
    print(to_return)