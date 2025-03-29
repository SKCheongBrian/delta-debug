from difflib import ndiff

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