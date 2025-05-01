from flask import Flask, request, render_template

import os

import tempfile

import re

import pytesseract

from pdf2image import convert_from_path
 
# Initialize the Flask application instance at the very top

app = Flask(__name__, template_folder='templates')
 
# Configure Tesseract (if needed)

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\1554\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
 
def extract_text_tesseract(pdf_path):

    """Extracts text from a PDF using Tesseract OCR."""

    text = ""

    images = convert_from_path(pdf_path)

    for i, image in enumerate(images):

        text += pytesseract.image_to_string(image) + "\n"

    return text

 
def extract_relevant_data(text, fields_to_extract):
    """Dynamically extracts specified fields from the text."""

    extracted_data = {}
    fields = [field.strip() for field in fields_to_extract.split(',')]

    for field in fields:
        #  Even more robust regex:
        #  -   Match field name and colon (or hyphen).
        #  -   Capture everything (including newlines) until:
        #      -   Another field name on a new line (with optional leading space)
        #      -   Two or more newlines
        #      -   The end of the string.
        pattern = re.compile(
            rf"{re.escape(field)}\s*[:\-]?\s*"  # Field name, optional colon/hyphen, optional space
            rf"((?:.|\n)*?)"
            rf"(?=\n\s*\w+\s*[:\-]|\n{{2,}}|\Z)",  # KEY CHANGE: More flexible lookahead
            re.IGNORECASE | re.DOTALL
        )
        print(f"Regex for {field}: {pattern.pattern}")
        match = pattern.search(text)

        if match:
                raw_value = match.group(1)
                print(f"Raw Matched Value for {field}: {raw_value}")
                extracted_data[field] = " ".join(raw_value.split()).strip()
        else:
            extracted_data[field] = None

    return extracted_data
 
@app.route('/', methods=['GET'])

def upload_form():

    print(f"Template folder: {app.template_folder}")  # Keep this for debugging

    return render_template('upload.html')
 
@app.route('/extract', methods=['POST'])

def extract():

    if 'pdf_file' not in request.files:

        return render_template('result.html', error='No file uploaded')
 
    pdf_file = request.files['pdf_file']

    if pdf_file.filename == '':

        return render_template('result.html', error='No filename provided')
 
    fields_to_extract = request.form.get('fields', '')  # Get the fields input

    print(f"Fields to extract: {fields_to_extract}")
 
    pdf_path = None

    try:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:

            pdf_file.save(temp_pdf.name)

            pdf_path = temp_pdf.name
        
            print(f"PDF saved to: {pdf_path}")

        print("--- Calling extract_text_tesseract ---")
 
        extracted_text = extract_text_tesseract(pdf_path)

        print("--- extract_text_tesseract returned ---")

        print("--- Extracted Text ---")

        print(extracted_text)

        print("--- End of Extracted Text ---")

        data = extract_relevant_data(extracted_text, fields_to_extract)

        return render_template('result.html', result=data)  # Changed 'data' to 'result' to match your template
 
    except Exception as e:

        print(f"An error occurred: {e}")

        return render_template('result.html', error=str(e))
 
    finally:

        if pdf_path:

            os.remove(pdf_path)

            print(f"Temporary PDF removed: {pdf_path}")
 
    return
 
if __name__ == '__main__':

    app.run(debug=True)
 