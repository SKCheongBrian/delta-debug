from difflib import ndiff
import json

def dddiff(c1, c2, n):
    ''' general delta debugging algorithm '''
    run = 1
    cbar_offset = 0

    # c1_orig = c1
    # c2_orig = c2

    # replace tail recursion with iteration
    while 1:
        print ("dd: c1 =", c1)
        print ("dd: c2 =", c2)

        t1 = test(c1) # PASS
        t2 = test(c2) # FAIL

        assert t1 == 1, "c1 should be valid"
        assert t2 == 0, "c2 should be invalid"

        edits = compute_edits(c1, c2)

        print("dd: edits =", edits)

        if n > len(edits):
            print("dd: done")
            return (c1, c2, edits)
        
        cs = split(edits, n)
        print("dd: cs =", cs)

        print("dd run #", run, ": trying")
        for i in range(n):
            if i > 0:
                print("+")
            print(len(cs[i]))
        
        progress = 0
        next_c1 = c1[:]
        next_c2 = c2[:]
        next_n = n
        
        # Check subsets
        for j in range(n):
            i = (j + cbar_offset) % n
            print("dd: trying", cs[i])
            
            


def split(c, n):
    """Split c into n chunks"""
    # k, m = divmod(len(c), n)
    # return (c[i * k + min(i, m): (i + 1) * k + min(i+1, m)] for i in range(n))
    chunks = []
    start = 0
    chunk_size = len(c) // n
    remainder = len(c) % n
    for i in range(n):
        end = start + chunk_size + (1 if i >= n - remainder else 0)
        if start < len(c): 
            chunks.append(c[start:end])
        start = end
    return chunks




# def test(c):
    # candidate = "".join(c)
    # print("Testing candidate:", candidate)

    # # Treat empty candidate as valid
    # if candidate.strip() == "":
    #     print("Candidate is empty, skipping.")
    #     return True
    # try:
    #     json.loads(candidate)
    #     return True
    # except json.JSONDecodeError:
    #     return False
    # Reassemble configuration into candidate string.

# Returns 1 if pass, 0 fail, 2 otherwise
def test(c):
    candidate = "".join(c)
    print("Testing candidate:", candidate)
    # Treat an empty candidate as passing.
    if candidate.strip() == "":
        return 1
    try:
        json.loads(candidate)
        return 1
    except json.JSONDecodeError as e:
        error_message = str(e)
        error_pos = e.pos
        print("Error at position", error_pos, ":", error_message)
        if "Expecting ',' delimiter" in error_message or "Expecting property name enclosed in double quotes" in error_message:
            print("------------------------------")
            return 0
        return 2


def compute_edits(c1, c2):
    """Compute fine-grained edit operations to transform c1 into c2"""
    diff = list(ndiff(c1, c2))
    edits = []
    current_index = 0  # Pointer for the current position in c1
    for d in diff:
        if d.startswith('-'):  # Deletion
            edits.append(("delete", current_index))
        elif d.startswith('+'):  # Insertion
            edits.append(("insert", current_index, d[2:]))
            current_index += 1  # Increment index for the insertion
        elif d.startswith(' '):  # No change
            current_index += 1
    return edits

def apply_edits(c1, edits):
    """Apply a list of fine-grained edit operations to c1."""
    current_string = list(c1)  # Convert string to list for mutability
    for edit in edits:  # Process edits sequentially
        if edit[0] == "delete":
            i1 = edit[1]
            del current_string[i1]
        elif edit[0] == "insert":
            i1, insertion = edit[1], edit[2]
            current_string[i1:i1] = list(insertion)
        # Print the string after each edit
        print(f"After {edit[0]} edit: {''.join(current_string)}")
    return ''.join(current_string)  # Convert list back to string


c1 = '{"foo": "bar"}'
c2 = '{ "baz": 7, "zip": 1.0, "zop": [1, 2]'

edits = compute_edits(c1, c2)
print("Fine-grained edit operations to transform c1 into c2:")
for edit in edits:
    print(edit)

print("\nApplying edits:")
result = apply_edits(c1, edits)
print("\nFinal result after applying all edits:")
print(result)

print("\nTesting candidates:")
c1_result = test(c1)
print("Test result for c1:", c1_result)
c2_result = test(c2)
print("Test result for c2:", c2_result)

dddiff(c1, c2, 2)
