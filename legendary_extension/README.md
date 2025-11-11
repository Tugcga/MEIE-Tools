### Legendary Explorer extension

This part of the repository contains extensions for [Legendary Explorer](https://github.com/ME3Tweaks/LegendaryExplorer). It allows the use of Python to extract static meshes and textures from game resources. While this can be done manually, each game level contains many static meshes with different transforms, making Python very helpful.


### AppExtension.cs

This code should be added to the ```App.cs``` file of the Legendary Explorer. After adding it, the application must be rebuilt. The implementation adds a web server that can receive requests from Python, process the data on the C# side, and return the response back to Python.

The ```App``` class should be extended by two methods:
```csharp
protected override void OnStartup(StartupEventArgs e)
{
    base.OnStartup(e);
    _server.Start(5000);
}

protected override void OnExit(ExitEventArgs e)
{
    _server.Stop();
    base.OnExit(e);
}
```

And also add a static variable to the ```App``` class

```csharp
WebServer _server = new WebServer();
```

### Python applications

Several Python applications are included, which can be used in different scenarios for extracting level data from game resources using Legendary Explorer.

#### Level information (```app_level.py```)

```def get_locations(pcc_folder: str, location_pcc: str)```

Store a text file with the same name as the in-game location in the ```locations``` folder. This file should contain a list of all linked resource files.

Parameters:
* ```pcc_folder``` - full path to the folder with game resource, for example ```G:/Mass Effect 2/BioGame/CookedPC/```
* ```location_pcc``` - the name of the location file, for example ```BioP_ProCer.pcc```

```def get_static_meshes_for_level(pcc_folder: str, level_pcc: str)```

Extract the names of static meshes from all files linked to the input level. Output these names into text files inside the directory ```static_names```.

Parameters:
* ```pcc_folder``` - full path to the folder with game resource
* ```location_pcc``` - the name of the location file. All linked locations are obtained from an already built file in ```locations``` folder

```def get_static_actors_for_level(pcc_folder: str, level_pcc: str)```

A similar function, but it returns the names of static actors in the input level. Store the output in a text file within the ```locations_actors``` directory.

```def export_level_meshes(pcc_folder: str, umodel_path: str, temp_models_path: str, textures_folder: str, level_pcc: str)```

Export all static meshes from the input level into glTF format using the UModel application as the exporter. UModel exports the meshes to glTF and stores them in the ```temp_models_path``` directory. However, this process lacks proper texture information. Therefore, this function also saves all required material data into text files with a ```.mat``` extension in the same temporary folder.

Parameters:
* ```pcc_folder``` - full path to the folder with game resource
* ```umodel_path``` - full path to ```umodel.exe```
* ```temp_models_path``` - full path to the temp folder for store material data
* ```textures_folder``` - full path to the folder. It will be used by UModel for export mesh textures
* ```level_pcc``` - the name of the location file


#### Fix models (```app_models.py```)

```def fix_models(temp_models_folder: str, textures_folder: str)```

Fix all models previously exported by UModel. For each model, it finds the required textures, creates a proper glTF material, and resaves the model with the correct structure. This function requires additional Python modules: [```PIL```](https://pypi.org/project/pillow/), [```numpy```](https://numpy.org/) and [```py3dscene```](https://github.com/Tugcga/py3dscene).

Parameters:
* ```temp_models_folder``` - full path to the folder where store the result of previous exports
* ```textures_folder``` - full path to the folder for output textures of fixed models


#### Actor bones (app_bones.py)

```def get_bones(pcc_folder: str, pcc_file: str, actor_name: str)```

For each actor, find the list of skin bones and store it in the ```bones``` folder. These bone lists will allow later to find compatible animations for each actor.

Parameters:
* ```pcc_folder``` - full path to the folder with game resource
* ```pcc_file``` - name of the pcc-file
* ```actor_name``` - name of the actor in the input pcc-file


#### Animations (py_animations.py)

```def export_all_animations(pcc_folder: str)```

Export all animation data from all resource files in the input directory. For each animation found in the resources, the function creates a text file in the ```animations``` directory and stores the keyframes of all bones for that animation.

Parameters:
* ```pcc_folder``` - full path to the folder with game resource

```def find_compatible_animations(actor: str)```

For a given actor name, find all compatible animations and store the list of their names in a text file named ```<actor>_compat_anims.txt```. An animation is compatible with the actor if its bone list exactly matches the actor's bone list.

Parameters:
* ```actor``` - the actor's name
