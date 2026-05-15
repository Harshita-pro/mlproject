# Medicine Identifier - Quick Start Guide

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- 4GB+ RAM (for models)
- Medicine_Details.csv dataset

## 🚀 Quick Start (Windows)

```bash
# 1. Run setup script
setup.bat

# 2. Activate virtual environment (if not auto-activated)
venv\Scripts\activate

# 3. Copy your dataset
# Place Medicine_Details.csv in data/ folder

# 4. Create FAISS index
python scripts/rag_ingest.py

# 5. Start Flask app
python app.py
```

## 🚀 Quick Start (Mac/Linux)

```bash
# 1. Run setup script
bash setup.sh

# 2. Activate virtual environment (if not auto-activated)
source venv/bin/activate

# 3. Copy your dataset
# Place Medicine_Details.csv in data/ folder

# 4. Create FAISS index
python scripts/rag_ingest.py

# 5. Start Flask app
python app.py
```

## 🌐 Access the App

Open your browser and navigate to:
```
http://localhost:5000
```

## 📁 Project Structure

```
mlproject/
├── app.py                    # Main Flask app
├── requirements.txt          # Dependencies
├── README.md                 # Full documentation
├── setup.bat / setup.sh      # Setup script
├── templates/
│   └── index.html            # Frontend
├── static/
│   ├── css/style.css         # Styling
│   ├── js/app.js             # Frontend logic
│   └── uploads/              # User uploads (auto-created)
├── utils/
│   ├── ocr.py                # OCR extraction
│   ├── matcher.py            # Medicine matching
│   ├── medicine_index.faiss  # FAISS index (generated)
│   └── medicine_data.pkl     # Dataset pickle (generated)
├── scripts/
│   └── rag_ingest.py         # Data ingestion script
└── data/
    └── Medicine_Details.csv  # Your dataset
```

## 🔧 Configuration

### Change Port
Edit `app.py` line 101:
```python
app.run(port=8000)  # Change 5000 to desired port
```

### Enable Debug Mode
Edit `app.py` line 100:
```python
debug=True,  # Set to True for development
```

### Increase Upload Size
Edit `app.py` line 17:
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # Change to desired size
```

## 📊 Dataset Requirements

Your `Medicine_Details.csv` must have these columns:

- `Medicine Name` - Name of the medicine
- `Composition` - Active ingredients
- `Uses` - What the medicine is used for
- `Side_effects` - Possible side effects (optional)
- `Manufacturer` - Medicine manufacturer (optional)

Example:
```
Medicine Name,Composition,Uses,Side_effects,Manufacturer
Aspirin,Acetylsalicylic acid 500mg,Pain relief,GI upset,Company A
```

## 🐛 Troubleshooting

### "ModuleNotFoundError"
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### "FAISS index not found"
```bash
# Run ingestion script
python scripts/rag_ingest.py
```

### "Medicine_Details.csv not found"
- Place your CSV in the `data/` folder
- Run `python scripts/rag_ingest.py` again

### OCR not working
- Check if EasyOCR is installed: `pip install easyocr`
- Ensure image is clear and well-lit
- Check EasyOCR models are downloaded (~100MB first run)

### Port already in use
```bash
# Change port in app.py or use:
flask run --port 5001
```

## 📈 Performance Tips

1. **Preprocessing**: Always preprocess images for better OCR
2. **File size**: Keep images under 10MB
3. **Lighting**: Ensure good lighting for OCR
4. **Angle**: Hold camera straight for better text extraction
5. **Crop**: Crop images to show composition text clearly

## 🚀 Deployment

### Local Production
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker
```bash
docker build -t medicine-identifier .
docker run -p 5000:5000 medicine-identifier
```

### Heroku
```bash
heroku create your-app-name
git push heroku main
```

## 📝 Useful Commands

```bash
# Activate environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install specific package
pip install package_name

# List installed packages
pip list

# Freeze dependencies
pip freeze > requirements.txt

# Run app with debugging
FLASK_APP=app.py FLASK_ENV=development flask run

# Run tests
pytest tests/
```

## 📚 Useful Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [FAISS Documentation](https://faiss.ai/)
- [Sentence Transformers](https://www.sbert.net/)

## 💡 Tips

- Create a `.env` file for sensitive configuration
- Use `python-dotenv` to load environment variables
- Add logging for debugging production issues
- Set up error tracking with Sentry
- Monitor API performance with Prometheus

## 📞 Support

For issues, check:
1. README.md for full documentation
2. Error messages in terminal/logs
3. Check if all dependencies are installed
4. Ensure dataset is in correct format

---

**Happy Medicine Identifying! 💊**
