from fb_albums import get_albums
from facial_recognition import face_detect
from os import listdir
from PIL import Image
import itertools
import sys

PHOTOS_PATH = 'albums2'

def download_photos():
	token_file = open('API_KEYS.txt', 'r')
	token = token_file.read()
	api_url = "https://graph.facebook.com/v2.1/"
	get_albums.download(token, PHOTOS_PATH)

def load_photos():
	folders = listdir(PHOTOS_PATH)
	for folder in folders:
		photos = listdir(PHOTOS_PATH + "/" + folder)
		for photo in photos:
			process_photo(PHOTOS_PATH + "/" + folder + "/" + photo)
		break

def process_photo(filename):

	try:
		original_image = Image.open(filename)
	except:
		print "Unable to load image {image}".format(image=filename)

	size = original_image.size
	print size

	#Case 1: Image is 4x6. Nothing to be done.
	if size[0] == size[1]*2/3 or size[1] == size[0]*2/3:
		pass

	#Case 2: Image is a square. Extention: Pad it with whitespace to make it a 4x6
	#currently does nothing
	elif size[0] == size[1]:
		process_square(original_image, size)
		return

	else:
		faces = face_detect.get_faces(filename)

		print "##############"
		print filename 
		print "##############"
		process_bad_proportions(original_image, size, faces)


#box bounds as as (x, y, w, h)
def overlap_area(box1, box2):
	""" From http://math.stackexchange.com/questions/99565/simplest-way-to
	-calculate-the-intersect-area-of-two-rectangles
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
	overlap_sum = 0
	for face in faces:
		overlap_sum += overlap_area(cropped_image, face)

	return overlap_sum

def process_square(original_image, size):
	pass

def IS_GOOD(image):

	size = image.size
	print "SIZE: {sz}".format(sz=size)
	if size[0] == size[1]*2/3 or size[1] == size[0]*2/3:
		print "GOOD SIZE"
	else:
		print "##############"
		print "## BAD SIZE ##"
		print "##############"
	print "- - - - - "

#faces as (x, y, w, h)
def process_bad_proportions(original_image, size, faces):

	width, height = size
	box=(0, 0, width, height)
	original_image_overlap = total_face_overlap(box, faces)

	#(left, upper, right, lower) All four coordinates are measured 
	#from the top/left corner, and describe the distance from that 
	#corner to the left edge, top edge, right edge and bottom edge.

	best_box = box
	best_score = sys.maxint

	new_height = 2*size[0]/3
	if(new_height < height):
		lost_area = width * (height - new_height)

		#ATTEMPT CROP 1: fix width, crop height to 2/3width - crop from bottom
		box=(0, 0, width, new_height)
		lost_face_area = original_image_overlap - total_face_overlap(box, faces)
		print "LOST FACE AREA: {area}".format(area=lost_face_area)

		#ATTEMPT CROP 2: fix width, crop height to 2/3width - crop from top
		box=(0, height - new_height, width, height)

		#ATTEMPT CROP 3: fix width, crop height to 2/3width - crop halfway from top & bottom
		box=(0, (height - new_height)/2, width, height - (height - new_height)/2)

	else:
		print "BAD NEW HEIGHT~~~~"
	

	new_width = 2*size[1]/3                                             
	if(new_width < width):
		cropped_pixels = height * (width - new_width)

		#ATTEMPT CROP 4: fix height, crop width to 2/height - crop from left
		newImage = original_image.crop(box=(0, 0, new_width, height))
		IS_GOOD(newImage)

		#ATTEMPT CROP 5: fix height, crop width to 2/height - crop from right
		newImage = original_image.crop(box=(width - new_width, 0, width, height))
		IS_GOOD(newImage)

		#ATTEMPT CROP 6: fix height, crop width to 2/height - crop halfway from left & right
		newImage = original_image.crop(box=((width - new_width)/2, 0,  width - (width - new_width)/2, height))
		IS_GOOD(newImage)
	else:
		print "BAD NEW WIDTH~~~~"



if __name__ == '__main__':
	download_photos()
	load_photos()



