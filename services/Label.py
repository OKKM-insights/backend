


class Label():
    LabelID: int
    LabellerID: int
    ImageID: int
    RelatedPixels: list[int]
    Class: str

    def __init__(self, LabelID: int, 
                LabellerID: int,
                ImageID: int,
                RelatedPixels: list[int],
                Class: str):
        self.LabelID = LabelID
        self.LabellerID = LabellerID
        self.ImageID = ImageID
        self.RelatedPixels = RelatedPixels
        self.Class = Class
                        