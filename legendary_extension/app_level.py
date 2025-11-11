import requests  # type: ignore
import os


def change_extension(file_path: str, ext: str) -> str:
    '''Change the extension of the file
    '''
    parts = file_path.split(".")
    return ".".join(parts[:-1]) + "." + ext


def get_locations(pcc_folder: str, location_pcc: str):
    '''location_pcc is a filename for the location (BioP_ProCer.pcc, for example)

    this function obtain all linked pcc-files required for the input location
    and save *.txt file with names of these pcc-files
    '''
    req = requests.get("http://localhost:5000/api/locations?pcc=" + pcc_folder + location_pcc)
    output = req.text
    # extract only file names, without default directory
    parts = output.split("#")
    names = []
    for part in parts:
        ptr = part.find(pcc_folder)
        if ptr == 0:
            names.append(part[len(pcc_folder):])
    names.append(names.pop(0))
    print(names)
    # save names in the file
    with open("locations\\" + change_extension(location_pcc, "txt"), "w") as file:
        file.write(str(names))


def get_static_meshes_list(pcc_folder: str, pcc_file: str) -> list[str]:
    '''pcc_file is just a file, not the whole path
    '''
    req = requests.get("http://localhost:5000/api/static?pcc=" + pcc_folder + pcc_file)
    output = req.text
    if len(output) == 0:
        return [""]
    else:
        return output.split("#")


def get_static_actors_list(pcc_folder: str, pcc_file: str):
    req = requests.get("http://localhost:5000/api/actors?pcc=" + pcc_folder + pcc_file)
    output = req.text
    return output.split("#")


def get_static_meshes_for_level(pcc_folder: str, level_pcc: str):
    '''level_pcc is the initial name of the pcc file

    as a result of this function, we create several txt-files in static_names folder
    '''
    location_data_file_path = "locations\\" + change_extension(level_pcc, "txt")
    if os.path.exists(location_data_file_path):
        with open(location_data_file_path, "r") as file:
            pccs = eval(file.read())
            for pcc_name in pccs:
                pcc_list = get_static_meshes_list(pcc_folder, pcc_name)
                # store the list with static meshes names in individual file
                if len(pcc_list) > 0:
                    with open("static_names\\" + change_extension(pcc_name, "txt"), "w") as list_file:
                        list_file.write(str(pcc_list))
                else:
                    print(pcc_name, "empty static meshes list")
    else:
        print("No data for the location", level_pcc)


def get_static_actors_for_level(pcc_folder: str, level_pcc: str):
    location_data_file_path = "locations\\" + change_extension(level_pcc, "txt")
    if os.path.exists(location_data_file_path):
        with open(location_data_file_path, "r") as file:
            pccs = eval(file.read())
            level_actors = {}  # key - pcc-file, value - array with names and transforms
            for pcc_name in pccs:
                pcc_actors = get_static_actors_list(pcc_folder, pcc_name)
                actors_count = len(pcc_actors) // 2
                entries = []
                for actor_index in range(actors_count):
                    actor_name = pcc_actors[2 * actor_index]  # static mesh object name
                    actor_str = pcc_actors[2 * actor_index + 1]  # string with transform matrix
                    parts = actor_str.split("%")
                    matrix_list = []
                    for i in range(4):
                        row = []
                        for j in range(4):
                            row.append(float(parts[4 * i + j]))
                        matrix_list.append(tuple(row))
                    tfm_matrix = tuple(matrix_list)
                    entries.append((actor_name, tfm_matrix))
                if len(entries) > 0:
                    level_actors[pcc_name] = entries
            with open("locations_actors\\" + change_extension(level_pcc, "txt"), "w") as out_file:
                out_file.write(str(level_actors))


def export_static_mesh(pcc_folder: str, umodel_path: str, temp_models_path: str, textures_folder: str, pcc_file: str, mesh_name: str):
    req = requests.get("http://localhost:5000/api/export?pcc=" + pcc_folder + pcc_file + "&name=" + mesh_name + "&umodel=" + umodel_path + "&ext=" + "gltf" + "&out=" + temp_models_path + "&tex=" + textures_folder)
    output = req.text
    # in the export process we save gltf file and also textures from the material
    # next we should store material data, returned by the request
    # store it in the same directory as a raw gltf
    model_folder = temp_models_path + "\\" + ".".join(pcc_file.split(".")[:-1]) + "\\StaticMesh3\\"
    if os.path.exists(model_folder):
        with open(model_folder + mesh_name + ".mat", "wt") as file:
            materials = []
            material: dict[str, int | str | list[str]] | None = None
            iterator = 0
            parts = output.split("#")
            print(parts)
            mode = 0
            while iterator < len(parts):
                part = parts[iterator]
                ind_start = part.find(r"%index")
                if ind_start == 0:
                    # this is start of the material section
                    if material is not None:
                        materials.append(material)
                    mat_index = int(part[6:])
                    material = {"index": mat_index}
                    mode = 0
                else:
                    # we parse material section
                    if mode == 0:
                        if part == "export":
                            if material is not None:
                                material["name"] = parts[iterator + 1]
                            iterator += 1
                        elif part == "textures":
                            mode = 1
                            if material is not None:
                                material["textures"] = []
                    elif mode == 1:
                        if part == "expressions":
                            mode = 2
                            material["parameters"] = []
                        else:
                            if material is not None:
                                material["textures"].append(part)  # type: ignore
                    elif mode == 2:
                        exp_name = part
                        exp_type = parts[iterator + 1]
                        exp_string = parts[iterator + 2]
                        iterator += 2
                        if exp_type == "scalar":
                            exp_value = float(exp_string)
                        elif exp_type == "vector":
                            exp_value = tuple(float(v) for v in exp_string.split("%"))
                        else:
                            exp_value = exp_string

                        material["parameters"].append((exp_name, exp_type, exp_value))  # type: ignore
                iterator += 1
            materials.append(material)
            # save material file
            file.write(str(materials))
    else:
        print("model", mesh_name, "from", pcc_file, "does not exported")


def export_level_meshes(pcc_folder: str, umodel_path: str, temp_models_path: str, textures_folder: str, level_pcc: str):
    '''export all static meshes from all pcc-files, connected with the given level
    '''
    location_data_file_path = "locations\\" + change_extension(level_pcc, "txt")
    if os.path.exists(location_data_file_path):
        with open(location_data_file_path, "r") as file:
            pccs = eval(file.read())
            for pcc in pccs:
                # open file with list of static meshes
                static_meshes_file = "static_names\\" + change_extension(pcc, "txt")
                if os.path.exists(static_meshes_file):
                    with open(static_meshes_file) as sm_file:
                        names = eval(sm_file.read())
                        for name in names:
                            print(pcc, name)
                            export_static_mesh(pcc_folder, umodel_path, temp_models_path, textures_folder, pcc, name)
