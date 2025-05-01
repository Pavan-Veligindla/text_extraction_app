from flask import Flask, request, render_template
import os
import pytesseract
from PIL import Image
import PyPDF2
import re


from fuzzywuzzy import fuzz

def extract_field(field_name, text):
    """
    Tries to find the value even with fuzzy OCR matches.
    """
    lines = text.split('\n')
    best_match_line = ''
    best_score = 0

    for line in lines:
        score = fuzz.partial_ratio(field_name.lower(), line.lower())
        if score > best_score:
            best_score = score
            best_match_line = line

    if best_score > 70:  # Threshold for matching
        parts = re.split(r'[:\-]', best_match_line, maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip()
    
    return "Not Found"


# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    text = ''
    try:
        # First, try normal extraction
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        print(f"Error reading PDF with PyPDF2: {e}")

    # If no text found, use OCR (image reading)
    if not text.strip():
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(pdf_path)
            for page in pages:
                text += pytesseract.image_to_string(page)
        except Exception as e:
            print(f"Error doing OCR: {e}")
    
    return text

def extract_required_fields(text, fields):
    result = {}
    for field in fields:
        field_value = extract_field(field, text)  # Use your regex function
        result[field] = field_value
    return result


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Get fields from form
        fields = request.form.get('fields')

        # 2. Get uploaded file
        file = request.files['pdf']

        # 3. Save uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 4. Extract text from PDF after saving
        text = extract_text_from_pdf(filepath)
        
        print("===== OCR Extracted Text =====")
        print(text)
        print("==============================")

        # 5. Extract required fields
        field_list = [f.strip() for f in fields.split(',')]
        result = extract_required_fields(text, field_list)

        # 6. Return the results
        return render_template('result.html', result=result)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
