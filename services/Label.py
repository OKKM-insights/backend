


class Label():
    LabellerID: int
    ImageID: int
    RelatedPixels: list[int]
    Class: str

    def __init__(self,
                LabellerID: int,
                ImageID: int,
                RelatedPixels: list[int],
                Class: str):
        self.LabellerID = LabellerID
        self.ImageID = ImageID
        self.RelatedPixels = RelatedPixels
        self.Class = Class
                        