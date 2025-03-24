import subprocess
import os
from pathlib import Path
from sqlalchemy import create_engine, text
import urllib.parse
from dotenv import load_dotenv
import io
from PIL import Image

# Load environment variables
load_dotenv()

def trigger_ml_detection(image_id: int) -> bool:
    """
    Trigger ML model detection on a new image.
    
    Args:
        image_id: The ID of the uploaded image
    
    Returns:
        bool: True if detection was successful, False otherwise
    """
    try:
        # Check if model files exist
        model_dir = Path("model")
        model_files = [
            model_dir / "model.tfl.meta",
            model_dir / "model.tfl.index",
            model_dir / "model.tfl.data-00000-of-00001"
        ]
        
        for file in model_files:
            if not file.exists():
                print(f"Error: Model file not found at {file}")
                return False
        
        # Get database connection parameters
        db_config = {
            'host': os.getenv('DB_HOSTNAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': os.getenv('DB_PORT')
        }
        
        # Create SQLAlchemy engine
        password = urllib.parse.quote_plus(db_config['password'])
        connection_str = f"mysql+pymysql://{db_config['user']}:{password}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(connection_str)
        
        # Check if image exists in database
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT ImageID FROM OriginalImages WHERE ImageID = :image_id"),
                {"image_id": image_id}
            )
            row = result.fetchone()
            if not row:
                print(f"Error: Image {image_id} not found in database")
                return False
        
        # We need to get the actual image from the first tile in the Images table
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT image FROM Images WHERE orig_image_id = :image_id LIMIT 1"),
                {"image_id": image_id}
            )
            row = result.fetchone()
            if not row:
                print(f"Error: No tiles found for image {image_id}")
                return False
            image_data = row[0]
        
        # Create a temporary directory for the image if it doesn't exist
        temp_dir = Path("temp_images")
        temp_dir.mkdir(exist_ok=True)
        
        # Save the image temporarily
        image_path = temp_dir / f"image_{image_id}.png"
        output_path = temp_dir / f"image_{image_id}_detection.png"
        
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        # Run the ML model detection
        cmd = [
            "python", "-m", "model.locator",  # Use module notation to avoid import issues
            str(model_dir / "model.tfl"),
            str(image_path),
            str(output_path),
            "--project_id", str(image_id)  # Pass image_id as project_id for simplicity
        ]
        
        print(f"\nRunning ML detection command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"ML detection successful for image {image_id}")
            print("\nOutput:")
            print(result.stdout)
            return True
        else:
            print(f"ML detection failed for image {image_id}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error triggering ML detection: {str(e)}")
        print("Traceback:")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temporary files
        if 'image_path' in locals() and image_path.exists():
            try:
                image_path.unlink()
            except:
                pass
        if 'output_path' in locals() and output_path.exists():
            try:
                output_path.unlink()
            except:
                pass 