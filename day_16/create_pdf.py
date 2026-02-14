"""
Run this script to create the loksewa_questions.pdf file
Usage: python create_pdf.py

This creates the PDF that the RAG system will index.
Place the output in: ./data/loksewa_questions.pdf
"""

import os

def create_pdf_from_text():
    """Create PDF using reportlab (most reliable library)"""
    
    # Read the text content
    text_file = "loksewa_questions.txt"
    
    if not os.path.exists(text_file):
        print(f"Error: {text_file} not found!")
        print("Make sure loksewa_questions.txt is in the same directory")
        return
    
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try reportlab first
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT
        
        print("Using reportlab to create PDF...")
        
        # Create output directory
        os.makedirs("./data", exist_ok=True)
        output_path = "./data/loksewa_questions.pdf"
        
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Styles
        styles = getSampleStyleSheet()
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6
        )
        
        # Build content
        story = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            
            # Detect headings
            if line.startswith('SECTION') or line.isupper() and len(line) > 5:
                # Replace Unicode chars that might cause issues
                clean_line = line.encode('ascii', 'ignore').decode('ascii')
                if clean_line.strip():
                    story.append(Paragraph(clean_line, heading_style))
            else:
                # Normal text - handle unicode
                clean_line = line.encode('ascii', 'ignore').decode('ascii')
                if clean_line.strip():
                    story.append(Paragraph(clean_line, normal_style))
        
        # Build PDF
        doc.build(story)
        print(f"✅ PDF created successfully: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        return True
        
    except ImportError:
        print("reportlab not installed. Trying alternative...")
        return create_simple_pdf(content)
    except Exception as e:
        print(f"reportlab error: {e}")
        return create_simple_pdf(content)


def create_simple_pdf(content):
    """Fallback: Create PDF using only built-in Python"""
    try:
        os.makedirs("./data", exist_ok=True)
        output_path = "./data/loksewa_questions.pdf"
        
        # Minimal PDF structure
        lines = [line for line in content.split('\n') if line.strip()]
        
        # PDF header
        pdf_lines = []
        pdf_lines.append("%PDF-1.4\n")
        
        # Encode text content (ASCII only for compatibility)
        text_content = ""
        for line in lines[:200]:  # First 200 lines
            clean = line.encode('ascii', 'ignore').decode('ascii')
            if clean.strip():
                text_content += clean + "\\n"
        
        # Simple PDF objects
        objects = []
        
        # Object 1: Catalog
        objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        
        # Object 2: Pages
        objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        
        # Object 3: Page
        objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
        
        # Object 4: Content stream
        stream = f"BT\n/F1 10 Tf\n50 750 Td\n12 TL\n"
        
        for line in lines[:100]:
            clean = line.encode('ascii', 'ignore').decode('ascii')[:80]  # Limit line length
            if clean.strip():
                # Escape special PDF characters
                clean = clean.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
                stream += f"({clean}) Tj\nT*\n"
        
        stream += "ET\n"
        stream_bytes = stream.encode('latin-1')
        
        objects.append(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream\nendobj\n")
        
        # Object 5: Font
        objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
        
        # Write PDF
        with open(output_path, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            offsets = []
            pos = 8
            
            for obj in objects:
                offsets.append(pos)
                obj_bytes = obj.encode('latin-1')
                f.write(obj_bytes)
                pos += len(obj_bytes)
            
            # Cross-reference table
            xref_pos = pos
            f.write(b"xref\n")
            f.write(f"0 {len(objects) + 1}\n".encode())
            f.write(b"0000000000 65535 f \n")
            for offset in offsets:
                f.write(f"{offset:010d} 00000 n \n".encode())
            
            # Trailer
            f.write(b"trailer\n")
            f.write(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode())
            f.write(b"startxref\n")
            f.write(f"{xref_pos}\n".encode())
            f.write(b"%%EOF\n")
        
        print(f"✅ Simple PDF created: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error creating PDF: {e}")
        print("\nFallback: Saving as .txt file instead")
        
        # Last resort: save as text that PyPDFLoader can handle
        with open("./data/loksewa_questions.txt", 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Saved as text file: ./data/loksewa_questions.txt")
        print("Note: Update _index_past_papers() to use TextLoader instead of PyPDFLoader")
        return False


if __name__ == "__main__":
    print("Creating Lok Sewa study material PDF...")
    print("=" * 50)
    
    success = create_pdf_from_text()
    
    if success:
        print("\n✅ Setup complete!")
        print("Next steps:")
        print("1. Make sure GROQ_API_KEY is in .env")
        print("2. Run: fastapi dev app/main.py")
        print("3. Go to: http://localhost:8000/docs")
        print("4. Register → Login → Generate Questions!")
    else:
        print("\n⚠️ PDF creation had issues.")
        print("Install reportlab: pip install reportlab")
        print("Then run this script again.")