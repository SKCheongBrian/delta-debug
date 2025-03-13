import difflib

class Config:
    def __init__(self, c_pass, c_fail):
        self.c_pass = c_pass
        self.c_fail = c_fail
        # Recompute diffs each time we create a new config.
        self.diffs = self.compute_diffs()
    
    def compute_diffs(self):
        matcher = difflib.SequenceMatcher(None, self.c_pass, self.c_fail)
        diffs = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                diffs.append((self.c_fail[j1:j2], j1, j2))
        return diffs

def overall_delta(diffs):
    return "".join(text for (text, _, _) in diffs)

def map_pos(c_pass, c_fail, pos):
    matcher = difflib.SequenceMatcher(None, c_pass, c_fail)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if pos < j2:
            if tag == "equal":
                return i1 + (pos - j1)
            else:
                return i1
    return len(c_pass)

def partition_overall(config, granularity):
    """
    Partition the overall delta—that is, for each diff in config.diffs
    produce one or more chunks. Chunks are never merged across diff boundaries.
    
    For each diff tuple (diff_text, start, end):
      - If len(diff_text) <= granularity, leave it as one chunk.
      - Otherwise, partition it into granularity many (roughly equal) chunks.
    Return a list of chunks: each chunk is (chunk_text, abs_start, abs_end)
    """
    chunks = []
    for diff in config.diffs:
        diff_text, start, end = diff
        L = len(diff_text)
        if L <= granularity:
            chunks.append((diff_text, start, end))
        else:
            # Partition this diff into granularity many parts (each within this diff).
            chunk_size = L // granularity
            offset = 0
            for i in range(granularity):
                if i < granularity - 1:
                    part_text = diff_text[offset: offset + chunk_size]
                    part_start = start + offset
                    part_end = part_start + len(part_text)
                    chunks.append((part_text, part_start, part_end))
                    offset += chunk_size
                else:
                    part_text = diff_text[offset:]
                    part_start = start + offset
                    part_end = end
                    chunks.append((part_text, part_start, part_end))
    return chunks

def union_config_part(c_pass, diff_part, c_fail):
    part_text, part_start, _ = diff_part
    ins_pos = map_pos(c_pass, c_fail, part_start)
    return c_pass[:ins_pos] + part_text + c_pass[ins_pos:]

def subtract_config_part(c_fail, diff_part):
    _, start, end = diff_part
    return c_fail[:start] + c_fail[end:]

def test(input_str):
    return 'test' in input_str

def dd2(config, granularity):
    # Always update diffs from the current configuration
    config.diffs = config.compute_diffs()
    delta = overall_delta(config.diffs)
    
    if len(delta) <= 1:
        print("Found minimal difference of size", len(delta))
        return config
    
    # Partition the overall delta (while preserving diff boundaries)
    overall_chunks = partition_overall(config, granularity)
    
    print(f"dd2 called: c_pass='{config.c_pass}', c_fail='{config.c_fail}', delta='{delta}', granularity={granularity}")
    print(f"Overall chunks: {[chunk[0] for chunk in overall_chunks]}")
    
    # Process each overall chunk for the four conditions.
    for chunk in overall_chunks:
        # Condition 1: If union of c_pass with this chunk yields failure.
        candidate = union_config_part(config.c_pass, chunk, config.c_fail)
        if test(candidate):
            print(f"Condition 1 triggered: union with chunk '{chunk[0]}' fails")
            new_config = Config(config.c_pass, candidate)
            return dd2(new_config, 2)
    
    for chunk in overall_chunks:
        # Condition 2: If subtraction of this chunk from c_fail yields pass.
        candidate = subtract_config_part(config.c_fail, chunk)
        if not test(candidate):
            print(f"Condition 2 triggered: subtraction of chunk '{chunk[0]}' yields pass")
            new_config = Config(candidate, config.c_fail)
            return dd2(new_config, 2)
    
    for chunk in overall_chunks:
        # Condition 3: If union with chunk yields pass.
        candidate = union_config_part(config.c_pass, chunk, config.c_fail)
        if not test(candidate):
            print(f"Condition 3 triggered: union with chunk '{chunk[0]}' yields pass")
            new_config = Config(candidate, config.c_fail)
            return dd2(new_config, max(granularity - 1, 2))
    
    for chunk in overall_chunks:
        # Condition 4: If subtraction with chunk yields failure.
        candidate = subtract_config_part(config.c_fail, chunk)
        if test(candidate):
            print(f"Condition 4 triggered: subtraction of chunk '{chunk[0]}' yields fail")
            new_config = Config(config.c_pass, candidate)
            return dd2(new_config, max(granularity - 1, 2))
    
    # Condition 5: Increase granularity if the overall delta is larger than current granularity.
    if granularity < len(delta):
        new_granularity = min(2 * granularity, len(delta))
        print(f"Condition 5: increasing overall granularity from {granularity} to {new_granularity}")
        return dd2(config, new_granularity)
    
    print("Condition 6: no further reduction possible")
    return config

def delta_debug(c_pass, c_fail, n=2):
    assert not test(c_pass), "c_pass must pass"
    assert test(c_fail), "c_fail must fail"
    initial_config = Config(c_pass, c_fail)
    return dd2(initial_config, n)

if __name__ == "__main__":
    passing_input = "thisisinputthatshouldpass"
    failing_input = "thisistestinputerrorthatshouldfail"
    print("Minimal Failure-Inducing Difference:")
    final_config = delta_debug(passing_input, failing_input)
    print("Result:")
    print("c_fail =", final_config.c_fail)
    print("c_pass =", final_config.c_pass)