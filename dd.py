
def dd1(c_fail, test_function, n):
    """
    A toy implementation of delta debugging. In this case we only keep track of the failing input,
    since there is another implementation that keeps track of a passing input and failing input.
    
    :c_fail: The failing input that is to be minimized
    :test_function: The testing function that returns True if input fails, False otherwise
    :n: The granularity of the deltas in consideration
    """
    length = len(c_fail)
    subset_size = length // n
    subsets = [c_fail[i * subset_size : (i + 1) * subset_size] for i in range(n)]

    for subset in subsets:
        if test_function(subset):
            return dd1(subset, test_function, 2)

    complements = [c_fail[:i * subset_size] + c_fail[(i + 1) * subset_size:] for i in range(n)]
    for complement in complements:
        if test_function(complement):
            return dd1(complement, test_function, max(n-1,2))

    if n < length:
        return dd1(c_fail, test_function, min(2 * n, length))

    return c_fail

def dd2(c_pass, c_fail, test_function, n):
    """
    Yet another toy implementation of delta debugging. In this case we keep track of both
    a c_pass input as well as a c_fail input.

    :c_pass: The passing input which should be a subset of `c_fail'
    :c_fail: The failing input that should be minimized
    :test_function: The test function that return True if input fails, False otherwise
    :n: The granularity of the deltas in consideration
    """
    delta_space = [c for i, c in enumerate(c_fail) if i >= len(c_pass) or c_pass[i] != c]
    length = len(delta_space)
    delta_size = length // n
    deltas = [c_fail[i * delta_size : (i + 1) * delta_size] for i in range(n)]
    
    for 
    


def test(input_str):
    """
    A function that fails it has the string 'test' within it
    """
    return 'test' in input_str

failing_input_1 = "thisistestinputerrorthatshouldfail"
failing_input_2 = "thisistestinputerrortestthatshouldfail"


print(dd1(failing_input_1, test, 2))
print(dd1(failing_input_2, test, 2))
