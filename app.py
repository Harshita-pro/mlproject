import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from utils.ocr import extract_text_from_image
from utils.matcher import find_medicine, SEMANTIC_AVAILABLE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'templates'),
    static_folder=str(BASE_DIR / 'static')
)

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['ENV'] = 'production'  # Set to development if debugging


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """
    Process uploaded medicine image and return identification results.
    
    Expected request:
        POST /predict
        Content-Type: multipart/form-data
        Body: image (file)
    
    Returns:
        JSON response with medicine details or error message
    """
    
    # Validate file presence
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No image file provided'
        }), 400

    file = request.files['image']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        # Save file with unique name to prevent collisions
        original_name = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_name}"
        filepath = UPLOAD_FOLDER / unique_filename
        file.save(filepath)
        logger.info(f"File saved: {unique_filename}")

        # Extract text using OCR
        extracted_text = extract_text_from_image(str(filepath))
        
        if not extracted_text or extracted_text.strip() == '':
            logger.warning("OCR returned empty text")
            return jsonify({
                'success': False,
                'message': 'Could not extract text from image. Try a clearer photo.'
            }), 422

        logger.info(f"Extracted text: {extracted_text[:100]}...")

        # Find matching medicine
        result = find_medicine(extracted_text)
        
        if not result:
            logger.info("No medicine match found")
            message = 'Medicine not found in database.'
            if not SEMANTIC_AVAILABLE:
                message += (
                    ' Semantic search is unavailable in this environment. '
                    'Install faiss and sentence-transformers and run '
                    'scripts/rag_ingest.py for better matching.'
                )
            return jsonify({
                'success': False,
                'extracted_text': extracted_text,
                'message': message,
                'semantic_search_available': SEMANTIC_AVAILABLE,
            }), 404

        logger.info(f"Medicine found: {result['medicine_name']}")
        return jsonify({
            'success': True,
            'extracted_text': extracted_text,
            'medicine_name': result['medicine_name'],
            'composition': result['composition'],
            'uses': result['uses'],
            'side_effects': result['side_effects'],
            'manufacturer': result['manufacturer'],
            'confidence': result['confidence'],
            'match_mode': result.get('match_mode', 'direct'),
            'semantic_search_available': result.get('semantic_search_available', SEMANTIC_AVAILABLE)
        })

    except Exception as exc:
        logger.error(f"Error processing image: {str(exc)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Error processing image. Please try again.'
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'message': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f}MB'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(
        debug=False,  # Set to True only during development
        host='0.0.0.0',
        port=5000
    )
