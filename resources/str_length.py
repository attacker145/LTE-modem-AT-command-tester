def count_characters(string):
    """Return the number of characters in the given string."""
    return len(string)

# Test the function
if __name__ == "__main__":
    user_input = input("Enter a string: ")
    result = count_characters(user_input)
    print(f"The number of characters is: {result}")