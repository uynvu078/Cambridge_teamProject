import fitz  # PyMuPDF
import io
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime

def fill_pdf(input_pdf_path, output_pdf_path, user_data):
    print("DEBUG: Opening PDF:", input_pdf_path)

    doc = fitz.open(input_pdf_path)
    page = doc[0]  # Get the first page

    print("DEBUG: Filling PDF with user data...")

    # Extract current date
    current_date = datetime.today().strftime('%Y-%m-%d')

    # Define user data that needs to be inserted
    text_data = {
        "First Name": user_data.get("first_name", ""),
        "Last Name": user_data.get("last_name", ""),
        "Email": user_data.get("email", ""),
        "Phone": user_data.get("phone", ""),
        "Student ID": user_data.get("student_id", ""),
        "Current Date": current_date,
    }

    # 🔍 Auto-detect field positions instead of hardcoding coordinates
    field_mapping = {
        "First Name": ["First Name:", "Student Name:", "FName:", "First"],
        "Last Name": ["Last Name:", "LName:", "Last"],
        "Email": ["Email:", "UHEmail:"],
        "Phone": ["Phone:", "Phone#:"],
        "Student ID": ["Student ID:", "myUH ID:", "myUH#:"],
        "Current Date": ["Date:"]
    }

    for field, labels in field_mapping.items():
        for label in labels:
            found = page.search_for(label)
            if found:
                rect = found[0]  # Get the first matching field
                x, y = rect.x1 + 5, rect.y0  # Position text slightly to the right
                value = text_data[field]

                # Ensure names appear on the same line instead of being stacked
                if field == "First Name":
                    x += 50  # Shift right to align with Last Name field

                if field == "Last Name":
                    x += 120  # Shift further right

                # Adjust font size dynamically
                font_size = 10 if len(value) < 20 else 8

                print(f"DEBUG: Inserting '{field}: {value}' at {x}, {y}")
                page.insert_text((x, y), value, fontsize=font_size, fontname="helv", color=(0, 0, 0))
                break  # Stop searching once the first match is found

    # ✅ Embed signature correctly
    if user_data.get("signature_path"):
        signature_path = user_data["signature_path"]
        try:
            # Find where "Signature" appears on the form
            signature_fields = page.search_for("Signature")
            if signature_fields:
                sig_rect = signature_fields[0]  # Use first signature field
                sig_x0, sig_y0, sig_x1, sig_y1 = sig_rect.x0, sig_rect.y0, sig_rect.x1 + 50, sig_rect.y1 + 30

                # Insert the signature image resized to fit properly
                page.insert_image(fitz.Rect(sig_x0, sig_y0, sig_x1, sig_y1), filename=signature_path)
                print(f"DEBUG: Signature inserted at {sig_x0}, {sig_y0}")
        except Exception as e:
            print(f"ERROR: Could not insert signature: {e}")

    # Save modified PDF
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    filename = f"filled_forms/{user_data['student_id']}_form.pdf"
    saved_path = default_storage.save(filename, ContentFile(buffer.read()))

    print("DEBUG: PDF saved at", saved_path)
    return saved_path
