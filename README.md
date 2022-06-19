# Remove duplicate Images

A command line interface tool to remove duplicate image files from multiple directories. An image file is considered a duplicate, if there is another image **with the exact same** image content; i.e. both files contain the same image -pixel for pixel- even if the file names, metadata, or extension are different. The tool is not good to remove almost similar image files; i.e. files with the same image but different dimensions, or files with the same image but cropped along one or more dimensions (image files with high degree with similarity). 

The tool uses [ImageMagick](https://imagemagick.org/index.php) to check image files for duplicates, by using ImageMagick's image signature. ImageMagick calculates image signature by hashing the image's pixel values.

<!-- MarkdownTOC -->

<!-- /MarkdownTOC -->

