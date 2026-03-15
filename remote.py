#!/usr/bin/env python3
"""steves_cli_rc — CLI remote control over WiFi via ICMP ping."""

import argparse   # parses command-line arguments
import shutil     # used to check if system tools are installed
import subprocess  # runs shell commands from python
import sys        # used for sys.exit()

# supported keypress tools and how to build their shell commands
# each entry: (tool name, function that builds the command list for a given key)
KEYPRESS_TOOLS = [
    ("xdotool", lambda key: ["xdotool", "key", key]),   # X11
    ("ydotool", lambda key: ["ydotool", "key", key]),    # Wayland
    ("wtype",   lambda key: ["wtype", "-k", key]),       # Wayland (wlroots)
]


def detect_keypress_tool():
    # filter the list down to only tools that exist on this system
    available = [(n, fn) for n, fn in KEYPRESS_TOOLS if shutil.which(n)]

    # bail if nothing is installed
    if not available:
        print("No keypress tool found. Install one of: xdotool, ydotool, wtype")
        sys.exit(1)

    # if only one tool exists, just use it automatically
    if len(available) == 1:
        name, cmd_fn = available[0]
        print(f"Using {name}.")
        return cmd_fn  # return the command-builder function

    # if multiple tools exist, let the user pick
    print("Multiple keypress tools detected:")
    for i, (name, _) in enumerate(available, 1):  # numbered list starting at 1
        print(f"  {i}) {name}")

    # keep asking until we get a valid choice
    while True:
        choice = input("Choose [1]: ").strip() or "1"  # default to 1 if empty
        try:
            idx = int(choice) - 1  # convert to 0-based index
            if 0 <= idx < len(available):  # bounds check
                print(f"Using {available[idx][0]}.")
                return available[idx][1]  # return the chosen command-builder
        except ValueError:
            pass  # non-numeric input, just retry
        print("Invalid choice.")


def listen(ip, key, cmd_fn):
    # build the tcpdump command that waits for exactly 1 ICMP ping from the target
    tcpdump_cmd = [
        "sudo",      # tcpdump needs root for raw packet capture
        "tcpdump",   # the packet capture tool
        "-i", "any",  # listen on all network interfaces
        "-n",        # don't resolve hostnames (faster)
        "-q",        # quiet output
        "-c", "1",   # stop after capturing 1 packet
        # BPF filter: only match ICMP echo requests from the given IP/subnet
        f"icmp and icmp[icmptype] = icmp-echo and src net {ip}",
    ]

    print(f"Listening for pings from {ip} — will press '{key}'...")

    # main loop: wait for ping -> press key -> repeat
    while True:
        # blocks here until a matching ping arrives (or tcpdump errors)
        result = subprocess.run(
            tcpdump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:  # 0 means a packet was captured
            # simulate the keypress using whichever tool was selected
            subprocess.run(
                cmd_fn(key), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )


def main():
    # set up CLI argument parsing
    parser = argparse.ArgumentParser(
        description="CLI remote control over WiFi via ICMP ping."
    )
    # required: the IP or subnet to listen for pings from
    parser.add_argument("ip", help="IP or subnet of the remote device")
    # optional: which key to simulate (defaults to spacebar)
    parser.add_argument(
        "-k", "--key", default="space", help="key to simulate (default: space)"
    )
    args = parser.parse_args()  # parse the arguments

    # make sure tcpdump is installed before we try to use it
    if not shutil.which("tcpdump"):
        print("tcpdump not found. Install it first.")
        sys.exit(1)

    cmd_fn = detect_keypress_tool()       # auto-detect or ask which keypress tool to use
    listen(args.ip, args.key, cmd_fn)     # start the listen loop


# standard python entry point guard
if __name__ == "__main__":
    main()
