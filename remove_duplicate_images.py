#!/bin/usr/env python3
# -*- coding: utf-8 -*-

"""
A CLI (Command Line Interface) tool that scans images in 2 or more directories,
move all non-duplicate images to a folder (a new folder which will be created,
al already existing folder, or one of the folders)

Usage:
python diff.py source_directory_1 source_directory_2 [-d source_directory_3] ...

Requirements:
- Python 3.9+ (https://www.python.org/)
- wand (https://pypi.org/project/Wand/)
- ImageMagick (https://imagemagick.org/script/download.php)
"""

import argparse
import logging as log
import pathlib
import shutil
import sys
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import *

import utils

LOGGER: log.Logger = log.getLogger(__name__)
UNIQUE_IMAGES_DIR: pathlib.Path = pathlib.Path("UNIQUE")
MAX_WORKERS: int = 8


def process_directory_images(directory: pathlib.Path, max_workers: int = MAX_WORKERS) -> Dict[int, List[pathlib.Path]]:
    """
    Scan folder images and calculate the signature of all the images in the directory,
    And maps image signatures are mapped to image files' paths.

    The signatures and image files are mapped in a dictionary,
    where image signatures are the keys, and image files are the values.
    Since there could be one or more duplicate images, the values are stored as
    a list of image files' paths.

    <b>Example:</b>

    <p>
        {
            12355596245 : [path/to/image/foo],
            65214552154 : [path/to/image/bar],
            8563248552 : [path/to/image/ham, path/to/image/spam],
            .
            .
            .
        }
    </p>

    :param directory: path to directory containing images
    :type directory: pathlib.Path
    :param max_workers: maximum number of parallel threads used to compute images
    signatures
    :type max_workers: int
    :return: dictionary containing image signatures as keys, and a list of
    all image files that map to the signature
    :rtype: Dict[int, List[str]]
    """

    LOGGER.debug(f"Scanning directory: {directory} for images")

    images_signatures: Dict[int, List[pathlib.Path]] = defaultdict(list)

    with ThreadPoolExecutor(max_workers=max_workers) as executor_pool:

        submissions: Iterable[Future[Tuple[pathlib.Path, int]]] = [
            executor_pool.submit(utils.sign_image, image) for image in directory.glob("*")
        ]

    for future in as_completed(submissions):

        try:
            result = future.result()

        except Exception as exc:
            LOGGER.info(f"Exception: {exc}")

        else:
            image: pathlib.Path = result[0]
            signature: int = result[1]
            images_signatures[signature].append(image)

    return images_signatures


def main(argc: int = 0, argv: List[str] | None = None) -> int:
    global MAX_WORKERS

    # --------------------------------------------------------------------------
    # Argument Parser
    # --------------------------------------------------------------------------

    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="A CLI (Command Line Interface) tool that scans 2 or more"
                    " directories and remove duplicate image files from them.",
        epilog=f"Example:\n"
               f"%(prog)s path/to/dir/a dir/b dir_c ... more_directories\n"
    )

    # main directory
    arg_parser.add_argument(
        "main_directory",
        help="Path to main directory (may contain images). The main directory is "
             "treated as the output directory when no output directory is supplied",
        type=pathlib.Path
    )

    # directory list
    arg_parser.add_argument(
        "directories",
        help="Paths to directories that contains images to compare. "
             "There MUST be at least 1 directory paths.",
        type=pathlib.Path,
        nargs='+'
    )

    # output directory
    arg_parser.add_argument(
        '-o', "--output",
        help="An optional output directory that will contain all unique images from other directories. "
             "Can be one of the directories that contains images. "
             "If not supplied, the main directory will be used as an output directory.",
        type=pathlib.Path,
        default=None
    )

    # maximum number of threads
    arg_parser.add_argument(
        '-j', "--jobs",
        help="Number of concurrent threads to use to copy images, "
             "a higher number will process images faster but will increase "
             "CPU load and RAM usage. Default: 8",
        type=int,
        default=8
    )

    # verbosity
    arg_parser.add_argument(
        '-v', "--verbosity",
        help="Show more debugging info, values: [0-5]. "
             "0: turn logging off. values [1 to 5]: display more logging information",
        type=int,
        choices=[0, 1, 2, 3, 4, 5],
        default=0
    )

    # --------------------------------------------------------------------------
    # Parse & Validate Command Line Arguments
    # --------------------------------------------------------------------------

    # check if we have enough arguments (at least program_name + 2 directories)
    if argc < 3:
        LOGGER.critical(
            "Not enough arguments. "
            "There must be at least 2 directories.\n"
        )
        arg_parser.print_help(sys.stderr)
        return -1

    # parse command line arguments
    parsed_args: argparse.Namespace = arg_parser.parse_args(argv[1:])

    main_directory: pathlib.Path = parsed_args.main_directory  # main directory
    dir_list: List[pathlib.Path] = parsed_args.directories  # directory list
    output_directory: pathlib.Path = parsed_args.output  # output directory
    MAX_WORKERS = parsed_args.jobs  # maximum number of threads
    verbosity = parsed_args.verbosity

    # configure logging
    if verbosity:
        verbosity = 10 * (6 - verbosity)
        log.basicConfig(level=verbosity)
    else:
        log.basicConfig(level=log.ERROR)

    # add main_directory to start of directory list
    dir_list.insert(0, main_directory)

    # check if directories in dir_list exists
    for directory in dir_list:
        if not directory.is_dir():
            LOGGER.critical(
                f"Path {directory} is not a directory or doesn't exist!\n"
            )
            return -2

    # check output directory
    if output_directory is None:
        output_directory = main_directory
        LOGGER.debug(f"Setting output directory as main directory: {main_directory}")

    if output_directory not in dir_list:
        dir_list.insert(0, output_directory)

    if not output_directory.exists():
        output_directory.mkdir(parents=True)
        LOGGER.debug(f"Creating output directory: {output_directory}")

    # --------------------------------------------------------------------------
    # Scan Images In Directories
    # --------------------------------------------------------------------------

    # start time
    start_time: int = round(time.time())

    files_to_move: List[pathlib.Path] = list()  # files to move to output directory
    duplicate_files: List[pathlib.Path] = list()  # files to remove (delete)

    # image signature map
    images_id: Dict[int, List[pathlib.Path]] = defaultdict(list)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor_pool:

        # process directory images
        results: Iterable[Future[Dict[int, List[pathlib.Path]]]] = [
            executor_pool.submit(
                lambda d: process_directory_images(d, max_workers=MAX_WORKERS),
                directory
            ) for directory in dir_list
        ]

        for future in results:
            try:
                signature_map = future.result()  # images signatures of one of the directories
            except Exception as exc:
                LOGGER.error(f"Exception: {exc}")
            else:
                for (signature, image_files) in signature_map.items():
                    images_id[signature].extend(image_files)

    # check image files to move & delete
    for (signature, image_files) in images_id.items():

        # skip files that are already in output directory
        to_move: pathlib.Path = image_files[0]
        if to_move.parent != output_directory:
            files_to_move.append(image_files[0])
            duplicate_files.extend(image_files[1:])

    # move image files to output directory
    LOGGER.info(f"Moving image files to output directory: {output_directory}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor_pool:
        executor_pool.submit(
            lambda files, output: utils.move_files(files, output, max_workers=MAX_WORKERS),
            files_to_move,
            output_directory
        )

    # delete duplicate image files
    LOGGER.info("Removing duplicate image files")

    for img_file in duplicate_files:
        LOGGER.debug(f"Removing file: {img_file}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor_pool:
        executor_pool.submit(
            lambda files: utils.remove_files(files, max_workers=MAX_WORKERS),
            duplicate_files
        )

    # remove directories
    LOGGER.info("Removing empty directories")
    for directory in dir_list[1:]:
        shutil.rmtree(directory)
        LOGGER.debug(f"Removed directory: {directory}")

    elapsed_time: int = int(time.time() - start_time)
    LOGGER.info(f"Done")

    LOGGER.debug(f"Elapsed time: {elapsed_time}")

    return 0


if __name__ == '__main__':
    arg_values: List[str] = sys.argv
    arg_count: int = len(arg_values)

    ret: int = main(arg_count, arg_values)

    sys.exit(ret)
