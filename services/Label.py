import uuid


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
                        