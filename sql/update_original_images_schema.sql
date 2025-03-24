-- Drop the foreign key constraint
ALTER TABLE Images DROP FOREIGN KEY orig_image_id;

-- Drop the existing table if it exists
DROP TABLE IF EXISTS OriginalImages;

-- Create the new table with ImagePath column
CREATE TABLE OriginalImages (
    ImageID VARCHAR(255) NOT NULL,
    ProjectID VARCHAR(255) NOT NULL,
    ImagePath VARCHAR(1024) NOT NULL,
    PRIMARY KEY (ImageID)
);

-- Add the missing column
ALTER TABLE OriginalImages ADD ImagePath VARCHAR(1024);

-- Recreate the foreign key constraint
ALTER TABLE Images ADD CONSTRAINT orig_image_id FOREIGN KEY (origImageID) REFERENCES OriginalImages(ImageID); 