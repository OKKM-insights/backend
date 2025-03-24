import subprocess

def trigger_ml_detection(image_path, project_id):
    """
    Trigger ML detection on the given image.
    Returns True if detection was successful, False otherwise.
    """
    try:
        # Define paths
        model_path = "model/model.tfl"
        output_path = image_path.replace(".png", "_detection.png")
        
        # Run the locator script with the project ID
        cmd = ["python", "model/locator.py", model_path, image_path, output_path, str(project_id)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the script ran successfully
        if result.returncode == 0:
            print("ML detection completed successfully")
            print(result.stdout)
            return True
        else:
            print("ML detection failed")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error running ML detection: {str(e)}")
        return False 