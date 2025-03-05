def test(input_str):
    """
    A function that fails if the string contains 'test'.
    """
    return 'test' in input_str

def dd2(c_pass, c_fail, n):
    """
    Revised dd2 implements the Delta Debugging algorithm.
    Assumes:
       c_fail.startswith(c_pass)
       test(c_pass)==False and test(c_fail)==True.
    Let delta = c_fail[len(c_pass):]
    
    The algorithm partitions delta into n equal (or near-equal) parts (δi)
    and applies these conditions:
    
      1. If for all i, test(c_pass ∪ δi) is True,
         then call dd2(c_pass, c_pass ∪ δ₁, 2).
      2. If for all i, test(c_fail − δi) is False,
         then call dd2(c_fail − δ₁, c_fail, 2).
      3. If for all i, test(c_pass ∪ δi) is False,
         then call dd2(c_pass ∪ δ₁, c_fail, max(n-1,2)).
      4. If for all i, test(c_fail − δi) is True,
         then call dd2(c_pass, c_fail − δ₁, max(n-1,2)).
      5. If n < |delta|,
         then increase granularity by calling dd2(c_pass, c_fail, min(2*n, |delta|)).
      6. Otherwise, return delta.
    """
    delta = c_fail[len(c_pass):]
    if len(delta) <= 1:
        print("Found minimal difference of size", len(delta))
        return delta

    n = min(n, len(delta))
    chunk_size = len(delta) // n
    parts = []
    start = 0
    for i in range(n):
        end = start + chunk_size if i < n - 1 else len(delta)
        parts.append(delta[start:end])
        start = end

    print(f"dd2 called: c_pass='{c_pass}', delta='{delta}', n={n}, parts={parts}")

    # Condition 1:
    if all(test(c_pass + part) for part in parts):
        print("Condition 1 triggered: each union (c_pass ∪ δi) fails")
        return dd2(c_pass, c_pass + parts[0], 2)

    # Condition 2:
    # subtraction is defined as removing the first occurrence of a part from delta.
    if all(not test(c_pass + delta.replace(part, "", 1)) for part in parts):
        print("Condition 2 triggered: each subtraction (c_fail − δi) passes")
        new_delta = delta.replace(parts[0], "", 1)
        return dd2(c_pass + new_delta, c_pass + delta, 2)

    # Condition 3:
    if all(not test(c_pass + part) for part in parts):
        print("Condition 3 triggered: each union (c_pass ∪ δi) passes")
        return dd2(c_pass + parts[0], c_fail, max(n-1, 2))

    # Condition 4:
    if all(test(c_pass + delta.replace(part, "", 1)) for part in parts):
        print("Condition 4 triggered: each subtraction (c_fail − δi) fails")
        new_delta = delta.replace(parts[0], "", 1)
        return dd2(c_pass, c_pass + new_delta, max(n-1, 2))

    # Condition 5, Increase granularity.
    if n < len(delta):
        print("Condition 5 triggered: increasing granularity")
        return dd2(c_pass, c_fail, min(2*n, len(delta)))

    print("Condition 6 triggered: no further reduction possible")
    return delta

def delta_debug(c_pass, c_fail, n=2):
    """
    Entry point for delta debugging.
    Assumes:
       c_fail.startswith(c_pass)
       test(c_pass)==False and test(c_fail)==True.
    """
    # Recursion invariant.
    assert not test(c_pass), "c_pass must pass the test"
    assert test(c_fail), "c_fail must fail the test"
    return dd2(c_pass, c_fail, n)

if __name__ == "__main__":
    # Use the provided passing input.
    passing_input = "this"
    failing_input = "thisistestinputerrorthatshouldfail"

    print("Minimal Failure-Inducing Difference:")
    result = delta_debug(passing_input, failing_input)
    print("Result:", result)