import uuid
from PIL import Image as pilImage

class Label():
    LabelID: str
    LabellerID: str
    ImageID: str
    Class: str
    top_left_x: int
    top_left_y: int
    bot_right_x: int
    bot_right_y: int
    offset_x: int
    offset_y: int
    creation_time: str
    origImageID: str

    def __init__(self,
                LabelID: str=None,
                LabellerID: str=None,
                ImageID: str= None,
                Class: str= None,
                top_left_x: int= None,
                top_left_y: int= None,
                bot_right_x: int= None,
                bot_right_y: int= None,
                offset_x: int= None,
                offset_y: int= None,
                creation_time: str= None,
                origImageID: str = None):

        '''
        If making a new Label object (not loading from database), set ID to None
        '''

        if not LabelID:
            self.LabelID = str(uuid.uuid4())
        else:
            self.LabelID = LabelID
        self.LabellerID = LabellerID
        self.ImageID = ImageID
        self.Class = Class
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.bot_right_x = bot_right_x
        self.bot_right_y = bot_right_y
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.creation_time = creation_time
        self.origImageID = origImageID




class Labeller():
    LabellerID: str
    skill: str
    alpha: float
    beta: float

    def __init__(self,
                LabellerID: str= None,
                skill: str=None,
                alpha: float=1.2,
                beta: float=1):

        self.LabellerID = LabellerID
        self.skill = skill
        self.alpha = alpha
        self.beta = beta
      


class ImageObject():
    ImageObjectID: str
    ImageID: str
    Class: str
    Confidence: float
    related_pixels: list[list[int, int]]
    related_labels: list[Label]
    
    def __init__(self,
                 ImageObjectID:str = None,
                 ImageID:str = None,
                 Class: str = None,
                 Confidence: float = None,

                 related_pixels: list[int] = None,
                 related_labels: list[Label] = None,):
        if not ImageObjectID:
            self.ImageObjectID = str(uuid.uuid4())
        else:
            self.ImageObjectID = ImageObjectID

        if not related_pixels:
            self.related_pixels = []
        else:
            self.related_pixels = related_pixels

        if not related_labels:
            self.related_labels = []
        else:
            self.related_labels = related_labels

        self.ImageID = ImageID
        self.Class = Class
        self.Confidence = Confidence



class Image():
    ImageID: str
    ProjectID: str
    # width: int
    # height: int
    image_data: pilImage

    def __init__(self, ImageID: str, ProjectID: str, image_data: pilImage):
        self.ImageID = ImageID
        self.ProjectID = ProjectID
        # self.width = width
        # self.height = height
        self.image_data = image_data


class Project():
    ProjectID: str
    classes: list[str]
    images: list[Image]

    def __init__(self, ProjectID: str, classes: list[str], images: list[Image]):
        self.ProjectID = ProjectID
        self.classes = classes
        self.images = images



class ImageClassMeasure:
    # contains the values necessary to calculate the probability for each pixel to be a given label
    imageID: str
    likelihoods: list[list[float]]
    confidence: list[list[float]]
    helper_values: list[list[list[float]]]
    label: str
    im_height: int
    im_width: int
    
    def __init__(self, imageID, likelihoods, confidence, helper_values, label, im_width, im_height):
        if not likelihoods:
            self.likelihoods = [[0.5] * im_width for _ in range(im_height)]
        else:
            self.likelihoods = likelihoods
        if not confidence:
            self.confidence = [[0.0] * im_width for _ in range(im_height)]
        else:
            self.confidence = confidence
        if not helper_values:
            self.helper_values = [[[0.5,0.5] for _ in range(im_width)] for _ in range(im_height)] # running total for P(w_i | L = 0) & P(w_i | L = 1)
        else:
            self.helper_values = helper_values
        self.imageID = imageID
        self.label = label
        self.im_width = im_width
        self.im_height = im_height