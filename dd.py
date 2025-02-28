
def dd1(failing_input, test_function, n):
    """
    A toy implementation of delta debugging. In this case we only keep track of the failing input,
    since there is another implementation that keeps track of a passing input and failing input.
    
    :failing_input: The failing input that is to be minimized
    :test_function: The testing function that returns True if input fails, False otherwise
    :n: The granularity of the deltas in consideration
    """
    length = len(failing_input)
    subset_size = length // n
    subsets = [failing_input[i * subset_size : (i + 1) * subset_size] for i in range(n)]

    for subset in subsets:
        if test_function(subset):
            return dd1(subset, test_function, 2)

    complements = [failing_input[:i * subset_size] + failing_input[(i + 1) * subset_size:] for i in range(n)]
    for complement in complements:
        if test_function(complement):
            return dd1(complement, test_function, max(n-1,2))

    if n < length:
        return dd1(failing_input, test_function, min(2 * n, length))

    return failing_input


def test(input_str):
    """
    A function that fails it has the string 'test' within it
    """
    return 'test' in input_str

failing_input_1 = "thisistestinputerrorthatshouldfail"
failing_input_2 = "thisistestinputerrortestthatshouldfail"


print(dd1(failing_input_1, test, 2))
print(dd1(failing_input_2, test, 2))
