import logging

from GoogleAI.vertexai_google import get_predictions
from resources.cme_error_codes import get_cme_error_description
from google_search_files.google_req import google_search
from utils import decode_ip


class ModemResponses:
    """
    A class containing modem command strings and CEREG value descriptions.
    """

    def __init__(self, display_modem_response, update_note_tabs, google_search_chk, select_ai, verb):
        self.display_modem_response = display_modem_response
        self.update_note_tabs = update_note_tabs
        self.google_search_chk = google_search_chk
        self.select_ai = select_ai
        self.verb = verb

    # CEREG value descriptions
    CEREG00 = """
The first '0': This indicates that the device is not registered with the LTE network.
The second '0': This likely means that the device is not searching for a network to register with.
"+CEREG: 0,0" means that the device is not currently registered with an LTE network and is not actively trying to 
register.
No SIM card: The device might not have a SIM card inserted, or the SIM card might be faulty.
Poor or no signal: The device might be in an area with no LTE coverage, or the signal might be too weak to establish a 
connection.
Network issues: There might be a problem with the LTE network in the area.
Device configuration: The device might not be configured correctly to connect to the LTE network.
Device malfunction: There might be a problem with the device itself.
    """

    CEREG01 = """
The second '1': This means the device is registered to the home network.
Asynchronous Reporting: The "+CEREG" command can be set to provide updates about network registration 
status automatically, without you having to ask for it each time. This is called "unsolicited result codes" (URCs).
Status Changes: When your device is moving or experiencing changes in network coverage, it might quickly switch between 
different registration states. The "+CEREG: 0,1" message could be a snapshot of a very brief moment where the device was 
registered to the home network while it was in the process of transitioning to a different state.
"+CEREG: 0,1", it likely means that your device was registered to the home network at some point, but it might not be at 
this exact instant. It could be:
Connecting: Your device is actively trying to connect to the LTE network.
Intermittent Connection: You might be in an area with fluctuating signal strength, causing your device to connect and 
disconnect briefly.
Recent Connection: Your device was recently connected but might have lost the connection due to various reasons.
    """

    CEREG02 = """
Not registered, but device is currently searching a new operator to register to
    """

    CEREG05 = """
The second '5': This means the device is registered to a roaming network.
In simpler terms, "+CREG: 0,5" means your device is currently using a network that is not its primary or "home" network. 
This usually happens when you are traveling in a different region or country.
Things to keep in mind about roaming:

Roaming charges: Using a roaming network can often incur extra charges from your mobile carrier. Be sure to check your 
plan for roaming rates.
Data usage: Data used while roaming might be charged differently or at a higher rate than data used on your home network.
Network availability: Roaming networks might not always offer the same level of coverage or service quality as your home 
network.
    """

    CEREG11 = """
The first '1': Subscribe unsolicited result codes +CEREG:<stat>
The second '1': This means that the device is currently roaming.
    """

    CEREG21 = """
The first '2': Subscribe unsolicited result codes +CEREG:<stat>[,<tac>,<ci>,<AcT>]
The second '1': Registered, home network
"+CEREG: 2,1" means that the device is registered with its home LTE network but is currently roaming.
    """

    CEREG22 = """
The first '2': Subscribe unsolicited result codes +CEREG:<stat>[,<tac>,<ci>,<AcT>]
The second '2': This means that the device is not currently roaming.
"+CEREG: 2,2" means that the device is registered with its home LTE network and is not roaming.
    """

    CEREG03 = """
Registration denied. This means the device tried to register with the network but was rejected. Keep trying to register.
Possible reasons for registration denial:
SIM card issues: The SIM card might be invalid, not inserted properly, or have a problem.
Network coverage: The device might be in an area with no network coverage.
Network issues: There could be temporary issues with the network preventing registration.
Device configuration: Incorrect settings on the device might be preventing it from registering.
Network restrictions: The network operator might have restrictions on the device or SIM card.
Troubleshooting steps:

Check the SIM card: Ensure the SIM card is valid and inserted correctly.
Check network coverage: Move to an area with better network reception.
Restart the device: Sometimes a simple restart_commands can resolve temporary glitches.
Check device settings: Verify that the device's network settings are correct.
Contact the network operator: If the issue persists, contact your network operator for assistance.
To see the reason for deny:
Run: AT+qcfg="emmcause"
    """

    CPSMS = """
Power Saving Mode 
    """

    COPS_Q = """  
The read command AT COPS? returns the current mode, the registered operator, and radio access technology. 
        """

    AT_V = """
This output shows the current settings of a modem. Let's break down each line:
AT&V: This command itself requests the modem to display its current configuration.  It's the "show settings" command.
&C: 1:  Flow control. &C: 1 typically means hardware flow control (RTS/CTS) is enabled. This is a good practice for reliable communication.
&D: 2: Data Terminal Ready (DTR) control. &D: 2 usually means the modem will hang up the connection if DTR is dropped 
by the computer.
&F: 0: Factory defaults. &F: 0 indicates that the modem is not currently using factory default settings.  If it were, 
it would likely be &F: 1.
&W: 0: Write settings. &W: 0 means the current settings are not being saved to non-volatile memory.  If you wanted to 
save the current configuration, you would use AT&W.
Q: 0: Quiet mode. Q: 0 means the modem is sending result codes (like "OK"). Q: 1 would suppress these codes.
V: 1: Verbose mode. V: 1 means the modem is sending verbose result codes (e.g., "CONNECT" instead of just "OK").
X: 4:  This parameter controls how the modem handles call progress tones and other events.  X: 4 is a common setting, 
but the exact meaning can vary slightly between modems. Consult the modem's documentation for specifics. It often relates 
to how the modem reports ring, busy, and other call states.
Z: 0:  This is usually related to restoring a specific stored profile. Z: 0 likely means no specific profile is being loaded.
E: 1: Echo. E: 1 means the modem is echoing back the commands you type. This is helpful for seeing what you're sending.
S0: 0: Auto-answer. S0: 0 means the modem will not automatically answer incoming calls.
S4: 10:  This S-register often relates to the time the modem waits before going online after a call is established. The 
value of 10 likely refers to a delay in tenths of a second (1 second).
S5: 8: This S-register typically sets the delay between a carriage return and the start of the result code.
S6: 2: This S-register often controls the time the modem waits for a carrier tone during call setup.
S7: 0: This S-register is usually related to the time the modem waits for a connection after dialing.
S8: 2:  This S-register often controls the time the modem waits before disconnecting after a call.
S10: 15: This S-register usually sets the time between rings before the modem answers (if auto-answer is enabled). 
Since S0 is 0, this is irrelevant in this configuration.
S3: 13: This S-register often relates to the number of rings before the modem answers (if auto-answer is enabled). 
Since S0 is 0, this is irrelevant in this configuration.
OK: This is the modem's response indicating that the AT&V command was executed successfully.
In summary, this output shows the modem's current configuration, including settings for flow control, DTR handling, 
various timers, and other parameters.  The S registers are particularly important and control a wide range of modem 
behavior.  If you need to change any of these settings, you would use other AT commands, like AT&W to save them.  
Remember to consult the specific documentation for your modem for the precise meaning of each setting, as they can vary slightly.
    """

    CBC = """
0: Indicates the battery charging status (e.g., 0 = not charging).
81: Represents the battery capacity percentage (e.g., 81% charged).
4012: Indicates the battery voltage in milli volts (e.g., 4.012 volts).
    """

    modem_response_dict = {
        "+CEREG: 0,0": CEREG00,
        "+CREG: 0,0": CEREG00,
        "+CEREG: 0,1": CEREG01,
        "+CREG: 0,1": CEREG01,
        "+CEREG: 0,2": CEREG02,
        "+CREG: 0,2": CEREG02,
        "+CEREG: 0,5": CEREG05,
        "+CREG: 0,5": CEREG05,
        "+CEREG: 0,3": CEREG03,
        "+CREG: 0,3": CEREG03,
        "+CPSMS:": CPSMS,
        "+COPS:": COPS_Q,
        "AT&V": AT_V,
        "+CBC": CBC
    }

    def process_modem_response_sub(self, read_val):
        read_val_stripped = read_val.strip()

        """if read_val.startswith("AT#SD=1"):
            self.display_modem_response(f"Wait for CONNECT...   {read_val}")
        else:
            self.display_modem_response(read_val)"""

        if read_val and read_val not in ("\r", "\n"):
            logging.info(read_val)

        if self.google_search_chk.get() == 1:
            read_val = read_val.split("\n")  # ['AT+QIACT=1', 'ERROR']
            first_part = read_val[0]  # "AT+QIACT=1"
            second_part = read_val[1]  # "ERROR"
            joined_val = " ".join([first_part, second_part])  # Google search request: "AT+QIACT=1 ERROR"
            print(joined_val)
            google_search(joined_val)

        if "+QIOPEN: 0,0" in read_val:
            self.update_note_tabs("TCP client is connected successfully")
        elif "AT#CGPADDR=" in read_val:
            ip_address = decode_ip(read_val)
            self.update_note_tabs(f"Modem IP: {ip_address}")
        elif "ERROR" in read_val:   # <---------------------------------------------- Modem ERROR response
            print(read_val)
            cme_error = get_cme_error_description(read_val)
            wait_message = f"Modem Error: {read_val}"
            if self.select_ai.get() == 1:  # If AI response is enabled
                wait_message += ", wait for AI response..."
                self.display_modem_response(wait_message)
                read_val = get_predictions(f"Error response to command {read_val}")
                logging.info(read_val)
                self.display_modem_response(read_val)
            else:
                self.display_modem_response(read_val + "\n" + cme_error)
                logging.error(read_val)
        else:
            self.display_modem_response(read_val)
            for key, value in ModemResponses.modem_response_dict.items():  # From modem_responses.py file, modem_response_dict dictionary
                if key in read_val_stripped:
                    if self.verb.get() == 1:
                        self.display_modem_response(value)  # modem_responses.py

                    if key in {"+CEREG: 0,0", "+CREG: 0,0", "+CEREG: 0,0", "+CREG: 0,0"}:
                        self.update_note_tabs("MT is not registered and Not currently searching a new operator to register to")
                    if key in {"+CEREG: 0,1", "+CREG: 0,1", "+CEREG: 0,5", "+CREG: 0,5"}:
                        self.update_note_tabs("MT is registered")
                    if key in {"+CEREG: 0,2", "+CREG: 0,2"}:
                        self.update_note_tabs("MT is not registered, but currently searching a new operator to register to")
                    if key in {"+CEREG: 0,3", "+CREG: 0,3"}:
                        self.update_note_tabs("MT registration was denied")
                    if key in {"+CEREG: 0,4", "+CREG: 0,4"}:
                        self.update_note_tabs("MT unknown (e.g. out of GERAN/UTRAN/E-UTRAN coverage)")
                    if key in {"+CEREG: 0,5", "+CREG: 0,5"}:
                        self.update_note_tabs("MT registered, roaming")
                    if key in {"+CEREG: 0,6", "+CREG: 0,6"}:
                        self.update_note_tabs("MT registered, roaming")
                    logging.debug(read_val)
                    break  # Exit loop after finding the first matching response





