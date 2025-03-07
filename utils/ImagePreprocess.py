import numpy as np
import scipy as sp
import skimage as ski

import matplotlib.pyplot as plt
import io
from PIL import Image
from matplotlib.patches import Rectangle


# Config
# ------------------------------------------------------------  
OBJECTSIZE = 32 #m - Size of the object in meters (max dimension)
RESOLUTION = 2 #pixels per meter (resolution of satalite image)
OBJECTSINFRAME = 5 #number of objects that fit in the frame

PIXELSIZE = OBJECTSIZE * RESOLUTION #pixels the object takes up in image
FRAMEPIXELSIZE = PIXELSIZE * OBJECTSINFRAME #pixels per meter
# ------------------------------------------------------------  

def preprocess_image(image_data):
    return 1