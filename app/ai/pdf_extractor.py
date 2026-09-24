import os
import io
import pytesseract

from pypdf import PdfReader
from pdf2image import convert_from_bytes

from PIL import ImageOps, ImageEnhance, ImageFilter

# Tesseract ka path 

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Poppler ka path

POPPLER_PATH = os.getenv( "POPPLER_PATH", r"C:\poppler-24.07.0\Library\bin" )

# Image processing

def preprocess_image(image):

    # Convert karega grayscale mein
    image = image.convert("L")

    # Improve karega contarst wagairah
    image = ImageEnhance.Contrast(image).enhance(1.3)

    # unnecesary background ko remove karega 
    image = ImageOps.autocontrast(image)

    return image


# pdf extraction main yaha se hoga

def extract_text_from_pdf(pdf_file):

    pdf_bytes = pdf_file.read()

    # normal pdf extraction

    try:

        reader = PdfReader(io.BytesIO(pdf_bytes))

        extracted_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                extracted_text += page_text + "\n"

        if extracted_text.strip():

            print("Normal PDF text extraction successful.")

            return extracted_text.strip()

    except Exception as e:

        print( f"Normal PDF extraction failed: {e}" )

    # enhanced version extract karne ke liye

    try:
        
        print("No selectable text found.")
        print("Starting OCR...")

        images = convert_from_bytes( pdf_bytes, dpi=300, poppler_path=POPPLER_PATH )
        total_pages = len(images)

        print( f"OCR processing {total_pages} pages..." )

        ocr_text = ""
        
        for page_number, image in enumerate( images, start=1 ):

            print( f"OCR page {page_number}/{total_pages}" )

            # Prepare image
            processed_image = preprocess_image( image )

            # Tesseract configuration 
            # PSM 3 = automatic page segmentation
            # This is better for normal scanned lecture notes than forcing PSM 6.

            custom_config = "--oem 3 --psm 3"

            page_text = pytesseract.image_to_string( processed_image, lang="eng", config=custom_config  )

            if page_text.strip():

                ocr_text += ( f"\n\n--- Page {page_number} ---\n\n" )
                ocr_text += page_text.strip()


        if ocr_text.strip():

            print( "OCR extraction successful." )
            return ocr_text.strip()


        return None


    except Exception as e:

        print( f"OCR extraction failed: {e}" )

        raise Exception( "PDF text extraction and OCR both failed. "  "Please check Tesseract and Poppler installation. " f"Details: {str(e)}" )