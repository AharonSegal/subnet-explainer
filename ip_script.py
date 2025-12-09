import re
import ipaddress

# MAIN INPUT : hard-code a single input
single_input_str = "192.0.2.10/27"

# ============================================================
#                    Terminal Colors
# ============================================================

class C:
    HEADER  = "\033[95m"
    OKBLUE  = "\033[94m"
    OKCYAN  = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL    = "\033[91m"
    ENDC    = "\033[0m"
    BOLD    = "\033[1m"

# ============================================================
#                    Parsing Function
# ============================================================

def parse_network(input_str: str) -> ipaddress.IPv4Network:
    """
    Parse input containing either:
    - CIDR notation  (59.89.212.216/14)
    - Full mask      (59.89.212.216 255.252.0.0)

    Accepted separators for mask: " ", "/", "-", ":"
    """
    # normalize separators
    cleaned = re.sub(r"[/\-:]+", " ", input_str.strip())
    parts = cleaned.split()

    if len(parts) != 2:
        raise ValueError(
            f"Bad format: '{input_str}'. Expected 'IP/CIDR' or 'IP MASK', "
            "e.g. '192.168.1.10/24' or '192.168.1.10 255.255.255.0'."
        )

    ip_part, mask_part = parts

    # validate IP
    try:
        ipaddress.IPv4Address(ip_part)
    except ipaddress.AddressValueError:
        raise ValueError(f"Invalid IP: {ip_part}")

    # CASE 1 — CIDR prefix number
    if mask_part.isdigit():
        cidr_value = int(mask_part)
        if not (0 <= cidr_value <= 32):
            raise ValueError("CIDR must be between 0-32.")
        return ipaddress.IPv4Network(f"{ip_part}/{cidr_value}", strict=False)

    # CASE 2 — full mask
    try:
        ipaddress.IPv4Address(mask_part)
    except ipaddress.AddressValueError:
        raise ValueError(f"Invalid subnet mask: {mask_part}")

    # convert long mask → CIDR
    try:
        prefix_len = ipaddress.IPv4Network(f"0.0.0.0/{mask_part}").prefixlen
    except (ipaddress.NetmaskValueError, ValueError):
        raise ValueError("Mask is not contiguous.")

    return ipaddress.IPv4Network(f"{ip_part}/{prefix_len}", strict=False)

# ============================================================
#                 Subnet Description Function
# ============================================================

def describe_subnet(network: ipaddress.IPv4Network) -> dict:
    # Compute first/last host without listing entire host set
    if network.num_addresses > 2:
        first = ipaddress.IPv4Address(int(network.network_address) + 1)
        last = ipaddress.IPv4Address(int(network.broadcast_address) - 1)
        first_str = str(first)
        last_str = str(last)
    else:
        first_str = "N/A"
        last_str = "N/A"

    return {
        "Network": str(network.network_address),
        "CIDR": f"/{network.prefixlen}",
        "Netmask": str(network.netmask),
        "First Host": first_str,
        "Last Host": last_str,
        "Broadcast": str(network.broadcast_address),
        "Next Subnet": str(network.network_address + network.num_addresses),
        "Total Addresses": network.num_addresses,
        "Usable Hosts": max(network.num_addresses - 2, 0),
    }

# ============================================================
#                 Pretty Colored Printer (Summary)
# ============================================================

def print_subnet_info(info: dict, label="TEST"):
    print(f"\n{C.BOLD}{C.OKBLUE}========== {label} =========={C.ENDC}")
    for key, value in info.items():
        color = C.OKGREEN if "Host" in key else C.OKCYAN
        print(f"{C.BOLD}{color}{key:<15}:{C.ENDC} {value}")

# ============================================================
#              Binary Helpers & Transition Logic
# ============================================================

def byte_to_bin_str(value: int) -> str:
    """Return an 8-bit binary string for a byte."""
    return f"{value:08b}"

def ip_to_bin_str(ip: ipaddress.IPv4Address) -> str:
    """Return IP in binary as 'xxxxxxxx/xxxxxxxx/...' per octet."""
    return "/".join(byte_to_bin_str(int(octet)) for octet in str(ip).split("."))

def mask_from_prefix(prefix: int) -> tuple[int, int, int, int]:
    """Return dotted decimal netmask bytes from prefix length."""
    if not (0 <= prefix <= 32):
        raise ValueError("Prefix must be between 0 and 32.")
    if prefix == 0:
        mask = 0
    else:
        mask = (0xffffffff << (32 - prefix)) & 0xffffffff
    return (
        (mask >> 24) & 0xff,
        (mask >> 16) & 0xff,
        (mask >> 8) & 0xff,
        mask & 0xff,
    )

def transition_info(prefix: int):
    """
    Given a prefix, return:
      - transition_index: 0-3 or None if prefix is multiple of 8 or 0
      - bits_in_transition: number of 1s in the transition octet (0-8)
    """
    if prefix == 0 or prefix % 8 == 0:
        return None, 0
    full_bytes = prefix // 8
    bits_in_transition = prefix % 8
    transition_index = full_bytes  # 0-based index
    return transition_index, bits_in_transition

# ============================================================
#            Detailed Explanation (Colored Output)
# ============================================================

def explain_network(original_ip: ipaddress.IPv4Address,
                    network: ipaddress.IPv4Network):
    """
    Print a detailed, colored explanation of how the subnet is
    calculated from the original IP and the network definition.
    """
    prefix = network.prefixlen
    netmask_bytes = mask_from_prefix(prefix)
    netmask = ipaddress.IPv4Address(".".join(str(b) for b in netmask_bytes))

    # Header
    print(f"\n{C.BOLD}{C.HEADER}----- DETAILED EXPLANATION -----{C.ENDC}")
    print(f"{C.BOLD}{C.OKCYAN}Input IP      :{C.ENDC} {original_ip}")
    print(f"{C.BOLD}{C.OKCYAN}Normalized CIDR:{C.ENDC} {network.network_address}/{prefix}")
    print(f"{C.BOLD}{C.OKCYAN}Netmask       :{C.ENDC} {netmask}")
    print()

    # BASE and SUBMASK in binary
    print(f"{C.BOLD}{C.OKBLUE}                BASE{C.ENDC}")
    print(f"{C.OKCYAN}{ip_to_bin_str(ipaddress.IPv4Address('0.0.0.0'))}{C.ENDC}")
    print()
    print(f"{C.BOLD}{C.OKBLUE}                SUBMASK{C.ENDC}")
    print(f"{C.OKCYAN}{ip_to_bin_str(netmask)}{C.ENDC}")
    print()

    # Transition byte info
    t_index, bits_in_transition = transition_info(prefix)
    if t_index is not None:
        t_byte = netmask_bytes[t_index]
        print(f"{C.BOLD}{C.OKGREEN}Transition byte index (0-based):{C.ENDC} {t_index}")
        print(f"{C.BOLD}{C.OKGREEN}Bits set in transition byte    :{C.ENDC} {bits_in_transition}")
        print(f"{C.BOLD}{C.OKGREEN}transition byte     ->{C.ENDC} {byte_to_bin_str(t_byte)}")
        print(
            f"{C.BOLD}{C.OKGREEN}the value of the byte ->{C.ENDC} "
            f"{byte_to_bin_str(t_byte)} = {t_byte}"
        )
    else:
        print(f"{C.BOLD}{C.WARNING}No partial transition byte (prefix multiple of 8 or /0).{C.ENDC}")
    print()

    # Step 1: Network Address calculation
    print(f"{C.BOLD}{C.OKBLUE}Step 1: Network Address (IP AND Netmask){C.ENDC}")
    ip_octets  = [int(o) for o in str(original_ip).split(".")]
    net_octets = [int(o) for o in str(network.network_address).split(".")]

    for i, (ip_o, mask_o, net_o) in enumerate(zip(ip_octets, netmask_bytes, net_octets), start=1):
        idx_label = {1: "1st", 2: "2nd", 3: "3rd"}.get(i, f"{i}th")
        print(
            f"{C.BOLD}{C.OKCYAN}{idx_label} byte:{C.ENDC} "
            f"{ip_o:3d} ({byte_to_bin_str(ip_o)})  AND  "
            f"{mask_o:3d} ({byte_to_bin_str(mask_o)})  =  "
            f"{C.OKGREEN}{net_o:3d} ({byte_to_bin_str(net_o)}){C.ENDC}"
        )

    print(
        f"\n{C.BOLD}{C.OKGREEN}Full network IP:{C.ENDC} "
        f"{C.OKGREEN}{network.network_address}{C.ENDC}"
    )
    print()

    # Step 2: First Host
    print(f"{C.BOLD}{C.OKBLUE}Step 2: First Host{C.ENDC}")
    if network.num_addresses > 2:
        first_host = ipaddress.IPv4Address(int(network.network_address) + 1)
        print(
            f"{C.OKCYAN}- First host = network IP + 1 → "
            f"{C.OKGREEN}{first_host}{C.ENDC}"
        )
    else:
        first_host = None
        print(
            f"{C.WARNING}- This subnet has no usable hosts by classical rules "
            f"(/31 or /32).{C.ENDC}"
        )
    print()

    # Step 3: Last Host
    print(f"{C.BOLD}{C.OKBLUE}Step 3: Last Host calculation{C.ENDC}")
    if network.num_addresses > 2:
        last_host = ipaddress.IPv4Address(int(network.broadcast_address) - 1)
        print(
            f"{C.OKCYAN}- Last Host = broadcast - 1 → "
            f"{C.OKGREEN}{last_host}{C.ENDC}"
        )
        print(
            f"{C.OKCYAN}- Usable hosts = Total addresses - 2 = "
            f"{network.num_addresses} - 2 = "
            f"{C.OKGREEN}{network.num_addresses - 2}{C.ENDC}"
        )
    else:
        last_host = None
        print(f"{C.WARNING}- No last host (no usable host addresses).{C.ENDC}")
    print()

    # Step 4: Broadcast Address
    print(f"{C.BOLD}{C.OKBLUE}Step 4: Broadcast Address{C.ENDC}")
    print(
        f"{C.OKCYAN}- Broadcast = all host bits set to 1 → "
        f"{C.OKGREEN}{network.broadcast_address}{C.ENDC}"
    )
    if last_host is not None:
        print(
            f"{C.OKCYAN}- Also: broadcast = last host + 1 → "
            f"{last_host} + 1 = {C.OKGREEN}{network.broadcast_address}{C.ENDC}"
        )
    print()

    # Step 5: Next Subnet
    print(f"{C.BOLD}{C.OKBLUE}Step 5: Next Subnet{C.ENDC}")
    next_net_int = int(network.network_address) + network.num_addresses
    next_net_ip = ipaddress.IPv4Address(next_net_int)
    print(
        f"{C.OKCYAN}- Next subnet starts at network_address + block size{C.ENDC}"
    )
    print(
        f"  {C.OKCYAN}= {network.network_address} + {network.num_addresses}"
        f"{C.ENDC}"
    )
    print(f"  {C.OKCYAN}= {C.OKGREEN}{next_net_ip}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}----- END EXPLANATION -----{C.ENDC}\n")

# ============================================================
#     Wrapper: Take raw input string, parse, and explain
# ============================================================

def explain_input_subnet(input_str: str):
    """
    Parse user input, compute network, and print a detailed explanation.
    Uses the IP part from the input as the 'original IP'.
    """
    cleaned = re.sub(r"[/\-:]+", " ", input_str.strip())
    parts = cleaned.split()
    if len(parts) != 2:
        raise ValueError(f"Bad format for explanation: '{input_str}'")

    ip_part, _ = parts
    original_ip = ipaddress.IPv4Address(ip_part)
    network = parse_network(input_str)
    explain_network(original_ip, network)

# ============================================================
#                      TEST CASES
# ============================================================

TEST_CASES = [
    # normal CIDR
    "59.89.212.216/14",
    "192.168.1.10/24",
    "10.0.0.1/8",
    "172.16.5.10/16",

    # full masks
    "192.168.1.10 255.255.255.0",
    "10.0.0.1 255.0.0.0",
    "172.16.5.10 255.255.0.0",

    # alternative separators
    "192.168.1.50-24",
    "192.168.1.50:24",
    "10.0.0.1-255.0.0.0",

    # edge cases
    "0.0.0.0/0",
    "255.255.255.255/32",
    "10.0.0.0/31",       # no usable hosts
    "10.0.0.0/32",       # single address
]

# ============================================================
#                     MAIN EXECUTION
# ============================================================

def run_subnet_checks(test_cases=None, single_input: str | None = None) -> None:
    """
    Run subnet summary + detailed explanation for:
      - All entries in test_cases (if any),
      - Then for single_input (if provided).

    test_cases:
      - list of strings like "192.168.1.10/24", or
      - None (will be treated as empty).
    """
    if test_cases is None:
        test_cases = []

    test_number = 1

    # Run list of test cases (if any)
    if test_cases:
        print(f"{C.OKBLUE}{C.BOLD}Running Subnet Test Suite (list)...{C.ENDC}")
        for case in test_cases:
            try:
                net = parse_network(case)
                info = describe_subnet(net)
                print_subnet_info(info, label=f"TEST #{test_number}   INPUT='{case}'")

                # Detailed explanation for each test
                explain_input_subnet(case)

            except Exception as e:
                print(f"{C.FAIL}{C.BOLD}TEST #{test_number} ERROR:{C.ENDC} {e}")

            test_number += 1
    else:
        print(f"{C.WARNING}{C.BOLD}Test case list is empty, skipping list run.{C.ENDC}")

    # Run single input (if provided)
    if single_input:
        print(f"\n{C.OKBLUE}{C.BOLD}Running Single IP/Subnet Input...{C.ENDC}")
        try:
            net = parse_network(single_input)
            info = describe_subnet(net)
            print_subnet_info(info, label=f"SINGLE INPUT='{single_input}'")

            explain_input_subnet(single_input)

        except Exception as e:
            print(f"{C.FAIL}{C.BOLD}SINGLE INPUT ERROR:{C.ENDC} {e}")
    else:
        print(f"{C.WARNING}{C.BOLD}No single IP/subnet input provided, skipping single run.{C.ENDC}")

if __name__ == "__main__":
    # Safely get TEST_CASES if defined; otherwise treat as None/empty.
    test_cases = globals().get("TEST_CASES", None)

    # --- TOGGLES ---
    USE_TEST_LIST   = False   # set to False to ignore TEST_CASES even if defined
    USE_SINGLE_IP   = True   # set to False to skip the single IP run


    # Option 2: ask the user interactively instead of hard-coding
    # single_input_str = input(
    #     f"{C.OKBLUE}{C.BOLD}Enter a single IP/mask "
    #     f"(e.g. 192.168.1.10/24 or 192.168.1.10 255.255.255.0), "
    #     f"or press Enter to skip: {C.ENDC}"
    # ).strip() or None

    # Decide what to actually pass into run_subnet_checks
    effective_test_cases = test_cases if USE_TEST_LIST else None
    effective_single     = single_input_str if USE_SINGLE_IP else None

    run_subnet_checks(effective_test_cases, effective_single)