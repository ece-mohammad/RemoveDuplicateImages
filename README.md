# Remove duplicate Images

A command line interface tool to remove duplicate image files from multiple directories. An image file is considered a duplicate, if there is another **nearly identical image**; an image files that contain the same image but with slight changes in image color content (like contrast, brightness, etc). Image scale, aspect ration, filename, metadata and extension can be different.

The tool uses perceptual image hashing (`pHash`) algorithm, from [ImageHash](https://github.com/JohannesBuchner/imagehash), to identify image files. It's much faster than calculating hash (like sha, md5) over image content. 
Also the ability to detect nearly identical images is a plus because, two images with only `1` different pixel, will have `2` completely different hashes, and both will be considered unique images.

<!-- MarkdownTOC -->

1. [Requirements](#requirements)
1. [Usage](#usage)
1. [Examples](#examples)

<!-- /MarkdownTOC -->


<a id="requirements"></a>
## Requirements


- Python 3.10
- Python Imaging Library (PIL)
- ImageHash


<a id="usage"></a>
## Usage

```text
usage: remove_duplicate_images.py [-h] [-o OUTPUT] [-j JOBS] [-v {0,1,2,3,4,5}] main_directory directories [directories ...]

positional arguments:
  main_directory        Path to main directory (may contain images). The main directory is treated as the output directory when no output directory is supplied
  directories           Paths to directories that contains images to compare. There MUST be at least 1 directory paths.

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        An optional output directory that will contain all unique images from other directories. Can be one of the directories that contains images. If the directory is not found, it ill be created. If not supplied, the main directory will be used as an output directory.
  -j JOBS, --jobs JOBS  Number of concurrent threads to use to copy images, a higher number will process images faster but will increase CPU load and RAM usage. Default: 8
  -v {0,1,2,3,4,5}, --verbosity {0,1,2,3,4,5}
                        Show more debugging info, values: [0-5]. 0: turn logging off. values [1 to 5]: display more logging information. Default: 1
```


<a id="examples"></a>
## Examples

```text
remove_duplicate_images.py foo bar
```
- Scan directories `foo` and `bar`, move all unique images into `foo` and delete everything else (including directory `bar`)

```text
remove_duplicate_images.py foo bar -o baz
```
- Scan directories `foo`, `bar` and `baz`, move all unique images into `baz` and delete everything else (including directories `foo`, `bar`)

```text
remove_duplicate_images.py foo bar -j 4
```
- Scan directories `foo` and `bar`, move all unique images into `foo` and delete everything else (including directory `bar`), use at most 4 threads

```text
remove_duplicate_images.py foo bar -v 5
```
- Scan directories `foo` and `bar`, move all unique images into `foo` and delete everything else (including directory `bar`), with max verbosity

