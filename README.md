# Medicine Identifier 💊

A web application that identifies medicines from uploaded images using OCR and semantic search with machine learning.

## Features

- **Image Upload**: Upload a photo of a medicine strip/box
- **OCR Extraction**: Automatically extract medicine composition from the image
- **Semantic Search**: Match medicine using FAISS embeddings and direct text matching
- **Detailed Info**: Get medicine name, composition, uses, side effects, and manufacturer
- **Confidence Score**: Understand how confident the system is about the match

## Tech Stack

- **Backend**: Flask (Python)
- **OCR**: EasyOCR
- **Matching**: FAISS + Sentence Transformers
- **Frontend**: HTML/CSS/JavaScript
- **Data**: Pandas, NumPy

## Project Structure

```
mlproject/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore                # Git ignore patterns
├── templates/
│   └── index.html            # Frontend template
├── static/
│   ├── css/
│   │   └── style.css         # Styling
│   ├── js/
│   │   └── app.js            # Frontend logic
│   └── uploads/              # User uploaded images
├── utils/
│   ├── __init__.py
│   ├── ocr.py                # OCR extraction module
│   └── matcher.py            # Medicine matching module
├── scripts/
│   └── rag_ingest.py         # Data indexing script
└── data/
    └── Medicine_Details.csv  # Medicine dataset
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
cd mlproject
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate      # On Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Place your `Medicine_Details.csv` in the `data/` folder.

5. Run the ingestion script to create FAISS index:
```bash
python scripts/rag_ingest.py
```

## Running the Application

```bash
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Upload a clear photo of the medicine strip/box
2. Click "Identify Medicine"
3. View the extracted information and confidence score
4. If the medicine is not recognized, try again with a clearer photo

## How it Works

### OCR Pipeline
1. **Image Upload**: User uploads medicine image
2. **Text Extraction**: EasyOCR extracts visible text
3. **Text Cleaning**: Spell corrections and standardization
4. **Brand Mapping**: Known brand names are mapped to active ingredients

### Matching Pipeline
1. **Token Matching**: Direct substring and word matching in composition
2. **Embedding Search**: If no direct match, use FAISS semantic search
3. **Confidence Scoring**: Combines multiple factors for reliability

## Confidence Score Explanation

- **90-100%**: High confidence - Direct composition match found
- **70-89%**: Medium confidence - Semantic embedding match
- **<70%**: Low confidence - Medicine may not be in database or OCR quality is poor

## Improvements & Future Work

- [ ] Add more data to the medicine database
- [ ] Improve OCR preprocessing with image enhancement
- [ ] Add user feedback mechanism to improve accuracy
- [ ] Deploy with Docker
- [ ] Add API documentation
- [ ] Implement caching for common medicines
- [ ] Add database backend (PostgreSQL)
- [ ] Add authentication and user history
- [ ] Implement unit and integration tests
- [ ] Add monitoring and logging

## Troubleshooting

### "ModuleNotFoundError"
Make sure you're in the virtual environment and ran `pip install -r requirements.txt`.

### "FAISS index not found"
Run `python scripts/rag_ingest.py` to generate the index.

### "Could not extract text from image"
- Ensure the image is clear and well-lit
- Try uploading a different photo
- Ensure the medicine composition text is visible in the image

## Performance Tips

- Use clear, well-lit photos
- Ensure the medicine strip/box composition is visible
- Hold the camera straight without angle
- Crop the image to show only the composition area if possible

## License

MIT License

## Author

Created for educational and resume purposes.

## Support

For issues or suggestions, please create an issue or contact the maintainer.
