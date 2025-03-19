import fitz  # PyMuPDF
import io
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def fill_pdf(input_pdf_path, output_pdf_path, user_data):
    print("DEBUG: Opening PDF:", input_pdf_path)

    doc = fitz.open(input_pdf_path)
    page = doc[0]  # Get the first page

    print("DEBUG: Filling PDF with user data...")

    # Define text positions for better alignment
    text_positions = {
        "First Name": (100, 150),
        "Last Name": (100, 170),
        "Email": (100, 190),
        "Phone": (100, 210),
        "Student ID": (100, 230),
    }

    text_data = {
        "First Name": user_data.get("first_name", ""),
        "Last Name": user_data.get("last_name", ""),
        "Email": user_data.get("email", ""),
        "Phone": user_data.get("phone", ""),
        "Student ID": user_data.get("student_id", ""),
    }

    # Insert text at correct positions
    for field, position in text_positions.items():
        value = text_data[field]
        print(f"DEBUG: Inserting '{field}: {value}' at {position}")
        page.insert_text(position, f"{field}: {value}", fontsize=12, fontname="helv", color=(0, 0, 0))

    # Embed signature if available
    if user_data.get("signature_path"):
        signature_path = user_data["signature_path"]
        signature_rect = fitz.Rect(400, 500, 550, 650)  # Adjust if needed
        page.insert_image(signature_rect, filename=signature_path)
        print("DEBUG: Signature inserted from", signature_path)

    # Save the modified PDF
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Store in Django's storage
    filename = f"filled_forms/{user_data['student_id']}_form.pdf"
    saved_path = default_storage.save(filename, ContentFile(buffer.read()))

    print("DEBUG: PDF saved at", saved_path)
    return saved_path
