import os
from typing import Optional

# import tensorflow as tf
# config = tf.config.threading.set_inter_op_parallelism_threads(4)
# tf.config.threading.set_intra_op_parallelism_threads(2)
import cv2
import numpy as np
from deepface import DeepFace
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

model = DeepFace.build_model("VGG-Face")

app = FastAPI()


def decode_image(contents: bytes) -> Optional[np.ndarray]:
    """
    Decode image bytes to an OpenCV image array.

    Args:
        contents (bytes): Image file contents.

    Returns:
        Optional[np.ndarray]: Decoded image array or None if decoding fails.
    """
    np_array = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    return image


def verify_against_database(
    uploaded_image_path: str, database_dir: str, model_name: str = "VGG-Face"
) -> dict:
    """
    Verify the uploaded image against a database of images using DeepFace.

    Args:
        uploaded_image_path (str): Path to the uploaded image.
        database_dir (str): Directory containing database images.
        model_name (str): DeepFace model to use for verification.

    Returns:
        dict: Verification result indicating if a match is found.
    """
    database_images = [
        os.path.join(database_dir, f)
        for f in os.listdir(database_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    for db_image_path in database_images:
        try:
            result = DeepFace.verify(
                img1_path=uploaded_image_path,
                img2_path=db_image_path,
                model_name=model_name,
            )
            if result.get("verified"):
                return {"match": True}

        except Exception as e:
            print(f"Error comparing {db_image_path}: {e}")

    return {"match": False}


@app.post("/verify")
async def verify_image(file: UploadFile = File(...)):
    """
    Endpoint to verify an uploaded image against a database.

    Args:
        file (UploadFile): Uploaded image file.

    Returns:
        JSONResponse: Result indicating if the image matches any database entry.
    """
    temp_path = f"temp_{file.filename}"

    try:
        contents = await file.read()
        image = decode_image(contents)

        if image is None:
            raise ValueError("Uploaded file is not a valid image.")

        image_resized = cv2.resize(image, (224, 224))
        cv2.imwrite(temp_path, image_resized)

        result = verify_against_database(
            uploaded_image_path=temp_path, database_dir="data"
        )

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
