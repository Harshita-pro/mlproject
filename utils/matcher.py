import numpy as np
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging
import re

logger = logging.getLogger(__name__)

# Load model and index on module import
try:
    logger.info("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    logger.info("Loading FAISS index...")
    index = faiss.read_index('utils/medicine_index.faiss')

    logger.info("Loading medicine database...")
    df = pd.read_pickle('utils/medicine_data.pkl')

    logger.info(f"✅ Models loaded successfully. Database has {len(df)} medicines.")

except Exception as e:
    logger.error(f"Failed to load models: {str(e)}")

    model = None
    index = None
    df = None


def tokenize_text(text):
    """
    Tokenize text into meaningful words.
    """

    return set(
        re.findall(r'\b[a-z0-9]{3,}\b', text.lower())
    )


def calculate_direct_match_score(
    extracted_text,
    composition,
    medicine_name
):
    """
    Calculate direct matching confidence.
    """

    extracted_tokens = tokenize_text(extracted_text)

    composition_tokens = tokenize_text(str(composition))

    medicine_tokens = tokenize_text(str(medicine_name))

    # Common words
    composition_match = extracted_tokens & composition_tokens

    medicine_match = extracted_tokens & medicine_tokens

    match_count = len(composition_match)

    # Bonus if medicine name matched
    if len(medicine_match) > 0:
        match_count += 2

    # Direct match threshold
    is_direct = match_count >= 1

    # Confidence score
    score = min(95, 50 + match_count * 15)

    return score, is_direct


def calculate_embedding_confidence(distances):
    """
    Convert FAISS similarity to confidence.
    """

    if distances is None or len(distances) == 0:
        return 0

    top1_score = float(distances[0])

    margin = 0

    if len(distances) > 1:

        top2_score = float(distances[1])

        margin = top2_score - top1_score

        margin = max(0, min(0.3, margin))

    confidence = int(
        100 * (
            0.7 * top1_score +
            0.3 * (margin / 0.3 if margin > 0 else 0)
        )
    )

    confidence = max(45, min(95, confidence))

    return confidence


def find_medicine(extracted_text, top_k=5):
    """
    Find medicine from OCR extracted text.
    """

    if model is None or index is None or df is None:

        logger.error("Models not initialized")

        return None

    if not extracted_text or len(extracted_text.strip()) < 2:

        logger.warning("Extracted text too short")

        return None

    extracted_lower = extracted_text.lower()

    logger.info(f"Searching medicine for text: {extracted_lower}")

    # -------------------------
    # STAGE 1: DIRECT MATCHING
    # -------------------------

    logger.info("Stage 1: Direct text matching")

    best_direct_match = None

    best_direct_score = 0

    for idx, (_, row) in enumerate(df.iterrows()):

        composition = str(
            row.get('Composition', '')
        )

        medicine_name = str(
            row.get('Medicine Name', '')
        )

        score, is_match = calculate_direct_match_score(
            extracted_text,
            composition,
            medicine_name
        )

        if score > best_direct_score:

            best_direct_score = score

            best_direct_match = (idx, row, score)

        # Perfect direct match
        if is_match and score >= 80:

            logger.info(
                f"High confidence direct match found: "
                f"{medicine_name} ({score}%)"
            )

            return {
                'medicine_name': row['Medicine Name'],
                'composition': row['Composition'],
                'uses': row.get('Uses', 'N/A'),
                'side_effects': row.get('Side_effects', 'N/A'),
                'manufacturer': row.get('Manufacturer', 'N/A'),
                'confidence': int(score)
            }

    # Return if decent score
    if best_direct_match is not None and best_direct_score >= 55:

        idx, row, score = best_direct_match

        logger.info(
            f"Direct match found: "
            f"{row['Medicine Name']} ({score}%)"
        )

        return {
            'medicine_name': row['Medicine Name'],
            'composition': row['Composition'],
            'uses': row.get('Uses', 'N/A'),
            'side_effects': row.get('Side_effects', 'N/A'),
            'manufacturer': row.get('Manufacturer', 'N/A'),
            'confidence': int(score)
        }

    # -------------------------
    # STAGE 2: FAISS SEARCH
    # -------------------------

    logger.info("Stage 2: FAISS semantic search")

    try:

        query_embedding = model.encode([extracted_text])

        query_embedding = np.array(
            query_embedding
        ).astype('float32')

        faiss.normalize_L2(query_embedding)

        distances, indices = index.search(
            query_embedding,
            k=min(top_k, len(df))
        )

        if len(indices[0]) == 0 or indices[0][0] == -1:

            logger.warning("No FAISS result found")

            return None

        best_idx = indices[0][0]

        best_distances = distances[0]

        confidence = calculate_embedding_confidence(
            best_distances
        )

        if confidence < 45:

            logger.info(
                f"Low FAISS confidence: {confidence}%"
            )

            return None

        row = df.iloc[best_idx]

        logger.info(
            f"FAISS match found: "
            f"{row['Medicine Name']} ({confidence}%)"
        )

        return {
            'medicine_name': row['Medicine Name'],
            'composition': row['Composition'],
            'uses': row.get('Uses', 'N/A'),
            'side_effects': row.get('Side_effects', 'N/A'),
            'manufacturer': row.get('Manufacturer', 'N/A'),
            'confidence': int(confidence)
        }

    except Exception as e:

        logger.error(
            f"FAISS search failed: {str(e)}",
            exc_info=True
        )

        return None