
import sys
from pathlib import Path
import numpy as np

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
from services.ProjectDatabaseConnector import ProjectDatabaseConnector, MYSQLProjectDatabaseConnector
from services.LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from services.LabellerDatabaseConnector import LabellerDatabaseConnector, MYSQLLabellerDatabaseConnector
from services.ImageObjectDatabaseConnector import ImageObjectDatabaseConnector, MYSQLImageObjectDatabaseConnector
from services.ObjectExtractionService import ObjectExtractionService
from services.ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector
from services.DataTypes import Labeller


class ObjectExtractionManager():


    def __init__(self,
                 project_db: ProjectDatabaseConnector,
                 label_db: LabelDatabaseConnector,
                 labeller_db: LabellerDatabaseConnector,
                 imageobject_db: ImageObjectDatabaseConnector_bb,
                 object_service: ObjectExtractionService):
        self.project_db = project_db
        self.label_db = label_db
        self.labeller_db = labeller_db
        self.imageobject_db = imageobject_db
        self.object_service = object_service
    
     # Kyle -  Putting this for now as calling get_objects exceeded 20 mins of runtime on my pc - since its pixel wise. Faster approach for testing purposes. Can comment out during actual implementation.
    def _simple_consensus_bounding_box(labels, image_shape, consensus_threshold=0.5):
        """
        Given a list of labels and the image shape (height, width),
        create a consensus mask without iterating over every pixel.
        Then, compute the union bounding box for pixels whose normalized
        consensus value exceeds consensus_threshold.
        
        Each label is assumed to have attributes:
        top_left_x, top_left_y, bot_right_x, bot_right_y.
        
        Returns:
        (x_min, y_min, x_max, y_max) or None if no pixels meet the threshold.
        """
        # image_shape should be a tuple like (height, width)
        mask = np.zeros(image_shape, dtype=np.float32)
        
        for label in labels:
            # Assuming each label object has top_left_x, top_left_y, bot_right_x, bot_right_y attributes
            mask[label.top_left_y:label.bot_right_y, label.top_left_x:label.bot_right_x] += 1

        normalized_mask = mask / len(labels)
        binary_mask = normalized_mask >= consensus_threshold
        
        if np.any(binary_mask):
            ys, xs = np.where(binary_mask)
            x_min, y_min, x_max, y_max = xs.min(), ys.min(), xs.max(), ys.max()
            return (x_min, y_min, x_max, y_max)
        else:
            return None
    

    def get_consensus_bbox(image, labels, threshold=0.5):
        # Get image shape from the PIL image object:
        image_shape = (image.image_data.height, image.image_data.width)
        
        bbox = _simple_consensus_bounding_box(labels, image_shape, consensus_threshold=threshold)
        if bbox is not None:
            print("Consensus bounding box:", bbox)
        else:
            print("No consensus bounding box found.")
        return bbox


    def get_objects(self, project_id, Class, demo=False):
        t = time.time()

        query_projects = f"SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"

        project = self.project_db.get_projects(query_projects)[0]
        objects = []
        for image in project.images:
            query_labels = f"SELECT * FROM my_image_db.Labels WHERE (OrigImageID = {image.ImageID}) and (Class = '{Class}');"
            labels = self.label_db.get_labels(query_labels)
            print(f"found {len(labels)} labels")
            labeller_ids = set()
            for label in labels:
                labeller_ids.add(label.LabellerID)

            query_labellers = f"SELECT * FROM my_image_db.Labeller_skills WHERE Labeller_id IN :ids"

            labellers = self.labeller_db.get_labellers_with_data(query_labellers, {'ids': tuple(labeller_ids)})

            found_labeller_ids = [labeller.LabellerID for labeller in labellers]
            for labeller_id in labeller_ids:
                if labeller_id not in found_labeller_ids:
                    labellers.append(Labeller(labeller_id, Class))

            print(labellers)
            print(labels[0].__dict__)

            objects.append(self.object_service.get_objects(image, Class, labellers, labels, demo=demo))

        for object_list in objects:
            for ob in object_list:
                self.imageobject_db.push_imageobject(ob)
        print(f"completed in {time.time()-t} seconds")


t = ObjectExtractionManager(MYSQLProjectDatabaseConnector(),MYSQLLabelDatabaseConnector(), MYSQLLabellerDatabaseConnector(), MYSQLImageObjectDatabaseConnector_bb(), ObjectExtractionService(MYSQLImageClassMeasureDatabaseConnector(), MYSQLLabellerDatabaseConnector()))
t.get_objects('66', 'plane', demo=False)

