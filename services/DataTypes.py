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
                creation_time: str= None):
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


class Labeller():
    UserID: str
    last_label_time: str
    skills: dict[str, tuple[float, float]]

    def __init__(self,
                UserID: str= None,
                last_label_time: str=None,
                skills: dict[str, tuple[float, float]]=None):

        if not skills:
            self.skills = dict()
        else:
            self.skills = skills

        self.UserID = UserID
        self.last_label_time = last_label_time        


class ImageObject():
    ImageObjectID: str
    ImageID: str
    Class: str
    confidence: float
    related_pixels: list[int]
    related_labels: list[Label]
    
    def __init__(self,
                 ImageObjectID:str = None,
                 ImageID:str = None,
                 Class: str = None,
                 confidence: float = None,
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
        self.confidence = confidence


class Image():
    ImageID: str
    ProjectID: str
    width: int
    height: int
    image_data: pilImage

    