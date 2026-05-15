import numpy as np
import pandas as pd
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path

try:
    import faiss
except ImportError:
    faiss = None
    logging.getLogger(__name__).warning(
        "FAISS is not installed. Semantic search will be disabled."
    )

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logging.getLogger(__name__).warning(
        "SentenceTransformers is not installed. Semantic search will be disabled."
    )

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
CSV_PATH = DATA_DIR / 'Medicine_Details.csv'
PICKLE_PATH = Path(__file__).resolve().parent / 'medicine_data.pkl'
INDEX_PATH = Path(__file__).resolve().parent / 'medicine_index.faiss'


def load_database():
    """Load medicine database from disk, with a CSV fallback."""
    if PICKLE_PATH.exists():
        try:
            logger.info(f"Loading medicine database from {PICKLE_PATH}...")
            return pd.read_pickle(str(PICKLE_PATH))
        except Exception as e:
            logger.warning(f"Failed to load pickled database: {e}")

    if CSV_PATH.exists():
        try:
            logger.info(f"Loading medicine database from fallback CSV {CSV_PATH}...")
            return pd.read_csv(str(CSV_PATH))
        except Exception as e:
            logger.warning(f"Failed to load CSV fallback database: {e}")

    return None


def load_faiss_index():
    """Load FAISS index if it exists."""
    if faiss is None:
        return None

    if INDEX_PATH.exists():
        try:
            logger.info(f"Loading FAISS index from {INDEX_PATH}...")
            return faiss.read_index(str(INDEX_PATH))
        except Exception as e:
            logger.warning(f"Failed to load FAISS index: {e}")

    return None


def load_model():
    """Load sentence transformer model if available."""
    if SentenceTransformer is None:
        logger.warning(
            "SentenceTransformer library is unavailable. Semantic search will be skipped."
        )
        return None

    try:
        logger.info("Loading sentence transformer model...")
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        logger.warning(f"Failed to load sentence transformer model: {e}")
        return None


model = load_model()
index = load_faiss_index()
df = load_database()

SEMANTIC_AVAILABLE = (
    faiss is not None and
    SentenceTransformer is not None and
    model is not None and
    index is not None
)

if df is None:
    logger.error(
        "No medicine database loaded. Please run scripts/rag_ingest.py or place Medicine_Details.csv in data/."
    )
else:
    df['Medicine Name'] = df.get('Medicine Name', '').fillna('')
    df['Composition'] = df.get('Composition', '').fillna('')
    df['Uses'] = df.get('Uses', '').fillna('')
    df['Side_effects'] = df.get('Side_effects', 'N/A').fillna('N/A')
    df['Manufacturer'] = df.get('Manufacturer', 'N/A').fillna('N/A')
    logger.info(f"✅ Database loaded with {len(df)} medicines.")
    if not SEMANTIC_AVAILABLE:
        logger.warning("Semantic search is unavailable. Direct matching will still work.")


def tokenize_text(text):
    """
    Tokenize text into meaningful words.
    """

    return set(
        re.findall(r'\b[a-z0-9]{3,}\b', text.lower())
    )


def normalize_text(text):
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower()).strip()


def calculate_fuzzy_similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


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

    target_tokens = composition_tokens | medicine_tokens
    matched_tokens = extracted_tokens & target_tokens

    name_match = len(extracted_tokens & medicine_tokens) > 0
    composition_match = len(extracted_tokens & composition_tokens) > 0
    match_count = len(matched_tokens)

    # Direct match threshold
    is_direct = match_count >= 1

    # Confidence score calculation
    score = 45 + match_count * 18
    if name_match:
        score += 10
    if composition_match and not name_match:
        score += 5

    score = min(100, score)

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

    if df is None:
        logger.error("Medicine database not loaded")
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
                'confidence': int(score),
                'match_mode': 'direct',
                'semantic_search_available': SEMANTIC_AVAILABLE
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
            'confidence': int(score),
            'match_mode': 'direct',
            'semantic_search_available': SEMANTIC_AVAILABLE
        }

    # Fallback fuzzy matching for challenging packaging text
    logger.info("Stage 1b: Fuzzy text similarity matching")
    best_fuzzy_match = None
    best_fuzzy_ratio = 0.0
    extracted_norm = normalize_text(extracted_text)

    for idx, (_, row) in enumerate(df.iterrows()):
        combined_text = normalize_text(
            f"{row.get('Medicine Name', '')} {row.get('Composition', '')} {row.get('Uses', '')}"
        )
        ratio = calculate_fuzzy_similarity(extracted_norm, combined_text)
        if ratio > best_fuzzy_ratio:
            best_fuzzy_ratio = ratio
            best_fuzzy_match = (idx, row, ratio)

    if best_fuzzy_match is not None and best_fuzzy_ratio >= 0.42:
        idx, row, ratio = best_fuzzy_match
        score = min(95, int(55 + best_fuzzy_ratio * 45))
        logger.info(
            f"Fuzzy match found: {row['Medicine Name']} (ratio={best_fuzzy_ratio:.2f}, score={score}%)"
        )
        return {
            'medicine_name': row['Medicine Name'],
            'composition': row['Composition'],
            'uses': row.get('Uses', 'N/A'),
            'side_effects': row.get('Side_effects', 'N/A'),
            'manufacturer': row.get('Manufacturer', 'N/A'),
            'confidence': int(score),
            'match_mode': 'fuzzy',
            'semantic_search_available': SEMANTIC_AVAILABLE
        }

    if faiss is None or model is None or index is None:
        logger.info("Skipping FAISS stage because semantic search is unavailable.")
        return None

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
            'confidence': int(confidence),
            'match_mode': 'semantic',
            'semantic_search_available': SEMANTIC_AVAILABLE
        }

    except Exception as e:

        logger.error(
            f"FAISS search failed: {str(e)}",
            exc_info=True
        )

        return None