"""Tesseract OCR with OpenCV preprocessing. Returns words with real per-word confidence."""
from __future__ import annotations

import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageOps

from app.core.config import Settings
from app.core.errors import ExtractionError
from app.services.layout import Word


def configure(settings: Settings) -> None:
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def ocr_available(settings: Settings) -> bool:
    configure(settings)
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _estimate_skew(gray: np.ndarray) -> float:
    """Projection-profile search for the rotation (degrees, -5..5) that makes text rows sharpest."""
    h, w = gray.shape
    scale = 600 / w if w > 600 else 1.0
    small = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA) if scale < 1 else gray
    _, bw = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    center = (bw.shape[1] / 2, bw.shape[0] / 2)
    best_angle, best_score = 0.0, -1.0
    for angle in np.arange(-5.0, 5.01, 0.5):
        m = cv2.getRotationMatrix2D(center, float(angle), 1.0)
        rotated = cv2.warpAffine(bw, m, (bw.shape[1], bw.shape[0]), flags=cv2.INTER_NEAREST)
        score = float(np.var(rotated.sum(axis=1)))
        if score > best_score:
            best_angle, best_score = float(angle), score
    return best_angle


def preprocess(img: Image.Image) -> Image.Image:
    """Orientation fix (EXIF), grayscale, upscale small images, contrast boost, deskew."""
    img = ImageOps.exif_transpose(img).convert("L")
    w, h = img.size
    if w < 1600:
        factor = 1600 / w
        img = img.resize((1600, int(h * factor)), Image.LANCZOS)
    arr = np.array(img)
    arr = cv2.medianBlur(arr, 3)
    if arr.std() < 40:  # low contrast
        arr = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(arr)
    angle = _estimate_skew(arr)
    if abs(angle) >= 0.5:
        m = cv2.getRotationMatrix2D((arr.shape[1] / 2, arr.shape[0] / 2), angle, 1.0)
        arr = cv2.warpAffine(arr, m, (arr.shape[1], arr.shape[0]), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    return Image.fromarray(arr)


def _fix_orientation(img: Image.Image, lang: str) -> Image.Image:
    """90/180/270 degree rotation via Tesseract OSD, when OSD data is installed and confident."""
    try:
        osd = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        if int(osd.get("rotate", 0)) in (90, 180, 270) and float(osd.get("orientation_conf", 0)) >= 2:
            return img.rotate(-int(osd["rotate"]), expand=True, fillcolor=255)
    except Exception:
        pass
    return img


def ocr_words(img: Image.Image, page: int, settings: Settings, psm: int = 6) -> list[Word]:
    configure(settings)
    prepared = preprocess(img)
    prepared = _fix_orientation(prepared, settings.ocr_lang)
    try:
        data = pytesseract.image_to_data(
            prepared, lang=settings.ocr_lang, config=f"--psm {psm}",
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractNotFoundError:
        raise ExtractionError("ocr_unavailable", "Tesseract OCR is not installed or not on PATH.", 503)
    except pytesseract.TesseractError as e:
        if "language" in str(e).lower():
            raise ExtractionError("ocr_language_missing",
                                  f"OCR language data '{settings.ocr_lang}' is not installed.", 503)
        raise ExtractionError("ocr_failed", "OCR failed on this page.")
    words: list[Word] = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            continue
        if not text or conf < 0:
            continue
        left, top, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        words.append(Word(text, left, left + w, top, top + h, conf, page))
    return words
