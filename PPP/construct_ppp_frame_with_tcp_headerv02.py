import struct
import binascii
import socket


def checksum(data: bytes) -> int:
    """Calculate the Internet checksum."""
    if len(data) % 2 == 1:
        data += b'\x00'
    s = sum(struct.unpack('!%dH' % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


def create_ppp_frame(message: str) -> bytes:
    """
    Basic PPP Frame Format:

    Field	               Size	    Notes
    Flag	                1       byte	Always 0x7E start/end marker
    Address	                1       byte	Usually 0xFF
    Control	                1       byte	Usually 0x03
    Protocol	            2       bytes	Indicates what's in the payload (e.g., 0x0021 for IP, 0xC021 for LCP, etc.)
    Payload	             Variable	The real data you're interested in
    FCS (CRC)	            2       bytes	Frame Check Sequence (optional for your parsing if already validated)
    Flag	                1       byte	End 0x7E

    |0x7E|FF|03|00 21|<Payload>|CRC|0x7E|
    """
    FLAG = b'\x7E'

    ADDRESS = b'\xFF'
    CONTROL = b'\x03'
    PROTOCOL = b'\x21'
    ppp_header = ADDRESS + CONTROL + PROTOCOL

    # TCP Parameters
    """
    Field                Type         Size (bytes)    Meaning
    --------------------------------------------------------------------------------------
    src_port            unsigned short  2           Source port
    dst_port            unsigned short  2           Destination port
    seq_num             unsigned long   4           Sequence number
    ack_num             unsigned long   4           Acknowledgment number
    data_offset         unsigned char   1           Data offset (TCP header length)
    flags               unsigned char   1           TCP flags (e.g., ACK, PSH)
    window              unsigned short  2           Window size
    checksum            unsigned short  2           Checksum (initially 0 for calculation)
    urg_ptr             unsigned short  2           Urgent pointer (usually 0)
    """
    src_port = 1234
    dst_port = 80
    seq_num = 1000
    ack_num = 2000
    data_offset = (5 << 4)  # 5 words (20 bytes) shifted left by 4
    flags = 0x18  # PSH + ACK
    window = 1024
    urg_ptr = 0

    # Dummy IPs for pseudo-header
    src_ip = socket.inet_aton('192.168.1.100')
    dst_ip = socket.inet_aton('192.168.1.1')

    message_bytes = message.encode('utf-8')

    # Pseudo Header for Checksum
    pseudo_header = src_ip + dst_ip + struct.pack('!BBH', 0, socket.IPPROTO_TCP, 20 + len(message_bytes))

    # TCP header with zero checksum for now
    """
    ! - network byte order (big-endian)
    H - stands for an unsigned short (2 bytes or 16 bits)
    L - stands for an unsigned long (4 bytes or 32 bits)
    B - stands for an unsigned char (1 byte or 8 bits)
    """
    tcp_header = struct.pack('!HHLLBBHHH',
                             src_port,
                             dst_port,
                             seq_num,
                             ack_num,
                             data_offset,
                             flags,
                             window,
                             0,  # Checksum placeholder
                             urg_ptr)

    # Calculate TCP checksum
    tcp_checksum = checksum(pseudo_header + tcp_header + message_bytes)

    # Repack TCP header with correct checksum
    tcp_header = struct.pack('!HHLLBBHHH',
                             src_port,
                             dst_port,
                             seq_num,
                             ack_num,
                             data_offset,
                             flags,
                             window,
                             tcp_checksum,
                             urg_ptr)

    payload = tcp_header + message_bytes

    crc_input = ppp_header + payload
    crc_value = binascii.crc_hqx(crc_input, 0xFFFF)
    crc = struct.pack('<H', crc_value)

    ppp_frame = FLAG + ppp_header + payload + crc + FLAG

    print(f"PPP Frame (Hex): {binascii.hexlify(ppp_frame).decode('utf-8')}")
    return ppp_frame


def parse_tcp_header(frame: bytes):
    # Skip FLAG, PPP header
    tcp_start = 1 + 3  # FLAG + PPP Header
    tcp_header = frame[tcp_start:tcp_start + 20]

    fields = struct.unpack('!HHLLBBHHH', tcp_header)
    print(f"Source Port: {fields[0]}")
    print(f"Dest Port: {fields[1]}")
    print(f"Seq Num: {fields[2]}")
    print(f"Ack Num: {fields[3]}")
    print(f"Flags: {fields[5]}")
    print(f"Checksum: {hex(fields[7])}")
    return fields


def extract_ppp_payload(frame: bytes):
    if frame[0] != 0x7E or frame[-1] != 0x7E:
        raise ValueError("Invalid PPP Frame")
    print(frame)
    # Skip Flag(1) + Address(1) + Control(1) + Protocol(2)
    tcp_start = 24  # FLAG + PPP Header
    # Remove the FCS (last 3 bytes: 2-byte CRC + 1-byte end flag)
    payload_end = -3
    payload = frame[tcp_start:payload_end]  # Skip header, remove CRC+Flag
    return payload


if __name__ == "__main__":
    frame = create_ppp_frame("Hello World")
    print("PPP Frame Length:", len(frame))
    print("PPP Frame (Hex Dump):", binascii.hexlify(frame).decode())
    parse_tcp_header(frame)
    payload = extract_ppp_payload(frame)
    print(payload.decode('utf-8'))
