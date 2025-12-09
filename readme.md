# Subnet Explainer – Quick README

## What This Script Does

This script takes an IPv4 address with a subnet (e.g. `192.0.2.10/27`) and: solves it 

- Parses the input (CIDR or dotted mask).
- Calculates:
  - Network address  
  - CIDR and netmask  
  - First host and last host  
  - Broadcast address  
  - Next subnet  
  - Total and usable addresses
- Prints a **colored summary** of the subnet.
- Prints a **detailed binary explanation**:
  - Shows BASE and SUBMASK in binary.
  - Highlights the *transition byte* (partial mask octet, if any).
  - Shows IP AND netmask byte-by-byte.
  - Explains how first host, last host, broadcast, and next subnet are derived.

The script is **mainly intended for a single, hard‑coded input**, e.g.:

```python
single_input_str = "192.0.2.10/27"
```

placed at the top of the file.

---

## Input Options

### 1. Main (hard-coded) single input

At the top of the script, you’ll see:

```python
single_input_str = "192.0.2.10/27"
```

You can change this string to any of the following formats:

- CIDR:

  ```text
  192.168.1.10/24
  10.0.0.1/8
  ```

- IP + dotted netmask:

  ```text
  192.168.1.10 255.255.255.0
  10.0.0.1 255.0.0.0
  ```

- Alternative separators:

  ```text
  192.168.1.50-24
  192.168.1.50:24
  10.0.0.1-255.0.0.0
  ```

These all get normalized and parsed by the script.

### 2. Optional test list (if you keep it)

If you keep a `TEST_CASES` list in the script, you can run multiple predefined examples.  
You can also comment it out to skip them and only use the hard-coded `single_input_str`.

Example:

```python
TEST_CASES = [
    "59.89.212.216/14",
    "192.168.1.10/24",
    "10.0.0.1 255.0.0.0",
]
```

The runner function can be configured to:

- Run only `TEST_CASES`
- Run only `single_input_str`
- Or run both (list first, then the single input)

depending on how you call `run_subnet_checks(...)` in `if __name__ == "__main__":`.

---

## How to Use

1. **Edit the hard-coded input** at the top:

   ```python
   single_input_str = "192.0.2.10/27"
   ```

2. (Optional) Define `TEST_CASES` if you want to test multiple subnets.

3. At the bottom, in the main section, call the runner with what you want to use, for example:

   ```python
   if __name__ == "__main__":
       test_cases = globals().get("TEST_CASES", None)
       run_subnet_checks(test_cases, single_input_str)
   ```

   - To run only the single input, you can do:

     ```python
     run_subnet_checks(None, single_input_str)
     ```

   - To run only the list:

     ```python
     run_subnet_checks(test_cases, None)
     ```

4. Run the script:

   ```bash
   python ip_script.py
   ```

You’ll see:

- A colored summary.
- A detailed explanation for each subnet processed.

---

## Error Handling

The script validates input and raises or prints clear error messages for:

- **Bad format** (not `IP/CIDR` or `IP MASK`):

  - Example: `"abcd"` or missing mask/prefix.

- **Invalid IP addresses**:

  - If the IP part is not a valid IPv4 address.

- **Invalid subnet masks**:

  - If the mask part is not a valid IPv4 dotted netmask.

- **Out-of-range CIDR prefixes**:

  - If the prefix is not between `0` and `32`.

- **Non-contiguous netmasks**:

  - Example: `255.0.255.0` → “Mask is not contiguous.”

In the main runner, any exception while processing a test or single input is caught and printed in **red** with a short description, so the script doesn’t crash the whole run when one input is bad.