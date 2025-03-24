-- Drop the existing table if it exists
DROP TABLE IF EXISTS ImageClassMeasure;

-- Create the new table with JSON columns
CREATE TABLE ImageClassMeasure (
    ImageID INT NOT NULL,
    Label VARCHAR(255) NOT NULL,
    likelihoods LONGTEXT NOT NULL,
    confidence LONGTEXT NOT NULL,
    helper_values LONGTEXT NOT NULL,
    im_width INT NOT NULL,
    im_height INT NOT NULL,
    PRIMARY KEY (ImageID, Label),
    FOREIGN KEY (ImageID) REFERENCES OriginalImages(imageId)
); 