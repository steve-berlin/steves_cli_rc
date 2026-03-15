import subprocess as sp

IP = input("Your remote control's subnet/IP: ")
print(f"Listening for ICMP echo requests from {IP}...")

while True:
    # The '-c 1' flag forces tcpdump to exit after capturing exactly 1 matching packet
    tcpdump_cmd = [
        "sudo", "tcpdump", "-i", "any", "-n", "-q", "-c", "1",
        f"icmp and icmp[icmptype] = icmp-echo and src net {IP}"
    ]

    # Blocks until a ping from the target IP is captured
    result = sp.run(tcpdump_cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    # If a packet is captured successfully, trigger the keypress script
    if result.returncode == 0:
        sp.run(["python3", "keypress.py"])

