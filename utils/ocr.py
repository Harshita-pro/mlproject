import easyocr
import cv2
import numpy as np
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize EasyOCR reader globally (loaded once)
try:
    reader = easyocr.Reader(['en'], gpu=False)
    logger.info("EasyOCR reader initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize EasyOCR: {str(e)}")
    reader = None

# Brand name to composition mapping
BRAND_MAP = {
    'aziagma': 'azithromycin',
    'azee': 'azithromycin',
    'azithral': 'azithromycin',
    'crocin': 'paracetamol',
    'dolo': 'paracetamol',
    'calpol': 'paracetamol',
    'augmentin': 'amoxicillin',
    'allegra': 'fexofenadine',
    'ascoril': 'ambroxol',
    'combiflam': 'ibuprofen paracetamol',
    'montair': 'montelukast',
    'levocet': 'levocetirizine',
    'pan': 'pantoprazole',
    'omez': 'omeprazole',
    'flagyl': 'metronidazole',
    'cipro': 'ciprofloxacin',
    'amoxil': 'amoxicillin',
    'avastin': 'bevacizumab',
    'bevacizumab': 'bevacizumab',
}

# Common OCR errors and corrections
OCR_CORRECTIONS = {
    'compoiltlon': 'composition',
    'composilion': 'composition',
    'containg': 'containing',
    'tablct': 'tablet',
    'conted': 'coated',
    'exclplon': 'excipion',
    'illm': 'film',
    '5oomg': '500mg',
    '50omg': '500mg',
    '250mq': '250mg',
    'mcq': 'mcg',
    'mg.': 'mg',
    'avastln': 'avastin',
    'bevaczimab': 'bevacizumab',
}


def preprocess_image(image_path):
    """
    Preprocess image for better OCR accuracy.
    """
    try:
        img = cv2.imread(image_path)

        if img is None:
            logger.warning(f"Failed to load image: {image_path}")
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Sharpen
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])

        sharpened = cv2.filter2D(enhanced, -1, kernel)

        return sharpened

    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return None


def clean_text(text):
    """
    Clean OCR text.
    """

    text_lower = text.lower()

    # Apply OCR corrections
    for wrong, right in OCR_CORRECTIONS.items():
        text_lower = text_lower.replace(wrong, right)

    # Keep useful characters only
    text_lower = re.sub(r'[^a-z0-9\s\+\(\)/\%\-]', ' ', text_lower)

    # Remove isolated single chars
    text_lower = re.sub(r'\b[a-z]\b', ' ', text_lower)

    # Normalize dosage spacing
    text_lower = re.sub(r'(\d+)\s*mg', r'\1mg', text_lower)

    # Normalize spaces
    text_lower = re.sub(r'\s+', ' ', text_lower)

    return text_lower.strip()


def extract_text_from_image(image_path):
    """
    Extract text from medicine image using OCR.
    """

    if reader is None:
        logger.error("EasyOCR reader not initialized")
        return ""

    try:
        candidates = []

        # OCR on the original image
        original_results = reader.readtext(image_path)
        candidates.append(('original', original_results))

        # OCR on the preprocessed image
        preprocessed = preprocess_image(image_path)
        if preprocessed is not None:
            processed_results = reader.readtext(preprocessed)
            candidates.append(('preprocessed', processed_results))

        best_text = ""
        best_source = None

        for source, results in candidates:
            extracted = " ".join(
                text for (_, text, confidence) in results if confidence >= 0.15
            )
            if len(extracted.strip()) > len(best_text):
                best_text = extracted.strip()
                best_source = source

        if not best_text:
            for source, results in candidates:
                extracted = " ".join(text for (_, text, _) in results)
                if len(extracted.strip()) > len(best_text):
                    best_text = extracted.strip()
                    best_source = source

        logger.info(f"Raw OCR extracted ({best_source}): {best_text[:120]}")

        full_text = clean_text(best_text)
        logger.info(f"Cleaned text: {full_text[:120]}")

        extra_compositions = []
        for brand, composition in BRAND_MAP.items():
            if brand in full_text:
                extra_compositions.append(composition)

        if extra_compositions:
            full_text += " " + " ".join(extra_compositions)

        logger.info(f"Final OCR text: {full_text[:120]}")
        return full_text.strip()

    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
        return ""