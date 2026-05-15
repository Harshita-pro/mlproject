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
}


def preprocess_image(image_path):
    """
    Preprocess image for better OCR accuracy.
    
    Steps:
    - Load image
    - Convert to grayscale
    - Apply denoising
    - Enhance contrast
    - Sharpen
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
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Sharpen
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) / 1.0
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return None


def clean_text(text):
    """
    Clean and standardize OCR extracted text.
    
    - Fix common OCR mistakes
    - Normalize spacing
    - Remove special characters (except dosage units)
    """
    text_lower = text.lower()
    
    # Apply OCR corrections
    for wrong, right in OCR_CORRECTIONS.items():
        text_lower = text_lower.replace(wrong, right)
    
    # Keep alphanumeric, spaces, +, (), /, %, dosage units
    text_lower = re.sub(r'[^a-z0-9\s\+\(\)/\%\-]', ' ', text_lower)
    
    # Normalize multiple spaces
    text_lower = re.sub(r'\s+', ' ', text_lower)
    
    return text_lower.strip()


def extract_text_from_image(image_path):
    """
    Extract text from medicine image using OCR.
    
    Process:
    1. Preprocess image for clarity
    2. Run EasyOCR
    3. Filter by confidence threshold
    4. Clean and standardize text
    5. Apply brand mapping
    
    Args:
        image_path (str): Path to image file
        
    Returns:
        str: Extracted and cleaned text
    """
    if reader is None:
        logger.error("EasyOCR reader not initialized")
        return ""
    
    try:
        # Preprocess image
        preprocessed = preprocess_image(image_path)
        if preprocessed is None:
            # Fallback: use original image
            results = reader.readtext(image_path)
        else:
            # Use preprocessed image - save temporarily
            temp_path = image_path.replace('.', '_temp.')
            cv2.imwrite(temp_path, preprocessed)
            results = reader.readtext(temp_path)
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
        
        # Extract text with confidence > 0.3
        text_parts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                text_parts.append(text)
        
        full_text = ' '.join(text_parts)
        logger.info(f"Raw OCR extracted: {full_text[:100]}...")
        
        # Clean extracted text
        full_text = clean_text(full_text)
        logger.info(f"Cleaned text: {full_text[:100]}...")
        
        # Apply brand mapping
        text_lower = full_text.lower()
        extra_compositions = []
        for brand, composition in BRAND_MAP.items():
            if brand in text_lower and composition:
                extra_compositions.append(composition)
        
        if extra_compositions:
            full_text = full_text + ' ' + ' '.join(extra_compositions)
            logger.info(f"After brand mapping: {full_text[:100]}...")
        
        return full_text.strip()
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
        return ""
