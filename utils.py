#!/bin/usr/env python3
# -*- coding: utf-8 -*-

"""
Python module that provides utility functions for "RemoveDuplicateImages" package
"""

import logging as log
import os
import pathlib
import random
import shutil
import stat
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import *

from PIL import Image
from imagehash import phash

LOGGER: log.Logger = log.getLogger(__name__)
MAX_WORKERS: int = 8


def get_image_signature(image_path: Union[str, pathlib.Path]) -> int:
    """
    Calculates a unique value for a given image, based on the image raw pixels
    value. Not taking into account the image name, path or metadata. Two images
    of different names & formats but contain the same picture will have the same
    signature.

    :param image_path: path to image
    :type image_path: str, or pathlib.Path
    :return: calculated image signature
    :rtype: int
    """
    if isinstance(image_path, str):
        image_path = pathlib.Path(image_path)

    if not image_path.is_absolute():
        image_path = image_path.absolute()

    LOGGER.debug(f"Opening image: {str(image_path)}")

    with Image.open(image_path) as img:
        return phash(img)

    # with image.Image(filename=image_path) as img:
    #     return img.signature


def sign_image(img: pathlib.Path) -> Tuple[pathlib.Path, int]:
    """
    Gets image signature, a unique number that depends on image pixels' values

    :param img: path to image file
    :type img: pathlib.Path
    :return: a tuple of (image path, image signature)
    :rtype: Tuple[str, int]
    """
    return img, get_image_signature(img)


def move_file_to_dir(src_file: pathlib.Path, dst_dir: pathlib.Path, replace: bool = False) -> pathlib.Path:
    """
    Moves a file (or directory) into destination directory.
    If a file already exists with the same name, it will be replaced if replace is True.

    :param src_file: path to file (or directory) to move
    :type src_file: pathlib.Path
    :param dst_dir: path to directory which the file will be moved into
    :type dst_dir: pathlib.Path
    :param replace: replace policy When moving a file and a file already exists with the same name.
    :type replace: bool
    :return: new path to the file after it was moved
    :rtype: pathlib.Path
    """

    LOGGER.debug(f"Moving file {src_file} to {dst_dir}")

    dst_file: pathlib.Path = dst_dir.joinpath(src_file.name)

    # if a file with the same name already exists in destination directory
    # rename source file
    if dst_file.is_file() and not replace:
        new_name: str = f"{src_file.stem}{random.randint(0, 10)}"
        LOGGER.debug(f"Renaming image {src_file} to {new_name}")
        src_file = src_file.rename(src_file.with_stem(new_name))

    # dst_file: pathlib.Path = shutil.move(src_file, dst_dir)
    dst_file: pathlib.Path = shutil.move(src_file, dst_dir)

    return dst_file


def move_files(file_list: List[pathlib.Path], dst_dir: pathlib.Path, max_workers: int = MAX_WORKERS) -> None:
    """
    Move files to destination directory

    :param file_list: list of files to move
    :type file_list: List[pathlib.Path]
    :param dst_dir: destination directory to move files into
    :param max_workers: maximum number of threads to move files
    :type max_workers: int
    :type dst_dir: pathlib.Path
    :return: None
    :rtype: None
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor_pool:
        submissions: Iterable[Future[None]] = [
            executor_pool.submit(move_file_to_dir, src_file, dst_dir) for src_file in file_list
        ]

    for future in as_completed(submissions):
        try:
            result = future.result()
        except Exception as exc:
            LOGGER.error(f"Exception: {exc}")


def remove_files(file_list: List[pathlib.Path], max_workers: int = MAX_WORKERS) -> None:
    """
    Remove given list of files

    :param file_list: list of files to remove
    :type file_list: List[pathlib.Path]
    :param max_workers: maximum number of worker threads
    :type max_workers: int
    :return: None
    :rtype: None
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor_pool:
        submissions = [
            executor_pool.submit(os.remove, src_file) for src_file in file_list
        ]

        for future in as_completed(submissions):
            try:
                result = future.result()
            except Exception as exc:
                LOGGER.error(f"Exception: {exc}")


if __name__ == '__main__':
    pass
