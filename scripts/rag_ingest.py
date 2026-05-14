"""
RAG Ingestion Script - Create FAISS index from medicine dataset

This script:
1. Loads medicine dataset from CSV
2. Cleans and prepares data
3. Generates embeddings using sentence transformers
4. Creates FAISS index for semantic search
5. Saves index and data for production use

Run this script after adding Medicine_Details.csv to data/ folder:
    python scripts/rag_ingest.py
"""

import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
UTILS_DIR = BASE_DIR / 'utils'
CSV_PATH = DATA_DIR / 'Medicine_Details.csv'
INDEX_PATH = UTILS_DIR / 'medicine_index.faiss'
DATA_PKL_PATH = UTILS_DIR / 'medicine_data.pkl'

# Ensure output directory exists
UTILS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset():
    """Load medicine dataset from CSV."""
    logger.info(f"Loading dataset from {CSV_PATH}...")
    
    if not CSV_PATH.exists():
        logger.error(f"Dataset not found at {CSV_PATH}")
        logger.info(f"Please place Medicine_Details.csv in {DATA_DIR} folder")
        return None
    
    df = pd.read_csv(CSV_PATH)
    logger.info(f"✅ Loaded {len(df)} medicines")
    
    return df


def prepare_data(df):
    """Clean and prepare data for indexing."""
    logger.info("Preparing data...")
    
    # Fill missing values
    df['Medicine Name'] = df['Medicine Name'].fillna('')
    df['Composition'] = df['Composition'].fillna('')
    df['Uses'] = df['Uses'].fillna('')
    df['Side_effects'] = df['Side_effects'].fillna('N/A')
    df['Manufacturer'] = df['Manufacturer'].fillna('N/A')
    
    # Create combined text for better embedding
    # This combines all searchable fields
    df['combined'] = (
        df['Medicine Name'].astype(str) + ' ' +
        df['Composition'].astype(str) + ' ' +
        df['Uses'].astype(str)
    )
    
    # Remove rows with empty combined text
    df = df[df['combined'].str.strip() != '']
    
    logger.info(f"✅ Prepared {len(df)} valid medicines for indexing")
    
    return df


def create_embeddings(df):
    """Generate embeddings using sentence transformers."""
    logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("✅ Model loaded")
    
    logger.info("Generating embeddings (this may take a few minutes)...")
    
    embeddings = model.encode(
        df['combined'].tolist(),
        show_progress_bar=True,
        batch_size=64
    )
    
    logger.info(f"✅ Generated {len(embeddings)} embeddings")
    
    return np.array(embeddings).astype('float32')


def create_index(embeddings):
    """Create FAISS index for semantic search."""
    logger.info("Creating FAISS index...")
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Use IndexFlatIP (inner product) for cosine similarity after normalization
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    logger.info(f"✅ Created FAISS index with {index.ntotal} embeddings")
    
    return index


def save_artifacts(df, index):
    """Save index and data for production."""
    logger.info("Saving artifacts...")
    
    # Save FAISS index
    faiss.write_index(index, str(INDEX_PATH))
    logger.info(f"✅ Saved FAISS index to {INDEX_PATH}")
    
    # Save dataframe
    df.to_pickle(str(DATA_PKL_PATH))
    logger.info(f"✅ Saved medicine data to {DATA_PKL_PATH}")


def main():
    """Main ingestion pipeline."""
    logger.info("=" * 60)
    logger.info("Starting RAG Ingestion Pipeline")
    logger.info("=" * 60)
    
    # Load dataset
    df = load_dataset()
    if df is None:
        return False
    
    # Prepare data
    df = prepare_data(df)
    
    # Create embeddings
    embeddings = create_embeddings(df)
    
    # Create index
    index = create_index(embeddings)
    
    # Save artifacts
    save_artifacts(df, index)
    
    logger.info("=" * 60)
    logger.info("✅ RAG Ingestion Pipeline Completed Successfully!")
    logger.info("=" * 60)
    logger.info(f"Total medicines indexed: {len(df)}")
    logger.info(f"Embedding dimension: {embeddings.shape[1]}")
    logger.info(f"Index size: {index.ntotal}")
    logger.info("")
    logger.info("You can now run the Flask app:")
    logger.info("    python app.py")
    
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
