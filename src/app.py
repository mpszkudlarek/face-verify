import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from deepface import DeepFace
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
IMAGE_SIZE = (224, 224)
MODEL_NAME = "VGG-Face"
DATABASE_DIR = os.getenv("DATABASE_DIR", "/app/database")

model = DeepFace.build_model(MODEL_NAME)
app = FastAPI()


class VerificationResult(BaseModel):
    match: bool
    confidence: float = 0.0
    matched_image: str = ""


def decode_image(contents: bytes) -> Optional[np.ndarray]:
    """
    Decode image bytes to an OpenCV image array.

    Args:
        contents (bytes): Image file contents.

    Returns:
        Optional[np.ndarray]: Decoded image array or None if decoding fails.
    """
    try:
        np_array = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
        return image
    except Exception as e:
        raise ValueError(f"Image decoding failed: {str(e)}")


def get_database_images() -> List[Path]:
    """
    Get list of valid image paths from database directory.

    Returns:
        List[Path]: List of valid image file paths
    """
    database_path = Path(DATABASE_DIR)
    if not database_path.exists():
        raise ValueError(f"Database directory {DATABASE_DIR} does not exist")

    return [
        f for f in database_path.iterdir() if f.suffix.lower() in ALLOWED_EXTENSIONS
    ]


def verify_against_database(
    uploaded_image_path: str, model_name: str = MODEL_NAME
) -> VerificationResult:
    """
    Verify the uploaded image against a database of images using DeepFace.

    Args:
        uploaded_image_path (str): Path to the uploaded image.
        model_name (str): DeepFace model to use for verification.

    Returns:
        VerificationResult: Verification result with match status and confidence.
    """
    best_match = VerificationResult(match=False)
    highest_confidence = 0.0

    try:
        database_images = get_database_images()

        for db_image_path in database_images:
            try:
                result = DeepFace.verify(
                    img1_path=uploaded_image_path,
                    img2_path=str(db_image_path),
                    model_name=model_name,
                )

                # Calculate confidence as 1 - distance (since lower distance means higher similarity)
                confidence = 1.0 - result.get("distance", 1.0)

                if result.get("verified") and confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = VerificationResult(
                        match=True,
                        confidence=round(confidence * 100, 2),  # Convert to percentage
                        matched_image=db_image_path.name,
                    )

            except Exception as e:
                print(f"Error comparing with {db_image_path}: {str(e)}")
                continue

        return best_match

    except Exception as e:
        raise ValueError(f"Verification failed: {str(e)}")


@app.post("/verify", response_model=VerificationResult)
async def verify_image(file: UploadFile = File(...)) -> VerificationResult:
    """
    Endpoint to verify an uploaded image against a database.

    Args:
        file (UploadFile): Uploaded image file.

    Returns:
        VerificationResult: Result indicating if the image matches any database entry.

    Raises:
        HTTPException: If image processing or verification fails.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    temp_path = f"temp_{file.filename}"

    try:
        contents = await file.read()
        image = decode_image(contents)
        image_resized = cv2.resize(image, IMAGE_SIZE)
        cv2.imwrite(temp_path, image_resized)

        result = verify_against_database(temp_path)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
