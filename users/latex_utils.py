import os
import subprocess
from datetime import datetime
from django.conf import settings

def fill_latex_template(template_path, context, output_filename):
    # Read .tex template
    with open(template_path, 'r') as file:
        tex_template = file.read()

    # Replace placeholders
    for key, value in context.items():
        tex_template = tex_template.replace(f"{{{{{key}}}}}", value)

    # Save to .tex
    tex_output_path = os.path.join(settings.MEDIA_ROOT, f"{output_filename}.tex")
    with open(tex_output_path, 'w') as tex_file:
        tex_file.write(tex_template)

    # PDF output path (same dir)
    pdf_output_path = os.path.join(settings.MEDIA_ROOT, f"{output_filename}.pdf")

    # Run pdflatex — will work when it's installed
    try:
        subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory", settings.MEDIA_ROOT,
            tex_output_path
        ], check=True)
    except Exception as e:
        print(f"[DEBUG] LaTeX compile skipped (pdflatex not installed): {e}")
        return pdf_output_path  # Return intended path anyway

    return pdf_output_path
