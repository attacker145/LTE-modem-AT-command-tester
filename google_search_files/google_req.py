import webbrowser


def google_search(query):
    url = "https://www.google.com/search"
    params = {"q": query}
    # Construct the full URL with query parameters
    full_url = f"{url}?q={query.replace(' ', '+')}"
    # Open the URL in the default web browser
    webbrowser.open(full_url)


if __name__ == '__main__':
    query = "Python programming"
    google_search(query)
