from difflib import SequenceMatcher

def compute_edits(c1, c2):
    """Compute the edit operations to transform c1 into c2"""
    matcher = SequenceMatcher(None, c1, c2)
    edits = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            edits.append(("replace", i1, i2, c2[j1:j2]))  # Replace c1[i1:i2] with c2[j1:j2]
        elif tag == "delete":
            edits.append(("delete", i1, i2))  # Remove c1[i1:i2]
        elif tag == "insert":
            edits.append(("insert", i1, c2[j1:j2]))  # Insert c2[j1:j2] at i1
    
    return edits

def apply_edits(c1, edits):
    """Apply a list of edit operations to c1."""
    result = list(c1)  # Convert string to list for mutability
    for edit in reversed(edits):  # Process edits in reverse order to avoid index shifting
        if edit[0] == "replace":
            i1, i2, replacement = edit[1], edit[2], edit[3]
            result[i1:i2] = list(replacement)
        elif edit[0] == "delete":
            i1, i2 = edit[1], edit[2]
            del result[i1:i2]
        elif edit[0] == "insert":
            i1, insertion = edit[1], edit[2]
            result[i1:i1] = list(insertion)
        # Print the string after each edit
        print(f"After {edit[0]} edit: {''.join(result)}")
    return ''.join(result)  # Convert list back to string


c1 = '{"foo": "bar"}'
c2 = '{ "baz": 7, "zip": 1.0, "zop": [1, 2]'

edits = compute_edits(c1, c2)
print("Edit operations to transform c1 into c2:")
for edit in edits:
    print(edit)

print("\nApplying edits:")
result = apply_edits(c1, edits)
print("\nFinal result after applying all edits:")
print(result)