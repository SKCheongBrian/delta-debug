import difflib

def compute_diff(c_pass, c_fail):
    """
    Compute a diff string from c_fail that contains the parts differing from c_pass.
    """
    matcher = difflib.SequenceMatcher(None, c_pass, c_fail)
    diff_parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            diff_parts.append(c_fail[j1:j2])
    return "".join(diff_parts)

def test(input_str):
    """
    A function that fails if the string contains 'test'.
    """
    return 'test' in input_str

def dd2(c_pass, c_fail, n):
    """
    Delta debugging function following the revised algorithm.
    
    Invariant: test(c_pass)==pass (False) and test(c_fail)==fail (True).
    Let delta = c_fail - c_pass (as computed by compute_diff) and partition it
    into n disjoint chunks (parts) of equal size.
    
    Then perform:
      1. If ∃ part in parts: test(c_pass ∪ part) = fail, then:
            return dd2(c_pass, c_pass ∪ part, 2)
      2. If ∃ part in parts: test(c_fail - part) = pass, then:
            return dd2(c_fail - part, c_fail, 2)
      3. If ∃ part in parts: test(c_pass ∪ part) = pass, then:
            return dd2(c_pass ∪ part, c_fail, max(n-1,2))
      4. If ∃ part in parts: test(c_fail - part) = fail, then:
            return dd2(c_pass, c_fail - part, max(n-1,2))
      5. If n < |delta|, increase granularity:
            return dd2(c_pass, c_fail, min(2*n, len(delta)))
      6. Otherwise, return (c_fail, c_pass) as a 1-minimal difference.
    """
    delta = compute_diff(c_pass, c_fail)
    # Base case: if delta is a single change, assume it’s minimal.
    if len(delta) <= 1:
        print("Found minimal difference of size", len(delta))
        return (c_fail, c_pass)

    # Partition delta (as in dd1 style)
    n = min(n, len(delta))
    subset_size = len(delta) // n
    parts = [delta[i*subset_size:(i+1)*subset_size] for i in range(n-1)]
    parts.append(delta[(n-1)*subset_size:])  # include remainder in last chunk

    print(f"dd2 called: c_pass='{c_pass}', c_fail='{c_fail}', delta='{delta}', n={n}, parts={parts}")

    # Condition 1: ∃ i: test(c_pass ∪ δᵢ) = fail.
    for part in parts:
        if test(c_pass + part):
            print(f"Condition 1 triggered: union with '{part}' fails")
            return dd2(c_pass, c_pass + part, 2)

    # Condition 2: ∃ i: test(c_fail - δᵢ) = pass.
    for part in parts:
        # Removal: remove the first occurrence of part from delta.
        candidate_delta = delta.replace(part, "", 1)
        candidate = c_pass + candidate_delta
        if not test(candidate):
            print(f"Condition 2 triggered: removal of '{part}' passes")
            # Adjust c_fail by removing this part.
            new_c_fail = c_fail.replace(part, "", 1)
            return dd2(new_c_fail, c_fail, 2)

    # Condition 3: ∃ i: test(c_pass ∪ δᵢ) = pass.
    for part in parts:
        if not test(c_pass + part):
            print(f"Condition 3 triggered: union with '{part}' passes")
            return dd2(c_pass + part, c_fail, max(n-1,2))

    # Condition 4: ∃ i: test(c_fail - δᵢ) = fail.
    for part in parts:
        candidate_delta = delta.replace(part, "", 1)
        candidate = c_pass + candidate_delta
        if test(candidate):
            print(f"Condition 4 triggered: removal of '{part}' fails")
            new_c_fail = c_fail.replace(part, "", 1)
            return dd2(c_pass, new_c_fail, max(n-1,2))

    # Condition 5: Increase granularity
    if n < len(delta):
        print("Condition 5 triggered: increasing granularity")
        return dd2(c_pass, c_fail, min(2 * n, len(delta)))

    print("Condition 6 triggered: no further reduction possible")
    return (c_fail, c_pass)

def delta_debug(c_pass, c_fail, n=2):
    """
    Entry point for delta debugging.
    Invariant: test(c_pass)==pass and test(c_fail)==fail.
    """
    assert not test(c_pass), "c_pass must pass the test"
    assert test(c_fail), "c_fail must fail the test"
    return dd2(c_pass, c_fail, n)

if __name__ == "__main__":
    # Use the provided passing input.
    passing_input = "thisisinputthatshouldpass"
    failing_input = "thisistestinputerrorthatshouldfail"
    
    print("Minimal Failure-Inducing Difference:")
    result = delta_debug(passing_input, failing_input)
    print("Result:", result)