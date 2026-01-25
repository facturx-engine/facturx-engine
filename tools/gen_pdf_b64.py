import base64
from io import BytesIO
from reportlab.pdfgen import canvas

b = BytesIO()
c = canvas.Canvas(b)
c.drawString(100, 750, "Factur-X Smoke Test")
c.save()
pdf_bytes = b.getvalue()
with open("tools/temp_b64.txt", "w") as f:
    f.write(base64.b64encode(pdf_bytes).decode('utf-8'))
