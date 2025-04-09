from utils.google_cld_vision import *

pdf_paths = [
    "uploads/pdf/02_소프트웨어품질.pdf",
]
combined_text = detect_text_pdf_path(pdf_paths)
print(combined_text)