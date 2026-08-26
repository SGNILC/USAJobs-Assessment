"""Local image preparation and OCR for TTB label verification."""

from __future__ import annotations

import time
from typing import Any

import cv2
import easyocr
import numpy as np

MAX_IMAGE_DIMENSION = 1280
reader = easyocr.Reader(["en"], gpu=False)

def _crop_text_regions(image: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    height, width = image.shape[:2]
    margin = max(4, int(min(height, width) * 0.05))
    inner = image[margin:height - margin, margin:width - margin]

    foreground = inner < 200
    rows = np.where(np.sum(foreground, axis=1) >= 2)[0]
    columns = np.where(np.sum(foreground, axis=0) >= 2)[0]

    if not len(rows) or not len(columns):
        return image, (0, 0, width, height)

    padding = max(8, int(min(height, width) * 0.02))
    left = max(0, margin + columns[0] - padding)
    top = max(0, margin + rows[0] - padding)
    right = min(width, margin + columns[-1] + padding)
    bottom = min(height, margin + rows[-1] + padding)

    return image[top:bottom, left:right], (
    int(left),
    int(top),
    int(right),
    int(bottom),
)

def check_quality_gate(quality_dict: dict[str, Any]) -> bool:
    return (
        quality_dict.get("ocr_confidence", 0.0) < 0.75
        or quality_dict.get("low_confidence", False)
        or quality_dict.get("contrast_stddev", 0.0) < 18.0
    )

def _resize_to_limit(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    largest = max(height, width)
    if largest <= MAX_IMAGE_DIMENSION:
        return image
    scale = MAX_IMAGE_DIMENSION / largest
    return cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)


def _correct_orientation(image: np.ndarray) -> np.ndarray:
    """Correct the common sideways-phone-photo case before OCR."""
    if image.shape[1] > image.shape[0]:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return image


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct small, clearly detectable label skew without expensive OCR retries."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=90,
        minLineLength=max(120, image.shape[1] // 3),
        maxLineGap=24,
    )
    if lines is None:
        return image

    angles: list[float] = []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if abs(angle) <= 12:
            angles.append(angle)
    if not angles:
        return image

    angle = float(np.median(angles))
    if abs(angle) < 0.7:
        return image
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def extract_text_with_metadata(image_bytes: bytes) -> tuple[list[str], dict[str, Any]]:
    """Run one bounded-size OCR pass and return text plus image-quality metadata."""
    processed, metadata = preprocess_image_with_metadata(image_bytes)
    started = time.perf_counter()
    ocr_results = reader.readtext(
         processed,
         detail=1,
         canvas_size=MAX_IMAGE_DIMENSION,
         mag_ratio=1.0,
         contrast_ths=0.1,
         adjust_contrast=0.5,
         workers=0,
    )

    text = [item[1] for item in ocr_results]
    confidence_scores = [float(item[2]) for item in ocr_results]
    metadata["ocr_confidence"] = (
        sum(confidence_scores) / len(confidence_scores)
        if confidence_scores
        else 0.0
    )
    metadata["low_confidence"] = metadata["ocr_confidence"] < 0.70  
    metadata["ocr_seconds"] = round(time.perf_counter() - started, 4)
    metadata["manual_review_recommended"] = check_quality_gate(metadata)

    return text, metadata

def preprocess_image_with_metadata(image_bytes: bytes) -> tuple[np.ndarray, dict[str, Any]]:
    """Decode, orient, resize, and enhance an image for fast local OCR."""
    started = time.perf_counter()
    color = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if color is None:
        raise ValueError("Could not decode image bytes; file may be corrupt or not a supported image format.")

    color = _correct_orientation(color)
    color = _resize_to_limit(color)
    color = _deskew(color)
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)

    # CLAHE is much cheaper than full-image non-local-means denoising and
    # improves readability on low-contrast labels.
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    cropped, crop_bounds = _crop_text_regions(enhanced)
    cropped = _resize_to_limit(cropped)
    glare_ratio = float(np.mean(gray >= 250))
    contrast = float(np.std(gray))
    metadata = {
        "glare_ratio": round(glare_ratio, 4),
        "contrast_stddev": round(contrast, 2),
        "needs_review": glare_ratio >= 0.05 and contrast < 28.0,
        "preprocess_seconds": round(time.perf_counter() - started, 4),
        "crop_bounds": crop_bounds,
        "binarized": False,
    }
    return cropped, metadata


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Compatibility wrapper returning only the prepared image."""
    image, _ = preprocess_image_with_metadata(image_bytes)
    return image



def extract_text_from_image(image_bytes: bytes) -> list[str]:
    """Compatibility wrapper returning only OCR text."""
    text, _ = extract_text_with_metadata(image_bytes)
    return text
