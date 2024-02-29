## Speech to speech using audio file. 

from flask import Flask, render_template, request
from googletrans import Translator
from googletrans import LANGUAGES
from gtts import gTTS
import speech_recognition as sr
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import fitz
import tempfile
import logging
import os


app = Flask(__name__)

# Get a dictionary of language codes and their corresponding names
language_codes = LANGUAGES

# Create the 'uploads' directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Function to translate text
def translate_text(text, target_lang):
    translator = Translator()
    translation = translator.translate(text, dest=target_lang)
    return translation.text

# Function to perform speech recognition
def recognize_audio_speech(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        detected_language = recognizer.recognize_google(audio_data, language="auto")
        return detected_language, recognizer.recognize_google(audio_data)
    
# Function to perform speech recognition from microphone
def recognize_microphone_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak something...")
        audio_data = recognizer.listen(source)
        print("Recognizing...")
        detected_language = recognizer.recognize_google(audio_data, language="auto")
        return detected_language, recognizer.recognize_google(audio_data)

# Function to perform OCR on an image file
def process_image_file(image_path, target_lang):
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(img)
        translated_text = translate_text(text, target_lang)
        return translated_text

# Function to get ISO 639-1 language code from language name
def get_language_code(language_name):
    for code, name in LANGUAGES.items():
        if name.lower() == language_name.lower():
            return code
    return None

# Function to perform OCR on image
def perform_ocr_on_image(image_path):
    text = pytesseract.image_to_string(image_path)
    return text

# Function to generate audio from text
def generate_audio(text, lang):
    try:
        if lang in LANGUAGES.values():
            lang_code = {v: k for k, v in LANGUAGES.items()}[lang]
            tts = gTTS(text=text, lang=lang_code)
            audio_filename = "static/translated_audio.mp3"  # Save audio to a fixed filename
            tts.save(audio_filename)
            return audio_filename
        else:
            return None
    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        return None

# Route for the home page
@app.route('/')  

@app.route("/translate", methods=["GET", "POST"])
def translate():
    if request.method == "POST":
        # Check if the post request has the file part
        if 'file' not in request.files:
            return render_template("index.html", languages=language_codes.values(), error="No file part")
        
        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return render_template("index.html", languages=language_codes.values(), error="No selected file")
        
        if file:
            # Save the uploaded audio file
            filename = secure_filename(file.filename)
            audio_path = os.path.join('uploads', filename)
            file.save(audio_path)

            # Perform speech recognition
            detected_language, speech_text = recognize_audio_speech(audio_path)

            # Translate the recognized text
            target_language = request.form.get("target_language")
            # Get ISO 639-1 language code for target language
            target_language_code = next((code for code, name in language_codes.items() if name == target_language), None)
            if not target_language_code:
                return render_template("index.html", languages=language_codes.values(), error="Invalid target language")
            translated_text = translate_text(speech_text, target_language_code)

            # Perform text-to-speech conversion for translated text
            tts = gTTS(translated_text, lang=target_language_code)
            audio_filename = f"static/translated_{filename}"
            tts.save(audio_filename)

            return render_template("index.html", languages=language_codes.values(), 
                                    detected_language_1=detected_language,
                                    speech_text_1=speech_text, 
                                    translated_audio_text=translated_text, 
                                    audio_filename=audio_filename)

    return render_template("index.html", languages=language_codes.values())

@app.route("/translate_microphone", methods=["GET", "POST"])
def translate_microphone():
    if request.method == "POST":
        # Perform speech recognition from microphone
        detected_language, speech_text = recognize_microphone_speech()

        # Translate the recognized text
        target_language = request.form.get("target_language")
        # Get ISO 639-1 language code for target language
        target_language_code = next((code for code, name in language_codes.items() if name == target_language), None)
        if not target_language_code:
            return render_template("index.html", languages=language_codes.values(), error="Invalid target language")
        translated_text = translate_text(speech_text, target_language_code)

        # Perform text-to-speech conversion for translated text
        tts = gTTS(translated_text, lang=target_language_code)
        audio_filename = f"static/translated_audio.mp3"
        tts.save(audio_filename)

        return render_template("index.html", languages=language_codes.values(), 
                                detected_language_2=detected_language,
                                speech_text_2=speech_text, 
                                microphone_audio_translated_text=translated_text, 
                                audio_filename=audio_filename)

    return render_template("index.html", languages=language_codes.values())

# Route for the home page
@app.route("/translate_image_upload", methods=["GET", "POST"])
def translate_image_upload():
    if request.method == "POST":
        if 'translate' in request.form:
            # Translate text from uploaded image
            target_language_name = request.form.get("target_language")
            target_language_code = get_language_code(target_language_name)
            if not target_language_code:
                return render_template("index.html", languages=language_codes.values(), error="Invalid target language")

            image_file = request.files['image_file']
            if image_file.filename == '':
                return render_template("index.html", languages=language_codes.values(), error="No file selected")

            # Save uploaded image file
            image_path = os.path.join('uploads', image_file.filename)
            image_file.save(image_path)

            # Process image file using OCR and translate the extracted text
            translated_text = process_image_file(image_path, target_language_code)

            # Perform text-to-speech conversion for translated text
            tts = gTTS(translated_text, lang=target_language_code)
            audio_filename = f"static/translated_audio.mp3"
            tts.save(audio_filename)

            # Remove uploaded image file
            os.remove(image_path)

            return render_template("index.html", languages=language_codes.values(),
                                    image_translated_text=translated_text, audio_filename_1=audio_filename)

    return render_template("index.html", languages=language_codes.values())

# Route for the home page
@app.route("/translate_image_pdf", methods=["GET", "POST"])
def translate_image_pdf():
    if request.method == "POST":
        # Get target language
        target_language = request.form.get("target_language")
        
        # Handle uploaded PDF file
        uploaded_file = request.files["pdf_file"]
        if uploaded_file.filename == "":
            return render_template("index.html", languages=language_codes.values(), error="No file selected")

        # Save the PDF file to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, uploaded_file.filename)
            uploaded_file.save(pdf_path)

            # Process the PDF file
            text = ""
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    if page.get_text():
                        text += page.get_text()
                    else:
                        image_list = page.get_images(full=True)
                        for image_index, img in enumerate(image_list):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]
                            image_name = os.path.join(temp_dir, f"page_{page_num}_image_{image_index}.{image_ext}")
                            with open(image_name, "wb") as image_file:
                                image_file.write(image_bytes)
                            image_text = perform_ocr_on_image(image_name)
                            text += image_text + "\n"
                            os.remove(image_name)  # Clean up the temporary image file

            if text.strip():
                translated_text = translate_text(text, target_language)
                audio_filename = generate_audio(translated_text, target_language)
                return render_template("index.html", languages=language_codes.values(), image_embedded_pdf_translated_text=translated_text, audio_filename_2=audio_filename)
            else:
                return render_template("index.html", languages=language_codes.values(), error="Text extraction from PDF failed. No text to translate.")

    return render_template("index.html", languages=language_codes.values())

if __name__ == "__main__":
    app.run(debug=True)