# Image Verification API

This project is a FastAPI application for image verification using DeepFace. It provides an API endpoint to verify an uploaded image against a database of images.

## Project Structure

```
.
├── .gitignore
├── README.md
├── src
│   └── app.py
└── database
```

- `.gitignore`: Contains rules for ignoring specific files and directories in version control.
- `README.md`: Project documentation.
- `src/app.py`: Contains the FastAPI application code for image verification.
- `database`: Directory where the image database is stored.

## Requirements

- Python 3.8+
- FastAPI
- DeepFace
- OpenCV
- NumPy
- Pydantic

## Installation

1. Clone the repository:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Environment Variables

- `DATABASE_DIR`: Path to the directory containing the image database (default: `/app/database`).

## Running the Application

1. Navigate to the `src` directory:
    ```sh
    cd src
    ```

2. Start the FastAPI application:
    ```sh
    uvicorn app:app --reload
    ```

3. The API will be available at `http://127.0.0.1:8000`.

## API Endpoint

### Verify Image

- **URL**: `/verify`
- **Method**: `POST`
- **Request**: Upload an image file.
- **Response**: JSON object with verification result.

#### Example Request

```sh
curl -X POST "http://127.0.0.1:8000/verify" -F "file=@path_to_image"
```

#### Example Response

```json
{
  "match": true,
  "confidence": 95.67,
  "matched_image": "example.jpg"
}
```

## License

This project was created for educational purposes at Wrocław University of Science and Technology.