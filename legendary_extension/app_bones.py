import requests  # type: ignore

def get_bones(pcc_folder: str, pcc_file: str, actor_name: str):
    req = requests.get("http://localhost:5000/api/bones?pcc=" + pcc_folder + pcc_file + "&res=" + actor_name)
    output = req.text
    bone_names = output.split("#")
    # write bone names to the file
    with open("bones\\" + actor_name + ".txt", "w") as file:
        file.write(str(bone_names))
