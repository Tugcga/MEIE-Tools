import os
from PIL import Image  # type: ignore
import numpy as np  # type: ignore
from py3dscene.gltf_io import from_gltf, to_gltf  # type: ignore

def mask_to_emission(texture_path, output_path, channel):
    texture_img = Image.open(texture_path).convert("RGB")
    texture_pixels = np.array(texture_img)
    emission = texture_pixels[..., channel]
    height, width = emission.shape
    combined = np.zeros((height, width, 3), dtype=np.float32)
    combined[..., 0] = emission
    combined[..., 1] = emission
    combined[..., 2] = emission
    combined_img = Image.fromarray((combined).astype(np.uint8))
    combined_img.save(output_path)


def convert_specular_channel_to_metallic_roughness(specular_path, output_path, channel, metallic_threshold=0.3):
    specular_img = Image.open(specular_path).convert("RGB")
    specular_pixels = np.array(specular_img) / 255.0
    specular = specular_pixels[..., channel]

    roughness = 1.0 - specular

    metallic = np.where(specular > metallic_threshold, 1.0, 0.0)

    height, width = roughness.shape
    combined = np.zeros((height, width, 3), dtype=np.float32)
    combined[..., 0] = 0.0
    combined[..., 1] = roughness
    combined[..., 2] = specular  # metallic

    combined_img = Image.fromarray((combined * 255).astype(np.uint8))
    combined_img.save(output_path)


def convert_specular_to_metallic_roughness(specular_path, output_path, metallic_threshold=0.3):
    specular_img = Image.open(specular_path).convert("RGB")
    specular_pixels = np.array(specular_img) / 255.0

    roughness = 1.0 - np.mean(specular_pixels, axis=2)

    # metallic = np.where(np.max(specular_pixels, axis=2) > metallic_threshold, 1.0, 0.0)
    metallic = np.mean(specular_pixels, axis=2)

    height, width = roughness.shape
    combined = np.zeros((height, width, 3), dtype=np.float32)
    combined[..., 0] = 0.0
    combined[..., 1] = roughness
    combined[..., 2] = metallic

    combined_img = Image.fromarray((combined * 255).astype(np.uint8))
    combined_img.save(output_path)


def convert_specular_power_to_metallic_roughness(input_path, output_path, metallic_threshold=0.35):
    img = Image.open(input_path).convert("RGB")
    pixels = np.array(img) / 255.0
    specular = pixels[..., 0]
    specular_power = pixels[..., 2]

    roughness = 1.0 - specular_power
    metallic = np.where(specular > metallic_threshold, 1.0, 0.0)
    height, width = roughness.shape
    combined = np.zeros((height, width, 3), dtype=np.float32)
    combined[..., 0] = 0.0
    combined[..., 1] = roughness
    combined[..., 2] = specular  # metallic

    result_img = Image.fromarray((combined * 255).astype(np.uint8))
    result_img.save(output_path)


def convert_specular_power_textures_to_metallic_roughness(specular_path, power_path, output_path, metallic_threshold=0.35):
    spec_img = Image.open(specular_path).convert("RGB")
    pwr_img = Image.open(power_path).convert("RGB")
    spec_width, spec_height = spec_img.size
    pwr_width, pwr_height = pwr_img.size
    width = min(spec_width, pwr_width)
    height = min(spec_height, pwr_height)
    spec_img = spec_img.resize((width, height))
    pwr_img = pwr_img.resize((width, height))

    spec_pixels = np.array(spec_img) / 255.0
    pwr_pixels = np.array(pwr_img) / 255.0
    specular = spec_pixels[..., 0]
    specular_power = pwr_pixels[..., 0]

    roughness = 1.0 - specular_power
    metallic = np.where(specular > metallic_threshold, 1.0, 0.0)
    combined = np.zeros((height, width, 3), dtype=np.float32)
    combined[..., 0] = 0.0
    combined[..., 1] = roughness
    combined[..., 2] = specular  # metallic

    result_img = Image.fromarray((combined * 255).astype(np.uint8))
    result_img.save(output_path)


def find_material_texture_param(material_data, key: str):
    mat_parameters = material_data["parameters"]
    for mat_param in mat_parameters:
        param_name = mat_param[0]
        param_type = mat_param[1]
        param_value = mat_param[2]
        if param_type == "texture":
            if param_name == key:
                return param_value
    return None


def find_material_nonassigned_texture(material_data, postfix: str):
    mat_textures = material_data["textures"]
    for tex in mat_textures:
        if tex.endswith(postfix):
            return tex
    return None


def find_material_vector_param(material_data, key: str):
    mat_parameters = material_data["parameters"]
    for mat_param in mat_parameters:
        param_name = mat_param[0]
        param_type = mat_param[1]
        param_value = mat_param[2]
        if param_type == "vector":
            if param_name == key:
                return param_value
    return None


def find_material_float_param(material_data, key: str):
    mat_parameters = material_data["parameters"]
    for mat_param in mat_parameters:
        param_name = mat_param[0]
        param_type = mat_param[1]
        param_value = mat_param[2]
        if param_type == "scalar":
            if param_name == key:
                return param_value
    return None


def get_diffuse_texture(material_data):
    '''return the name of the diffuse texture
    material_data is a dictionary with keys index, name, textures and parameters

    if there are no diffuse texture, return empty string
    '''
    diffuse = find_material_texture_param(material_data, "Diffuse")
    if diffuse is None:
        diffuse = find_material_texture_param(material_data, "Simple Diffuse")
    if diffuse is None:
        diffuse = find_material_texture_param(material_data, "Diff")
    if diffuse is None:
        diffuse = find_material_texture_param(material_data, "Texture")
    if diffuse is None:
        diffuse = find_material_texture_param(material_data, "Diffuse_Map")
    if diffuse is None:
        diffuse = find_material_texture_param(material_data, "Tech_Diff")
    if diffuse is None:
        diffuse = find_material_texture_param(material_data, "Base_Diff")

    # search placeholder
    if diffuse is None:
        diffuse = find_material_nonassigned_texture(material_data, "_Diff")
        if diffuse is None:
            diffuse = find_material_nonassigned_texture(material_data, "_DIFF")
        if diffuse is None:
            diffuse = find_material_nonassigned_texture(material_data, "_Msk1")
        if diffuse is None:
            diffuse = find_material_nonassigned_texture(material_data, "_tex")
        if diffuse is None:
            diffuse = find_material_nonassigned_texture(material_data, "_diff")
        if diffuse is None:
            diffuse = find_material_nonassigned_texture(material_data, "_Graphs")
        if diffuse is not None:
            print("\t\tuse diffuse placeholder " + diffuse)
    return "" if diffuse is None else diffuse


def get_normal_texture(material_data):
    normal = find_material_texture_param(material_data, "Normal")
    if normal is None:
        normal = find_material_texture_param(material_data, "NormalMap")
    if normal is None:
        normal = find_material_texture_param(material_data, "Base_Normal")
    if normal is None:
        normal = find_material_texture_param(material_data, "NORM")
    if normal is None:
        normal = find_material_texture_param(material_data, "Normal_Map")
    if normal is None:
        normal = find_material_texture_param(material_data, "HMM_VSR_Norm")
    if normal is None:
        normal = find_material_texture_param(material_data, "TechInset_Norm01")
    if normal is None:
        normal = find_material_texture_param(material_data, "Base_Norm")
    
    # search placeholder
    if normal is None:
        normal = find_material_nonassigned_texture(material_data, "_Norm")
        if normal is None:
            normal = find_material_nonassigned_texture(material_data, "_NORM")
        if normal is None:
            normal = find_material_nonassigned_texture(material_data, "_norm")
        if normal is not None:
            print("\t\tuse normal placeholder " + normal)
    return "" if normal is None else normal


def get_emissive_texture(material_data):
    emissive = find_material_texture_param(material_data, "Emissive")
    return "" if emissive is None else emissive


def get_specular_texture(material_data):
    specular = find_material_texture_param(material_data, "Specular")
    if specular is None:
        specular = find_material_texture_param(material_data, "Simple Specular")
    if specular is None:
        specular = find_material_texture_param(material_data, "Spec")
    return "" if specular is None else specular


def get_specular_power_texture(material_data):
    power = find_material_texture_param(material_data, "SpecularPower")
    return "" if power is None else power


def get_emissive_color(material_data):
    color = find_material_vector_param(material_data, "EmissiveColour")
    if color is None:
        color = find_material_vector_param(material_data, "Emissive_color")
    if color is None:
        color = find_material_vector_param(material_data, "EmissiveColor")
    if color is None:
        color = find_material_vector_param(material_data, "Emissive_Color_Intensity")

    value = find_material_float_param(material_data, "Emissive")
    if value is not None:
        color = (value, value, value, 1.0)

    if color is None:
        # raise Exception("Try to get emission color, but fail for the material " + str(material_data))
        print("\t\tNO EMISSION COLOR")
    return (0.0, 0.0, 0.0) if color is None else (color[:3] if color[3] < 0.01 else tuple(color[i] * color[3] for i in range(3)))


def get_all_textures(material_data):
    '''return list of all textures, used in expressions
    return texture file names
    '''
    to_return = []
    mat_parameters = material_data["parameters"]
    for mat_param in mat_parameters:
        param_name = mat_param[0]
        param_type = mat_param[1]
        param_value = mat_param[2]
        if param_type == "texture":
            if param_value not in to_return:
                to_return.append(param_value)
    return to_return


def get_msk3_texture(material_data):
    '''return texture name, if it has the form ..._Msk3
    '''
    mat_parameters = material_data["parameters"]
    for mat_param in mat_parameters:
        param_name = mat_param[0]
        param_type = mat_param[1]
        param_value = mat_param[2]
        if param_type == "texture":
            if param_value.split("_")[-1] == "Msk3" or param_name.startswith("MSK3"):
                return param_value
    return ""


def get_msk_texture(material_data):
    msk = find_material_texture_param(material_data, "Msk2")
    if msk is None:
        msk = find_material_texture_param(material_data, "MSK")
    return "" if msk is None else msk


def get_msk3_keys(material_data, msk3_texture):
    mat_parameters = material_data["parameters"]
    for mat_param in mat_parameters:
        param_name = mat_param[0]
        param_type = mat_param[1]
        param_value = mat_param[2]
        if param_type == "texture" and param_value == msk3_texture:
            # we should parse param name and extract parts for red, green and blue keys
            red_ptr = param_name.find("Red")
            green_ptr = param_name.find("Green")
            blue_ptr = param_name.find("Blue")
            red_key = param_name[red_ptr+3:green_ptr].replace("-", "").strip()
            green_key = param_name[green_ptr+5:blue_ptr].replace("-", "").strip()
            blue_key = param_name[blue_ptr+4:].replace("-", "").strip()
            return red_key, green_key, blue_key


def change_extension(file_path: str, ext: str) -> str:
    '''Change the extension of the file
    '''
    parts = file_path.split(".")
    return ".".join(parts[:-1]) + "." + ext


def fix_one_model(file: str, textures_folder: str):
    file_name = file.split("\\")[-1]
    print(file_name)
    scene = from_gltf(file)
    # get material data
    mat_file = change_extension(file, "mat")
    if os.path.exists(mat_file):
        with open(mat_file, "r") as mf:
            mats_data = eval(mf.read())
        # print(scene)

        scene_materials = scene.get_all_materials()
        for mat_id, material in enumerate(scene_materials):
            material.set_metalness(0.0)
            material.set_roughness(1.0)
            material.set_albedo(1.0, 1.0, 1.0, 1.0)
            mat_data = mats_data[mat_id]
            print("\t" + (mat_data["name"] if "name" in mat_data else "UNKNOWN NAME"))
            # print(mat_data)
            has_emission = False
            has_specular = False
            if "parameters" not in mat_data:
                print("\t\tNo parameters section in the material")
                # set neutral albedo
                material.set_albedo(0.5, 0.5, 0.5, 1.0)
                continue
            material_textures = get_all_textures(mat_data)  # here names of all used textures
            diffuse_texture = get_diffuse_texture(mat_data)
            if diffuse_texture != "":
                # assign diffuse texture to the material
                material.set_albedo_texture(textures_folder + diffuse_texture + ".png", 0)
                if diffuse_texture in material_textures:
                    # check it, because we can get diffuse texture not from parameters, but from non-assigned textures
                    material_textures.remove(diffuse_texture)
            else:
                # raise Exception("No diffuse for " + file)
                print("\t\tNO DIFFUSE")
            normal_texture = get_normal_texture(mat_data)
            if normal_texture != "":
                material.set_normal_texture(textures_folder + normal_texture + ".png", 0, 1.0)
                if normal_texture in material_textures:
                    material_textures.remove(normal_texture)
            else:
                # raise Exception("No normals for " + file)
                print("\t\tNO NORMAL")
            # optional emissive texture
            emissive_texture = get_emissive_texture(mat_data)
            if emissive_texture != "":
                has_emission = True
                material.set_emissive_texture(textures_folder + emissive_texture + ".png", 0)
                material_textures.remove(emissive_texture)
                # may be there is emissive color
                emissive_color = get_emissive_color(mat_data)
                material.set_emissive(*emissive_color)
            # optional specular texture
            specular_texture = get_specular_texture(mat_data)
            if specular_texture != "":
                has_specular = True
                material_textures.remove(specular_texture)
                # convert to another texture for M/R
                # check is there is a specular power texture
                pwr_texture = get_specular_power_texture(mat_data)
                mr_texture = textures_folder + specular_texture + "MR.png"
                if pwr_texture != "":
                    material_textures.remove(pwr_texture)
                    convert_specular_power_textures_to_metallic_roughness(
                        textures_folder + specular_texture + ".png",
                        textures_folder + pwr_texture + ".png",
                        mr_texture)
                else:
                    convert_specular_to_metallic_roughness(
                        textures_folder + specular_texture + ".png",
                        mr_texture)
                material.set_metallic_roughness_texture(mr_texture, 0)
                material.set_metalness(1.0)

            # try to obtain msk3 texture
            msk3_texture = get_msk3_texture(mat_data)
            if msk3_texture != "":
                material_textures.remove(msk3_texture)
                rgb_keys = get_msk3_keys(mat_data, msk3_texture)
                if not has_specular:
                    # for specular use the b-channel of the mask
                    has_specular = True
                    mr_texture = textures_folder + msk3_texture + "MR.png"
                    convert_specular_power_to_metallic_roughness(
                        textures_folder + msk3_texture + ".png",
                        mr_texture)
                    material.set_metallic_roughness_texture(mr_texture, 0)
                    material.set_metalness(1.0)
                if not has_emission:
                    # extract emission map from g-channel
                    has_emission = True
                    em_texture = textures_folder + msk3_texture + "EM.png"
                    mask_to_emission(textures_folder + msk3_texture + ".png", em_texture, 1)
                    material.set_emissive_texture(em_texture, 0)
                    # try to get emission color
                    emissive_color = get_emissive_color(mat_data)
                    material.set_emissive(*emissive_color)
            msk_texture = get_msk_texture(mat_data)
            if msk_texture != "":
                # in msk: r - specular, g - emission, b - ao?
                material_textures.remove(msk_texture)
                if not has_specular:
                    has_specular = True
                    mr_texture = textures_folder + msk_texture + "MR.png"
                    convert_specular_channel_to_metallic_roughness(
                        textures_folder + msk_texture + ".png",
                        mr_texture,
                        0)
                    material.set_metallic_roughness_texture(mr_texture, 0)
                    material.set_metalness(1.0)
                if not has_emission:
                    has_emission = True
                    em_texture = textures_folder + msk_texture + "EM.png"
                    mask_to_emission(textures_folder + msk_texture + ".png", em_texture, 1)
                    material.set_emissive_texture(em_texture, 0)
                    emissive_color = get_emissive_color(mat_data)
                    material.set_emissive(*emissive_color)

            # print(material_textures, "emission " + str(has_emission), "specular " + str(has_specular))
            if len(material_textures) > 0:
                print("\t\tunused textures", material_textures)
        # save scene in another gltf
        to_gltf(scene, "models\\" + file_name)
    else:
        raise Exception("No material file for the model " + file)


def fix_models(temp_models_folder: str, textures_folder: str):
    all_files = []
    for subdir, dirs, files in os.walk(temp_models_folder):
        for file in files:
            if file.endswith(".gltf"):
                # write only gltf files
                all_files.append(os.path.join(subdir, file))
    for file in all_files:
        fix_one_model(file, textures_folder)