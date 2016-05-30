from fb_albums import get_albums
from facial_recognition import face_detect
from os import listdir
from PIL import Image
import itertools
import sys
from collections import namedtuple

PHOTOS_PATH = 'albums2'
LOST_FACE_FACTOR = 10

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
	print "Image Size: {sz}".format(sz=size)

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
	if size[1]*2/3 - 1 <= size[0] <= size[1]*2/3 + 1 or size[0]*2/3 - 1 <= size[1] <= size[0]*2/3 + 1:
		print "GOOD SIZE"
	else:
		print "##############"
		print "## BAD SIZE ##"
		print "##############"
	print "- - - - - "

def attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces):
	lost_face_area = original_image_overlap - total_face_overlap(new_box, faces)
	print "Lost face area scaled: {area}".format(area=lost_face_area)
	print "Lost image area: {area}".format(area=lost_area)
	new_crop = Crop(box=new_box, score= ((LOST_FACE_FACTOR * lost_face_area) + lost_area))

	return new_crop if new_crop.score <= best_crop.score else best_crop

#faces as (x, y, w, h)
def process_bad_proportions(original_image, size, faces):

	width, height = size
	original_box=(0, 0, width, height)
	original_image_overlap = total_face_overlap(original_box, faces)

	#(left, upper, right, lower) All four coordinates are measured 
	#from the top/left corner, and describe the distance from that 
	#corner to the left edge, top edge, right edge and bottom edge.

	best_crop = Crop(box= original_box, score= sys.maxint)

	boxes = []

	new_height = 2*size[0]/3
	if(new_height < height):
		lost_area = width * (height - new_height)
		boxes.append(Crop(box=(0, 0, width, new_height), score=lost_area))
		boxes.append(Crop(box=(0, height - new_height, width, height), score=lost_area))
		boxes.append(Crop(box=(0, (height - new_height)/2, width, height - (height - new_height)/2), score=lost_area))

	new_height = 3*size[0]/2
	if(new_height < height):
		lost_area = width * (height - new_height)
		boxes.append(Crop(box=(0, 0, width, new_height), score=lost_area))
		boxes.append(Crop(box=(0, height - new_height, width, height), score=lost_area))
		boxes.append(Crop(box=(0, (height - new_height)/2, width, height - (height - new_height)/2), score=lost_area))

	new_width = 2*size[1]/3  
	if(new_width < width):
		lost_area = height * (width - new_width)
		boxes.append(Crop(box=(0, 0, new_width, height), score=lost_area))
	 	boxes.append(Crop(box=(width - new_width, 0, width, height), score=lost_area))
	 	boxes.append(Crop(box=((width - new_width)/2, 0,  width - (width - new_width)/2, height), score=lost_area))

	new_width = 3*size[1]/2
	if(new_width < width):
		lost_area = height * (width - new_width)
		boxes.append(Crop(box=(0, 0, new_width, height), score=lost_area))
	 	boxes.append(Crop(box=(width - new_width, 0, width, height), score=lost_area))
	 	boxes.append(Crop(box=((width - new_width)/2, 0,  width - (width - new_width)/2, height), score=lost_area))

	for new_crop in boxes:
		best_crop = attempt_crop(new_crop.box, original_image_overlap, new_crop.score, best_crop, faces)


	# new_height = 3*size[0]/2
	# #new_height = 2*size[0]/3
	# if(new_height < height):
	# 	lost_area = width * (height - new_height)

	# 	print "ATTEMPT CROP 1: fix width, crop height to 2/3width - crop from bottom"
	# 	new_box = (0, 0, width, new_height)
	# 	best_crop = attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces)
	# 	new_image = original_image.crop(box=new_box)
	# 	IS_GOOD(new_image)

	# 	print "ATTEMPT CROP 2: fix width, crop height to 2/3width - crop from top"
	# 	new_box=(0, height - new_height, width, height)
	# 	best_crop = attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces)
	# 	new_image = original_image.crop(box=new_box)
	# 	IS_GOOD(new_image)

	# 	print "ATTEMPT CROP 3: fix width, crop height to 2/3width - crop halfway from top & bottom"
	# 	new_box=(0, (height - new_height)/2, width, height - (height - new_height)/2)
	# 	best_crop = attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces)
	# 	new_image = original_image.crop(box=new_box)
	# 	IS_GOOD(new_image)




	# new_width = 2*size[1]/3                                             
	# if(new_width < width):
	# 	lost_area = height * (width - new_width)

	# 	print "ATTEMPT CROP 4: fix height, crop width to 2/height - crop from left"
	# 	new_box=(0, 0, new_width, height)
	# 	best_crop = attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces)


	# 	print "ATTEMPT CROP 5: fix height, crop width to 2/height - crop from right"
	# 	new_box=(width - new_width, 0, width, height)
	# 	best_crop = attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces)

	# 	print "ATTEMPT CROP 6: fix height, crop width to 2/height - crop halfway from left & right"
	# 	new_box=((width - new_width)/2, 0,  width - (width - new_width)/2, height)
	# 	best_crop = attempt_crop(new_box, original_image_overlap, lost_area, best_crop, faces)


	new_image = original_image.crop(box=best_crop.box)
	new_image.show()
	IS_GOOD(new_image)




if __name__ == '__main__':
	Crop = namedtuple('Crop', ['box', 'score'])
	download_photos()
	load_photos()



