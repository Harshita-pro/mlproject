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
    Tokenize text into meaningful words for matching.
    
    - Convert to lowercase
    - Extract words of length > 4 (ignore common words)
    - Return as set for fast intersection
    """
    return set(re.findall(r'\b[a-z0-9]{4,}\b', text.lower()))


def calculate_direct_match_score(extracted_text, composition, medicine_name):
    """
    Calculate confidence score based on direct text matching.
    
    Factors:
    - Number of words in extracted_text that appear in composition
    - Number of words in composition that appear in extracted_text
    - Bonus if medicine brand name is recognized
    
    Returns:
        tuple: (match_score, is_direct_match)
    """
    extracted_tokens = tokenize_text(extracted_text)
    composition_tokens = tokenize_text(str(composition))
    medicine_tokens = tokenize_text(str(medicine_name))
    
    # Calculate intersection score
    intersection = extracted_tokens & composition_tokens
    match_count = len(intersection)
    
    # Bonus points if medicine name is matched
    if len(extracted_tokens & medicine_tokens) > 0:
        match_count += 1
    
    # Direct match if we have at least 2 meaningful token matches
    is_direct = match_count >= 2
    
    # Score: more matches = higher confidence
    score = min(90, 60 + match_count * 10)
    
    return score, is_direct


def calculate_embedding_confidence(distances, index_size=100):
    """
    Convert FAISS distance to confidence score.
    
    For normalized embeddings with cosine similarity:
    - Lower distance = higher similarity = higher confidence
    - Scale to 0-100 range
    - Account for margin between top match and second match
    
    Args:
        distances: Distance from top-1 and top-2 results
        
    Returns:
        int: Confidence score 0-100
    """
    if distances is None or len(distances) == 0:
        return 0
    
    # Cosine score (after L2 normalization, smaller distance = higher score)
    top1_score = float(distances[0])
    
    # Calculate margin with second best match if available
    margin = 0
    if len(distances) > 1:
        top2_score = float(distances[1])
        margin = top2_score - top1_score
        margin = max(0, min(0.3, margin))  # Normalize margin
    
    # Combine: 70% from top1 score, 30% from margin
    confidence = int(100 * (0.7 * top1_score + 0.3 * (margin / 0.3 if margin > 0 else 0)))
    confidence = max(50, min(95, confidence))  # Clamp to reasonable range
    
    return confidence


def find_medicine(extracted_text, top_k=5):
    """
    Find matching medicine from extracted OCR text.
    
    Two-stage process:
    1. Direct text matching (fast, high precision)
    2. FAISS semantic search (slower, better recall)
    
    Args:
        extracted_text (str): Text extracted from medicine image
        top_k (int): Number of embeddings to search in FAISS
        
    Returns:
        dict: Medicine details with confidence, or None if not found
    """
    
    if model is None or index is None or df is None:
        logger.error("Models not initialized")
        return None
    
    if not extracted_text or len(extracted_text.strip()) < 3:
        logger.warning("Extracted text too short or empty")
        return None
    
    extracted_lower = extracted_text.lower()
    
    # Stage 1: Direct composition matching
    logger.info("Stage 1: Attempting direct text matching...")
    best_direct_match = None
    best_direct_score = 0
    
    for idx, (_, row) in enumerate(df.iterrows()):
        composition = str(row.get('Composition', ''))
        medicine_name = str(row.get('Medicine Name', ''))
        
        score, is_match = calculate_direct_match_score(
            extracted_text,
            composition,
            medicine_name
        )
        
        if score > best_direct_score:
            best_direct_score = score
            best_direct_match = (idx, row, score)
        
        # Early exit if we find a perfect match
        if is_match and score >= 80:
            logger.info(f"High confidence direct match found: {medicine_name} ({score}%)")
            return {
                'medicine_name': row['Medicine Name'],
                'composition': row['Composition'],
                'uses': row.get('Uses', 'N/A'),
                'side_effects': row.get('Side_effects', 'N/A'),
                'manufacturer': row.get('Manufacturer', 'N/A'),
                'confidence': int(score)
            }
    
    # Return direct match if confidence >= 70
    if best_direct_match is not None and best_direct_score >= 70:
        idx, row, score = best_direct_match
        logger.info(f"Direct match above threshold: {row['Medicine Name']} ({score}%)")
        return {
            'medicine_name': row['Medicine Name'],
            'composition': row['Composition'],
            'uses': row.get('Uses', 'N/A'),
            'side_effects': row.get('Side_effects', 'N/A'),
            'manufacturer': row.get('Manufacturer', 'N/A'),
            'confidence': int(score)
        }
    
    # Stage 2: FAISS semantic search
    logger.info("Stage 2: Running FAISS semantic search...")
    try:
        query_embedding = model.encode([extracted_text])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        distances, indices = index.search(query_embedding, k=min(top_k, len(df)))
        
        if len(indices[0]) == 0 or indices[0][0] == -1:
            logger.warning("FAISS search returned no results")
            return None
        
        best_idx = indices[0][0]
        best_distances = distances[0]
        
        # Calculate confidence from embedding distance
        confidence = calculate_embedding_confidence(best_distances)
        
        if confidence < 60:
            logger.info(f"FAISS match below confidence threshold: {confidence}%")
            return None
        
        row = df.iloc[best_idx]
        logger.info(f"FAISS match found: {row['Medicine Name']} ({confidence}%)")
        
        return {
            'medicine_name': row['Medicine Name'],
            'composition': row['Composition'],
            'uses': row.get('Uses', 'N/A'),
            'side_effects': row.get('Side_effects', 'N/A'),
            'manufacturer': row.get('Manufacturer', 'N/A'),
            'confidence': int(confidence)
        }
        
    except Exception as e:
        logger.error(f"FAISS search failed: {str(e)}", exc_info=True)
        return None
