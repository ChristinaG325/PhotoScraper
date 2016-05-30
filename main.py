#!/usr/bin/env python
"""
File: main.py
---------------
Assignment 4: Final Project - PhotoScraper
Course: CS 41
Name: Christina Gilbert
SUNet: christyg

This script pulls a user's posted photos from all photo albums, saves
them to the filesystem, and crops the photos to be 4x6 in such a way
to minimize both the total area cropped from the photo and the area of
faced cropped from the photo.

Square photos are padded with black space to become 4x6 photos.

--------------
A note on box coordinates: PIL uses box bounds in the format

(left, upper, right, lower)

where all four coordinates are measured from the top/left corner,
and describe the distance from that corner to the left edge, top
edge, right edge and bottom edge.

However, opencv represents face coordinate as

(x, y, w, h)

where x,y is the uppper lefthand corner, and w and h are the width
and height of the box. In the comments, I will refer to the formatting
of the box tuple as either (left, upper, right, lower) or (x, y, w, h)
"""
from os import listdir
import sys
from collections import namedtuple

from PIL import Image

from fb_albums import get_albums
from facial_recognition import face_detect

PHOTOS_PATH = 'albums'
LOST_FACE_FACTOR = 10


def download_photos():
    """ For every album for a given facebook user, downloads all photos
    from all posted album to the filesystem to a folder defined by
    PHOTOS_PATH
    """

    token_file = open('access_token', 'r')
    token = token_file.read()
    api_url = "https://graph.facebook.com/v2.1/"
    get_albums.download(token, PHOTOS_PATH)


def load_photos():
    """ Processes photos in all albumbs pulled from facebook
    """

    folders = listdir(PHOTOS_PATH)
    for folder in folders:
        photos = listdir(PHOTOS_PATH + "/" + folder)
        for photo in photos:
            process_photo(PHOTOS_PATH + "/" + folder + "/" + photo)


def process_photo(filename):
    """ Given a photo, saves a 4x6 version of the photo in its place.
    Given a square photo, adds padding. Given any other dimensions,
    crops the photo. Saves 4x6 to filesystem in place of original
    photo

    @param filename: path to image
    """

    try:
        original_image = Image.open(filename)
    except:
        print "Unable to load image {image}".format(image=filename)

    size = original_image.size

    # Case 1: Image is 4x6. Nothing to be done.
    if size[0] == size[1] * 2 / 3 or size[1] == size[0] * 2 / 3:
        pass

    # Case 2: Image is a square. Pad it with whitespace to make it a 4x6
    elif size[0] == size[1]:
        padded_square = process_square(original_image, size)
        padded_square.save(filename)

    # Case 3: Image has any other dimensions
    else:
        faces = face_detect.get_faces(filename)

        cropped_image = process_bad_proportions(original_image, size, faces)
        cropped_image.save(filename)

# box bounds as as (x, y, w, h)


def overlap_area(box1, box2):
    """ Calculates the overlap between all the bounded boxes and the cropped
    version of the photo.

    From http://math.stackexchange.com/questions/99565/simplest-way-to
    -calculate-the-intersect-area-of-two-rectangles

    @param box1, box2: boxes to find overlap
    @return: area of overlap between two boxes
    """
    x11, y11, w1, h1 = box1
    x12 = x11 + w1
    y12 = y11 + h1

    x21, y21, w2, h2 = box2
    x22 = x21 + w2
    y22 = y21 + h2

    x_overlap = max(0, min(x12, x22) - max(x11, x21))
    y_overlap = max(0, min(y12, y22) - max(y11, y21))
    return x_overlap * y_overlap


def total_face_overlap(cropped_image, faces):
    """ Calculates total overlap between a potential crop of the photo and
    all faces in the photo

    @param cropped_image: bounds of the potential crop in format
    (left, upper, right, lower)
    @return: area of overlap between two boxes
    """

    overlap_sum = 0
    for face in faces:
        overlap_sum += overlap_area(cropped_image, face)

    return overlap_sum


def process_square(original_image, size):
    """ Pads a square photo to make it a 4x6

    @param original_image: original square photo
    @param size: dimensions of original_image
    @return: Paded 4x6 image
    """

    width, height = size
    new_image = original_image.crop(box=(0, 0, width * 3 / 2, height))
    return new_image


def valid4x6(image):
    """Debugging function to determine if an image is a valid 4x6.
    Prints result

    @param image: Image to determine if 4x6
    """

    size = image.size
    print "SIZE: {sz}".format(sz=size)
    if size[1] * 2 / 3 - 1 <= size[0] <= size[1] * 2 / 3 + \
            1 or size[0] * 2 / 3 - 1 <= size[1] <= size[0] * 2 / 3 + 1:
        print "GOOD SIZE"
    else:
        print "##############"
        print "## BAD SIZE ##"
        print "##############"


def attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces):
    """Calculates the cost of a crop given the amount of area lost from the image and
    the total area of the faces lost

    @param new_box: coordinates of the potential crop as (left, upper, right, lower)
    @param original_image_overlap: the overlap of the original image with all faces
    @param lost_area: the amount of area cropped from the photo
    @param best_crop: Crop of the best score we've encountered thus far
    @param faces: list of coordinates of all faces in photo as (x, y, w, h)
    @return: score associated with this crop
    """

    lost_face_area = original_image_overlap - \
        total_face_overlap(new_box, faces)
    new_crop = Crop(
        box=new_box, score=(
            (LOST_FACE_FACTOR * lost_face_area) + lost_area))

    return new_crop if new_crop.score <= best_crop.score else best_crop


def process_bad_proportions(original_image, size, faces):
    """Given an image with bad proportions, calculates the best 4x6 crop to minimize photo
    area and in particular, face area, lost from the photo

    @param original_image: image to be cropped
    @param size: size of original_image
    @param faces: list of coordinates of all faces in photo as (x, y, w, h)
    """

    width, height = size
    original_box = (0, 0, width, height)
    original_image_overlap = total_face_overlap(original_box, faces)

    best_crop = Crop(box=original_box, score=sys.maxsize)

    boxes = []

    new_height = 2 * size[0] / 3
    if(new_height < height):
        lost_area = width * (height - new_height)
        boxes.append(Crop(box=(0, 0, width, new_height), score=lost_area))
        boxes.append(
            Crop(
                box=(
                    0,
                    height -
                    new_height,
                    width,
                    height),
                score=lost_area))
        boxes.append(Crop(box=(0, (height - new_height) / 2, width,
                               height - (height - new_height) / 2), score=lost_area))

    new_height = 3 * size[0] / 2
    if(new_height < height):
        lost_area = width * (height - new_height)
        boxes.append(Crop(box=(0, 0, width, new_height), score=lost_area))
        boxes.append(
            Crop(
                box=(
                    0,
                    height -
                    new_height,
                    width,
                    height),
                score=lost_area))
        boxes.append(Crop(box=(0, (height - new_height) / 2, width,
                               height - (height - new_height) / 2), score=lost_area))

    new_width = 2 * size[1] / 3
    if(new_width < width):
        lost_area = height * (width - new_width)
        boxes.append(Crop(box=(0, 0, new_width, height), score=lost_area))
        boxes.append(
            Crop(
                box=(
                    width -
                    new_width,
                    0,
                    width,
                    height),
                score=lost_area))
        boxes.append(Crop(box=((width - new_width) / 2, 0, width - \
                     (width - new_width) / 2, height), score=lost_area))

    new_width = 3 * size[1] / 2
    if(new_width < width):
        lost_area = height * (width - new_width)
        boxes.append(Crop(box=(0, 0, new_width, height), score=lost_area))
        boxes.append(
            Crop(
                box=(
                    width -
                    new_width,
                    0,
                    width,
                    height),
                score=lost_area))
        boxes.append(Crop(box=((width - new_width) / 2, 0, width - \
                     (width - new_width) / 2, height), score=lost_area))

    for new_crop in boxes:
        best_crop = attempt_crop(
            new_crop.box,
            original_image_overlap,
            new_crop.score,
            best_crop,
            faces)

    new_image = original_image.crop(box=best_crop.box)

    return new_image

if __name__ == '__main__':
    Crop = namedtuple('Crop', ['box', 'score'])
    download_photos()
    load_photos()
