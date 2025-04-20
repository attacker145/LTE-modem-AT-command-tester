import fitz  # PyMuPDF
import sys


def search_pdf(pdf_path, query):
    """
    Search for a given query string in a PDF file and return matching pages with context.
    """
    try:
        doc = fitz.open(pdf_path)
        results = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            if query.lower() in text.lower():
                results.append((page_num + 1, text))

        doc.close()

        if results:
            print(f"Found {len(results)} matches in '{pdf_path}':\n")
            for page_num, text in results:
                print(f"Page {page_num}:\n{text[:500]}...\n")  # Show first 500 chars for context
                print("-" * 80)
        else:
            print("No matches found.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # python search_pdf.py myfile.pdf "search term"
    """if len(sys.argv) < 3:
        print("Usage: python search_pdf.py <pdf_path> <query>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    query = " ".join(sys.argv[2:])"""
    search_pdf("TC_2G_3G_4G_Registration_Process_Application_Note_r4.pdf", "APN")
