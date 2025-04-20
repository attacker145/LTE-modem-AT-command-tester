import webbrowser
import sys


def google_search(search_query):
    try:

        # Check if input is empty
        if not search_query.strip():
            print("Error: Please enter a search term")
            return

        # Format the query for Google's URL
        google_query = search_query.replace(" ", "+")

        # Construct the full Google search URL
        google_url = f"https://www.google.com/search?q={google_query}"

        # Optional: Let user choose browser (uncomment to use)
        # print("Available browsers:")
        # print("1. Default browser")
        # print("2. Chrome")
        # print("3. Firefox")
        # choice = input("Select browser (1-3): ")

        # Open in default browser
        webbrowser.open(google_url)

        # For specific browsers, you can use:
        # Chrome: webbrowser.get('chrome').open(google_url)
        # Firefox: webbrowser.get('firefox').open(google_url)

        print("Search opened successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    search_query = "AT+COPS"
    google_search(search_query)