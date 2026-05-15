// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const imageInput = document.getElementById('imageInput');
const previewSection = document.getElementById('previewSection');
const imagePreview = document.getElementById('imagePreview');
const identifyBtn = document.getElementById('identifyBtn');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

// Event Listeners
uploadArea.addEventListener('click', () => imageInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

/**
 * Handle file selection and preview
 */
function handleFileSelect(file) {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showError('Invalid file type. Please upload PNG, JPG, JPEG, BMP or GIF.');
        return;
    }

    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File is too large. Maximum size is 10MB.');
        return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadArea.style.display = 'none';
        previewSection.style.display = 'block';
        identifyBtn.disabled = false;
    };
    reader.readAsDataURL(file);

    // Store file for later use
    window.selectedFile = file;
}

/**
 * Clear upload and reset UI
 */
function clearUpload() {
    imageInput.value = '';
    window.selectedFile = null;
    uploadArea.style.display = 'block';
    previewSection.style.display = 'none';
    identifyBtn.disabled = true;
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}

/**
 * Predict medicine from uploaded image
 */
async function predict() {
    if (!window.selectedFile) {
        showError('Please select an image first.');
        return;
    }

    loading.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    identifyBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('image', window.selectedFile);

        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        loading.style.display = 'none';

        if (data.success) {
            displayResult(data);
        } else {
            showError(data.message, data.extracted_text);
        }
    } catch (error) {
        loading.style.display = 'none';
        showError('Unable to connect to server. Please try again.');
        console.error('Fetch error:', error);
    } finally {
        identifyBtn.disabled = false;
    }
}

/**
 * Display medicine identification result
 */
function displayResult(data) {
    const confidenceScore = parseInt(data.confidence);
    const confidenceClass = getConfidenceClass(confidenceScore);
    const confidenceLabel = getConfidenceLabel(confidenceScore);

    const resultHTML = `
        <h2>✅ Medicine Identified</h2>
        
        <div class="result-item">
            <div class="result-label">Medicine Name</div>
            <div class="result-value">${escapeHtml(data.medicine_name)}</div>
        </div>

        <div class="result-item">
            <div class="result-label">Composition</div>
            <div class="result-value">${escapeHtml(data.composition)}</div>
        </div>

        <div class="result-item">
            <div class="result-label">Uses</div>
            <div class="result-value">${escapeHtml(data.uses)}</div>
        </div>

        <div class="result-item">
            <div class="result-label">Side Effects</div>
            <div class="result-value">${escapeHtml(data.side_effects)}</div>
        </div>

        <div class="result-item">
            <div class="result-label">Manufacturer</div>
            <div class="result-value">${escapeHtml(data.manufacturer)}</div>
        </div>

        <div class="result-item">
            <div class="result-label">Confidence Score</div>
            <div class="result-value">
                <span class="confidence-badge ${confidenceClass}">
                    ${confidenceScore}% - ${confidenceLabel}
                </span>
            </div>
        </div>

        <div class="result-item">
            <div class="result-label">Extracted Text</div>
            <div class="extracted-text">${escapeHtml(data.extracted_text)}</div>
        </div>
    `;

    resultSection.innerHTML = resultHTML;
    resultSection.style.display = 'block';
}

/**
 * Show error message
 */
function showError(message, extractedText = null) {
    let errorHTML = `
        <h2>⚠️ ${message}</h2>
    `;

    if (extractedText) {
        errorHTML += `
            <p><strong>Extracted text:</strong></p>
            <div class="extracted-text">${escapeHtml(extractedText)}</div>
            <p style="margin-top: 12px; font-size: 13px;">
                If you see the extracted text above, you can manually search for the medicine in your database.
            </p>
        `;
    }

    errorHTML += `
        <p style="margin-top: 15px; font-size: 13px;"><strong>Try again with:</strong></p>
        <ul>
            <li>Clear, well-lit photo</li>
            <li>Visible medicine composition text</li>
            <li>Straight camera angle</li>
            <li>Close-up of the medicine strip/box</li>
        </ul>
    `;

    errorSection.innerHTML = errorHTML;
    errorSection.style.display = 'block';
}

/**
 * Get confidence score CSS class
 */
function getConfidenceClass(score) {
    if (score >= 80) return 'confidence-high';
    if (score >= 70) return 'confidence-medium';
    return 'confidence-low';
}

/**
 * Get confidence score label
 */
function getConfidenceLabel(score) {
    if (score >= 80) return 'High Confidence';
    if (score >= 70) return 'Medium Confidence';
    return 'Low Confidence';
}

/**
 * Escape HTML special characters for safe display
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Medicine Identifier loaded successfully');
    identifyBtn.disabled = true;
});
