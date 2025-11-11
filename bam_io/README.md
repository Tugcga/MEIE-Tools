### Bam IO Python module

This module introduces support for Bam V2 files, allowing them to be loaded, edited, and saved. It is built on top of the [```PIL```](https://pypi.org/project/pillow/) Python module and also requires the [```texture2ddecoder```](https://pypi.org/project/texture2ddecoder/) module to be installed. The ```texture2ddecoder``` module is used for reading image PVRZ pages linked to the BAM file. For writing PVRZ pages, the Windows console application ```texconv.exe``` is used. Therefore, saving BAM files only works on Windows. This application is used for decoding images in DXT1 or DXT5 format.

### How to use

Create bam-object

```python
bam = BamV2()
```

Create several frames. Each frame requires dimensions and center coordinates

```python
frame_00 = Frame(32, 32, 0, 0)
frame_01 = Frame(32, 32, 0, 0)
```

Add images to each frame

```python
frame_00.set_image(Image.new("RGB", (32, 32), "#aaa"))
frame_01.set_image(Image.new("RGB", (32, 32), "#444"))
```

Add frames to the bam

```python
frame_00_index = bam.add_frame(frame_00)
frame_01_index = bam.add_frame(frame_01)
```

Add a cycle

```python
cycles_index = bam.add_cycle()
```

Add frames to the cycle

```python
bam.add_frame_to_cycle(cycles_index, frame_00_index)
bam.add_frame_to_cycle(cycles_index, frame_01_index)
```

Save the bam to the file

```python
bam_to_file(bam, "output.bam", 1, TextureFormat.DXT1)
```

### IO functions

```def bam_to_file(bam: BamV2, output_path: str, pvrz_prefix: int, txt_format: TextureFormat):```

This function saves the content of a ```BamV2``` object to a BAM file. 

Parameters:
* ```bam``` - the source object
* ```output_path``` - the full path to the output file (with the ```.bam``` extension)
* ```pvrz_prefix``` - a non-zero integer used to store PVRZ pages in separate files named ```MOSX***.pvrz```, where ```X``` is the ```pvrz_prefix```
* ```txt_format``` - the format for texture encoding: ```DXT1``` or ```DXT5```. Use ```DXT5``` if the frames use an alpha channel, for non-transparent frames, use ```DXT1```


```def bam_from_file(file_path: str) -> BamV2```

This function reads an external BAM file and creates a ```BamV2``` object from its contents.

Parameters:
* ```file_path``` - the full path to the source BAM file
