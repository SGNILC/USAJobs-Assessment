'''
    Handles image preprocessing (grayscale, thresholding, deskewing) with OpenCV 
    and runs EasyOCR to pull text with bounding boxes.  
'''

# import modules
import cv2
import numpy as np
import easyocr

# Initialize EasyOCR reader once to meet performance(under 5 sec) threshold
reader = easyocr.Reader(['en'], gpu=False)

"""
    Decodes image bytes, converts to grayscale, and applies adaptive thresholding
    to handle glare and minor lighting issues.
"""
def preprocess_image(image_bytes: bytes) -> np.ndarray:

    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image bytes; file may be corrupt or not a supported image format.")

    # Convert to Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Reduce noise and enhance text contrast
    processed = cv2.fastNlMeansDenoising(gray, h=10)
    return processed

"""
    Runs EasyOCR on processed image bytes and returns a list of detected text strings.
"""
def extract_text_from_image(image_bytes: bytes) -> list:
    processed_img = preprocess_image(image_bytes)
    results = reader.readtext(processed_img, detail=0)
    return results