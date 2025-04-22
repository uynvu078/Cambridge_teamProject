import os
import subprocess
from datetime import datetime
from django.conf import settings


def fill_latex_template(template_path, context, output_filename):
    # Read .tex template
    with open(template_path, 'r') as file:
        tex_template = file.read()

    # Replace placeholders safely
    for key, value in context.items():
        if value is None:
            print(f"⚠️ Warning: `{key}` is None — replaced with empty string.")
        tex_template = tex_template.replace(f"{{{{{key}}}}}", str(value or ""))

    # Save to .tex file
    tex_output_path = os.path.join(settings.MEDIA_ROOT, f"{output_filename}.tex")
    with open(tex_output_path, 'w') as tex_file:
        tex_file.write(tex_template)

    # Set up .pdf output path (same directory)
    pdf_output_path = os.path.join(settings.MEDIA_ROOT, f"{output_filename}.pdf")

    # Run pdflatex to compile to PDF (if installed)
    try:
        subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory", settings.MEDIA_ROOT,
            tex_output_path
        ], check=True)
    except Exception as e:
        print(f"[DEBUG] LaTeX compile skipped or failed: {e}")

    return pdf_output_path
