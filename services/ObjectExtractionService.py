from .DataTypes import ImageObject, Labeller, Label, Image, ImageClassMeasure
import numpy as np
import pandas as pd
from .ImageClassMeasureDatabaseConnector import ImageClassMeasureDatabaseConnector, MYSQLImageClassMeasureDatabaseConnector
from scipy.special import beta
from collections import deque
from .LabellerDatabaseConnector import LabellerDatabaseConnector

class ObjectExtractionService:

    # generates a list of ImageObjects which have likelihoods over a certain amount

    def __init__(self, icm_db: ImageClassMeasureDatabaseConnector, labeller_db: LabellerDatabaseConnector, threshold: float=.7):
        self.threshold = threshold
        self.icm_db = icm_db
        self.labeller_db = labeller_db

    def get_objects(self, image: Image, Class: str, labellers: list[Labeller], labels: list[Label]) -> list[ImageObject]:
        # get objects for a given image and class
        image_data = np.asarray(image.image_data)

        labellers = pd.DataFrame([l.__dict__ for l in labellers])
        labels = pd.DataFrame([l.__dict__ for l in labels])

        # labels = labels[labels['Class'] == Class]
        labellers = labellers[labellers['skill']==Class]

        print(labels)
        print(labellers)
        icm = self.__get_icm(image.ImageID, Class)

        if not icm:
            print('creating new ICM')
            icm = ImageClassMeasure(image.ImageID, None, None, None, Class, len(image_data[0]), len(image_data[1]))
        else:
            print('ICM loaded')

        for i, labeller in labellers.iterrows(): 
            print(f'applying label group {i}')
            tmp_labels = labels[labels['LabellerID'] == labeller['LabellerID']]
            self.__update_label_likelihood(icm, tmp_labels, Labeller(labeller['LabellerID'],
                                                                     labeller['skill'],
                                                                     labeller['alpha'],
                                                                     labeller['beta']
                                                                     ))
        
        self.__update_label_confidence(icm)

        for i, labeller in labellers.iterrows():
            id = labeller['LabellerID']
            print(f'updating labeller {id}') 
            tmp_labels = labels[labels['LabellerID'] == labeller['LabellerID']]
            l = Labeller(labeller['LabellerID'],
                                                                     labeller['skill'],
                                                                     labeller['alpha'],
                                                                     labeller['beta']
                                                                     )
            self.__update_labeler_accuracy(icm, tmp_labels, l)
            self.labeller_db.push_labeller(l)
        groups = self.__find_connected_groups(icm.likelihoods)
        print(f'found {len(groups)} groups')
        output = []
        for group in groups:
            min_confidence = 1
            for pixel in group:
                if min_confidence > icm.confidence[pixel[1]][pixel[0]]:
                    min_confidence = icm.confidence[pixel[1]][pixel[0]]
            output.append(ImageObject(None, image.ImageID, Class, min_confidence, group, [Label()]))

        self.icm_db.push_imageclassmeasure(icm)

        return output

    def __get_icm(self, imageID: str, Class: str) -> ImageClassMeasure:
        query = f"""
            SELECT * FROM ImageClassMeasure Where ImageID = '{imageID}' and Label = '{Class}';
        """
        return self.icm_db.get_imageclassmeasures(query)


    def __update_label_likelihood(self, icm: ImageClassMeasure, labels:pd.DataFrame, labeller: Labeller):
        # modifies the probabilities of each pixel being in the class based on a new set of labels made by the same labeler
        # can be ported to GPU if performance requires
        print("Starting label likelihood update...")
        
        a = labeller.alpha
        b = labeller.beta
        
        # Pre-compute bounding boxes for faster lookup
        boxes = []
        for _, label in labels.iterrows():
            boxes.append({
                'x1': label['top_left_x'] + label['offset_x'],
                'x2': label['bot_right_x'] + label['offset_x'],
                'y1': label['top_left_y'] + label['offset_y'],
                'y2': label['bot_right_y'] + label['offset_y']
            })
        
        # Process rows in chunks for progress reporting
        chunk_size = 50
        total_rows = icm.im_height
        for row in range(0, total_rows, chunk_size):
            if row % 100 == 0:
                print(f"Processing rows {row} to {min(row + chunk_size, total_rows)} of {total_rows}")
            
            for r in range(row, min(row + chunk_size, total_rows)):
                for col in range(icm.im_width):
                    # Check if pixel is in any bounding box
                    class_prediction = 0
                    for box in boxes:
                        if (col >= box['x1'] and col <= box['x2'] and 
                            r >= box['y1'] and r <= box['y2']):
                            class_prediction = 1
                            break
                    
                    # Update helper values and likelihood
                    icm.helper_values[r][col][0] *= beta(1-class_prediction + a, class_prediction + b)
                    icm.helper_values[r][col][1] *= beta(class_prediction + a, 1-class_prediction + b)
                    icm.likelihoods[r][col] = icm.helper_values[r][col][1] / (icm.helper_values[r][col][1] + icm.helper_values[r][col][0])
        
        print("Label likelihood update completed.")

    def __update_label_confidence(self, icm: ImageClassMeasure):
        for row in range(icm.im_height):
            for col in range(icm.im_width):
                prediction = 1 if icm.likelihoods[row][col] > self.threshold else 0
                icm.confidence[row][col] = abs(icm.likelihoods[row][col] - 1 + prediction)

    def __update_labeler_accuracy(self, icm: ImageClassMeasure, labels:pd.DataFrame, labeller: Labeller):
        # update agent accuracy based on proportion of pixels correctly labeled
        image_size = icm.im_height * icm.im_width
        a:float = 0
        b:float = 0

        for row in range(icm.im_height):
            for col in range(icm.im_width):
                class_prediction = 1 if icm.likelihoods[row][col] > self.threshold else 0
                label_prediction = 0
                for i, label in labels.iterrows():
                    if (col >= label['top_left_x'] + label['offset_x'] and col <= label['bot_right_x'] + label['offset_x'] and row >= label['top_left_y'] + label['offset_y'] and row <= label['bot_right_y'] + label['offset_y']):
                        label_prediction = 1
                        break
                if class_prediction == label_prediction:
                    a += icm.confidence[row][col]
                else:
                    b += icm.confidence[row][col]
        
        labeller.alpha += a/image_size
        labeller.beta += b/image_size


    def __find_connected_groups(self, grid):
        """
        Identifies all groups of connected pixels above a given threshold.

        :param grid: 2D list of numerical values
        :param threshold: Minimum value for a pixel to be included in a group
        :return: List of groups, where each group is a list of (x, y) coordinates
        """
        if not grid or not grid[0]:  # Handle empty input
            return []

        rows, cols = len(grid), len(grid[0])
        visited = set()  # Keep track of visited pixels
        groups = []  # List to store all groups

        # 8 possible directions (up, down, left, right, diagonals)
        directions = [(-1, -1), (-1, 0), (-1, 1),
                    (0, -1),         (0, 1),
                    (1, -1), (1, 0), (1, 1)]

        def __bfs(start_x, start_y):
            """Performs BFS to find all connected pixels in a group."""
            queue = deque([(start_x, start_y)])
            group = []  # Store (x, y) positions of the current group
            visited.add((start_x, start_y))

            while queue:
                x, y = queue.popleft()
                group.append((x, y))

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in visited:
                        if grid[nx][ny] > self.threshold:
                            queue.append((nx, ny))
                            visited.add((nx, ny))

            return group

        # Iterate through the grid
        for i in range(rows):
            for j in range(cols):
                if grid[i][j] > self.threshold and (i, j) not in visited:
                    groups.append(__bfs(i, j))

        return groups

# o = ObjectExtractionService()
# i = Image('1','2','1')
# ls = [Labeller('t', 'boat','1.1','1.2'),
#       Labeller('2', 'boat','1.3','1.2')]
# o.get_objects(i, ls, None)