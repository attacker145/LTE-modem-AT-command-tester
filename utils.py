import re
import tkinter as tk
import time
from datetime import datetime, timedelta


def decode_ip(input_string):
    ip_address = None
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # Regular expression pattern for matching an IPv4 address
    match = re.search(ip_pattern, input_string)  # Search for the IP address in the input string
    if match:  # Check if a match was found
        # Extract and print the IP address
        ip_address = match.group(0)
        print(f"IP Address found: {ip_address}")
    else:
        print("No IP Address found in the input string.")
    return ip_address


def parse_csq_response(response):
    """
    Extracts RSSI and BER values from the +CSQ response.
    Args:
        response (str): The +CSQ response string.
    Returns:
        tuple: A tuple containing the RSSI and BER values.
    """
    lines = response.splitlines()
    for line in lines:
        if line.startswith("+CSQ:"):
            values = line.split(":")[1].split(",")
            rssi = int(values[0])
            ber = int(values[1])
            response = response + "\n" + "RSSI: {} dBm, BER(number of erroneous bits): {} bit error".format(rssi, ber)
            return response
    return response


def parse_at_atrfsts(response: str):
    parsed_data = {}  # Initialize a dictionary to store the parsed data
    response = response.replace("AT#RFSTS ", "").strip()  # Remove the prefix "AT#RFSTS " if it exists

    if "#RFSTS:" not in response:
        return response

    purged_response = response.replace("\n", " ").replace("\n\r", " ").strip()
    print(f"Purged Response: {purged_response}")  # Debug: Print the purged response
    # 1. Parse MCC and MNC
    mcc_mnc_pattern = r'"(\d{3}) (\d{3})"'
    mcc_mnc_match = re.search(mcc_mnc_pattern, purged_response)
    if mcc_mnc_match:
        parsed_data['mcc'] = mcc_mnc_match.group(1)
        parsed_data['mnc'] = mcc_mnc_match.group(2)
    else:
        parsed_data['mcc'] = parsed_data['mnc'] = None

    # 2. Parse EARFCN
    earfcn_pattern = r',(\d+),'
    earfcn_match = re.search(earfcn_pattern, purged_response)
    if earfcn_match:
        parsed_data['arfcn'] = int(earfcn_match.group(1))
    else:
        parsed_data['arfcn'] = None

    # 3. Parse RSRP, RSRQ, RSSI
    rsrp_rsrq_rssi_pattern = r'(-?\d+),(-?\d+),(-?\d+)'
    rsrp_rsrq_rssi_match = re.search(rsrp_rsrq_rssi_pattern, purged_response)
    if rsrp_rsrq_rssi_match:
        parsed_data['rxlev'] = int(rsrp_rsrq_rssi_match.group(1))
        parsed_data['rsrq'] = int(rsrp_rsrq_rssi_match.group(2))
        parsed_data['rssi'] = int(rsrp_rsrq_rssi_match.group(3))
    else:
        parsed_data['rxlev'] = parsed_data['rsrq'] = parsed_data['rssi'] = None

    # 4. Parse Cell ID, TAC, SNR
    cell_id_tac_snr_pattern = r',([\dA-F]+)?,,(\d+),(-?\d+)'
    cell_id_tac_snr_match = re.search(cell_id_tac_snr_pattern, purged_response)
    if cell_id_tac_snr_match:
        parsed_data['cell_id'] = cell_id_tac_snr_match.group(1) if cell_id_tac_snr_match.group(1) else "N/A"
        parsed_data['lac'] = int(cell_id_tac_snr_match.group(2))
        parsed_data['snr'] = int(cell_id_tac_snr_match.group(3))
    else:
        parsed_data['cell_id'] = parsed_data['lac'] = parsed_data['snr'] = None

    # 5. Parse eNB ID, IMEI, IMSI, Operator
    enb_imei_imsi_operator_pattern = r',([\dA-F]+),"(\d+)","(\d+)","([^"]+)"'
    enb_imei_imsi_operator_match = re.search(enb_imei_imsi_operator_pattern, purged_response)
    if enb_imei_imsi_operator_match:
        parsed_data['tmsi'] = enb_imei_imsi_operator_match.group(1)
        parsed_data['imei'] = enb_imei_imsi_operator_match.group(2)
        parsed_data['imsi'] = enb_imei_imsi_operator_match.group(3)
        parsed_data['operator'] = enb_imei_imsi_operator_match.group(4)
    else:
        parsed_data['tmsi'] = parsed_data['imei'] = parsed_data['imsi'] = parsed_data['operator'] = None

    # 6. Parse Band, Bandwidth, Temperature
    band_bandwidth_temp_pattern = r',(\d+),(\d+),(\d+)'
    band_bandwidth_temp_match = re.search(band_bandwidth_temp_pattern, purged_response)
    if band_bandwidth_temp_match:
        parsed_data['bsic'] = band_bandwidth_temp_match.group(1)
        parsed_data['bandwidth'] = int(band_bandwidth_temp_match.group(2))
        parsed_data['temperature'] = int(band_bandwidth_temp_match.group(3))
    else:
        parsed_data['bsic'] = parsed_data['bandwidth'] = parsed_data['temperature'] = None

    # Return the result in the specified format
    result = response + "\nAbsolute Radio Frequency Channel Number: {}".format(parsed_data["arfcn"]) \
             + "\nReceived Signal Level (RXLEV): {}".format(parsed_data["rxlev"]) \
             + "\nOperator: {}".format(parsed_data["operator"]) \
             + "\nLocation Area Code: {}".format(parsed_data["lac"]) \
             + "\nCell ID: {}".format(parsed_data["cell_id"]) + "\nTMSI: {}".format(parsed_data["tmsi"]) \
             + "\nBSIC: {}".format(parsed_data["bsic"]) + "\nMCC: {}".format(parsed_data["mcc"])

    return result


def parse_servinfo_response(response):
    """
    # Example usage:
    response = "#SERVINFO: 2300,-77,\"T-Mobile\",\"310260\",0000057,0028,128,3,-111\r\nOK"
    result = parse_servinfo_response(response)
    print("Original Response:")
    print(result["original_response"])
    print("\nService Information:")
    for key, value in result["servinfo"].items():
        print(f"{key}: {value}")

    Extracts service information from the #SERVINFO response.
    Args:
        response (str): The #SERVINFO response string.
    Returns:
        dict: A dictionary containing the original response and the service information.
    """
    lines = response.splitlines()
    for line in lines:
        if line.startswith("#SERVINFO:"):
            values = line.split(":")[1].split(",")
            servinfo = {
                "arfcn": int(values[0]),
                "rxlev": int(values[1]),
                "operator": values[2].strip('"'),
                "lac": values[3],
                "cell_id": values[4],
                "tmsi": values[5],
                "bsic": values[6],
                "mcc": values[7],
                "mnc": int(values[8]),
            }
            result = response + "\nAbsolute Radio Frequency Channel Number: {}".format(servinfo["arfcn"]) \
                     + "\nReceived Signal Level (RXLEV): {}".format(servinfo["rxlev"]) \
                     + "\nOperator: {}".format(servinfo["operator"]) \
                     + "\nLocation Area Code: {}".format(servinfo["lac"]) \
                     + "\nCell ID: {}".format(servinfo["cell_id"]) + "\nTMSI: {}".format(servinfo["tmsi"]) \
                     + "\nBSIC: {}".format(servinfo["bsic"]) + "\nMCC: {}".format(servinfo["mcc"]) \
                     + "\nMNC: {}".format(
                servinfo["mnc"]) + "\nRXLEV:\n-50 dBm to -80 dBm: Strong signal (good coverage)" \
                                   "\n-80 dBm to -90 dBm: Medium signal (fair coverage)" \
                                   "\n-90 dBm to -100 dBm: Weak signal (poor coverage)" \
                                   "\n-100 dBm to -110 dBm: Very weak signal (very poor coverage)"
            return result
    return response


def parse_cesq_response(response):
    """
    # Example usage:
    response = "+CESQ: 99,99,255,255,10,32\r\nOK"
    cesq = parse_cesq_response(response)
    for key, value in cesq.items():
        print(f"{key}: {value}")

    Extracts signal quality information from the +CESQ response.
    Args:
        response (str): The +CESQ response string.
    Returns:
        dict: A dictionary containing the signal quality information.
    """
    lines = response.splitlines()
    for line in lines:
        if line.startswith("+CESQ:"):
            values = line.split(":")[1].split(",")
            cesq = {
                "rssi": int(values[0]),
                "ber": int(values[1]),
                "rxqual": int(values[2]),
                "txqual": int(values[3]),
                "txpwr": int(values[4]),
                "full_txpwr": int(values[5])
            }
            result = {
                "original_response": response,
                "servinfo": cesq
            }
            return result
    return response


def create_checkbox(root, text, variable, row, column, command=None):
    checkbutton = tk.Checkbutton(root, text=text, bg='', variable=variable, onvalue=1,
                                 offvalue=0, command=command)
    checkbutton.grid(column=column, row=row, padx=0, pady=0)


class Timer:
    def __init__(self):
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time
            while self.is_running:
                self.elapsed_time = time.time() - self.start_time
                print(self.format_time(self.elapsed_time))
                time.sleep(1)
        return self.elapsed_time

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.elapsed_time = time.time() - self.start_time

    def reset(self):
        self.is_running = False
        self.elapsed_time = 0
        print("Timer reset to 00:00:00")

    def format_time(self, seconds):
        seconds = int(seconds)
        minutes = seconds // 60
        hours = minutes // 60
        return f"{hours:02d}:{minutes % 60:02d}:{seconds % 60:02d}"


def time_delay(delta_time):
    current_time = datetime.now()  # Get the current time
    delay = timedelta(seconds=delta_time)  # Define the delay
    end_time = current_time + delay  # Calculate the end time by adding the delay to the current time
    while datetime.now() < end_time:  # Loop until the end time is reached
        pass  # Empty loop body to simulate delay


def update_post_request_content_length(post_request, post_data):
    """
    Counts the number of characters in the POST data and updates the Content-Length header in the POST request.
    Args:
        post_request: A string representing the initial POST request headers.
        post_data: A string representing the data in the POST request body.
    Returns:
        A string representing the updated POST request with the correct
        Content-Length.
    """
    content_length = len(post_data)

    lines = post_request.splitlines()
    updated_lines = []
    content_length_found = False

    for line in lines:
        if line.lower().startswith("content-length:"):
            updated_lines.append(f"Content-Length: {content_length}")
            content_length_found = True
        else:
            updated_lines.append(line)

    if not content_length_found:
        updated_lines.append(f"Content-Length: {content_length}")

    updated_request = "\n".join(updated_lines) + "\n\n" + post_data
    return updated_request


if __name__ == '__main__':
    # Initial POST request headers
    initial_request = """POST /receiversvp/1235 HTTP/1.1
Host: www.uvdi-iot.com
Content-Type: application/x-www-form-urlencoded
Content-Length: 39"""

    # POST request data
    post_data = "rsvp=Hello, Roman Chak communicate 123434"

    # Update the Content-Length
    updated_request = update_post_request_content_length(initial_request, post_data)

    # Print the updated POST request
    print(updated_request)

    """# Sample response
    response = 'AT#RFSTS #RFSTS: "310 260",2300,-103,-70,-13,3B28,,128,19,0,2DAB003,"234500094385174","T-Mobile",3,4,158 OK'
    parsed_values = parse_at_atrfsts(response)
    print(parsed_values)
    
    timer = Timer()
    timer.start_timer()
    
    # Simulate some work
    time.sleep(2)
    
    elapsed = timer.get_elapsed_time()
    print(f"Elapsed time: {elapsed:.2f} seconds")"""
