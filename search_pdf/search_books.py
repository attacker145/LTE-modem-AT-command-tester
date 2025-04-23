import os
import pdfplumber
import subprocess
import sys


def extract_text_from_pdf(pdf_path, query):
    """Extract text from a PDF file using pdfplumber and return all matching pages."""
    matching_pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and query.lower() in page_text.lower():
                    matching_pages.append(page_num)  # Store all matching pages
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return (pdf_path, matching_pages) if matching_pages else None


def find_and_open_first_match(root_dir, query):
    """Search for the first PDF that contains the query and open it."""
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_path = os.path.join(subdir, file)
                print(f"Searching: {file_path}")  # Display the current file being searched
                result = extract_text_from_pdf(file_path, query)
                if result:
                    book_path, page_numbers = result
                    print(f"Found relevant information in: {book_path} on pages {page_numbers}")

                    # Open the PDF file automatically
                    open_pdf(book_path)

                    return result  # Stop searching after the first match
    return None


def open_pdf(pdf_path):
    """Open a PDF file using the default viewer."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(pdf_path)  # Windows
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", pdf_path])  # macOS
        else:
            subprocess.Popen(["xdg-open", pdf_path])  # Linux
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")


if __name__ == '__main__':
    # Example usage
    books_dir = r"C:\Users\Name\Documents\Github\LTE-UI\search_pdf\CAT-M1"
    query = "COPS"  # Search term

    result = find_and_open_first_match(books_dir, query)

    if not result:
        print("No books found with the requested information.")
