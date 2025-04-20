cme_errors = {
    0: "Phone failure",
    1: "No connection to phone",
    2: "Phone-adaptor link reserved",
    3: "Operation not allowed",
    4: "Operation not supported",
    5: "PH-SIM PIN required",
    10: "SIM not inserted",
    11: "SIM PIN required",
    12: "SIM PUK required",
    13: "SIM failure",
    14: "SIM busy",
    15: "SIM wrong",
    16: "Incorrect password",
    17: "SIM PIN2 required",
    18: "SIM PUK2 required",
    20: "Memory full",
    21: "Invalid index",
    22: "Not found",
    23: "Memory failure",
    24: "Text string too long",
    25: "Invalid characters in text string",
    26: "Dial string too long",
    27: "Invalid characters in dial string",
    30: "No network service",
    31: "Network timeout",
    32: "Network not allowed - emergency calls only",
    40: "Network personalization PIN required",
    41: "Network personalization PUK required",
    42: "Network subset personalization PIN required",
    43: "Network subset personalization PUK required",
    44: "Service provider personalization PIN required",
    45: "Service provider personalization PUK required",
    46: "Corporate personalization PIN required",
    47: "Corporate personalization PUK required",
    100: "Unknown",
    103: "Illegal MS",
    106: "Illegal ME",
    107: "GPRS services not allowed",
    111: "PLMN not allowed",
    112: "Location area not allowed",
    113: "Roaming not allowed in this location area",
    132: "Service option not supported",
    133: "Requested service option not subscribed",
    134: "Service option temporarily out of order",
    148: "Unspecified GPRS error",
    149: "PDP authentication failure",
    150: "Invalid mobile class",
    256: "Operation temporarily not allowed",
    257: "Call barred",
    258: "Phone is busy",
    259: "User abort",
    260: "Invalid dial string",
    261: "SS not executed",
    262: "SIM blocked",
    263: "Invalid block",
    300: "ME failure",
    301: "SMS service of ME reserved",
    302: "Operation not allowed",
    303: "Operation not supported",
    304: "Invalid PDU mode parameter",
    305: "Invalid text mode parameter",
    310: "SIM not inserted",
    311: "SIM PIN required",
    312: "PH-SIM PIN required",
    313: "SIM failure",
    314: "SIM busy",
    315: "SIM wrong",
    316: "SIM PUK required",
    317: "SIM PIN2 required",
    318: "SIM PUK2 required",
    320: "Memory failure",
    321: "Invalid memory index",
    322: "Memory full",
    330: "SMSC address unknown",
    331: "No network service",
    332: "Network timeout",
    340: "No +CNMA acknowledgement expected",
    500: "Unknown error",
    527: "Please wait, and retry your selection later (Specific Modem Sierra)",
    528: "Location update failure – emergency calls only (Specific Modem Sierra)",
    529: "Selection failure – emergency calls only (Specific Modem Sierra)",
    772: "SIM powered down"
    # Note: Codes 512+ are manufacturer-specific and vary by vendor
}


def get_cme_error_description(error_string):
    """
    Takes a CME ERROR string (e.g., '+CME ERROR: 10') and returns the error description.
    Args: error_string (str): The error message in format '+CME ERROR: <err>'
    Returns:
        str: The error description, or an error message if the code is invalid/unrecognized
    """
    error_code_str = ""
    try:
        # Check if the input starts with '+CME ERROR:'
        # if not error_string.strip().startswith("+CME ERROR:"):
            # return "Command ERROR. Invalid CME ERROR format. Expected '+CME ERROR: <err>'"

        # Extract the error code part after '+CME ERROR:'
        error_code_str = error_string.split("+CME ERROR:")[1].strip()

        # Convert to integer (assuming numeric error code)
        error_code = int(error_code_str)

        # Look up the error code in the dictionary
        return cme_errors.get(error_code, f"Unknown CME ERROR code: {error_code}")

    except ValueError:
        # Handle case where error code isn't a number (verbose mode)
        return f"Non-numeric CME ERROR: {error_code_str}"
    except Exception as e:
        return f"Error processing CME ERROR: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Test cases
    print(get_cme_error_description("+CME ERROR: 10"))  # "SIM not inserted"
    print(get_cme_error_description("+CME ERROR: 30"))  # "No network service"
    print(get_cme_error_description("+CME ERROR: 999"))  # "Unknown CME ERROR code: 999"
    print(get_cme_error_description("Invalid input"))  # "Invalid CME ERROR format..."
    print(get_cme_error_description("+CME ERROR: text"))  # "Non-numeric CME ERROR: text"