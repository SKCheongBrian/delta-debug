# Delta Debugging for Humans

- [Delta Debugging for Humans](#delta-debugging-for-humans)
  - [What is this?](#what-is-this)
  - [How is this achieved](#how-is-this-achieved)
  - [Algorithm of ddmax](#algorithm-of-ddmax)
  - [Running showcases](#running-showcases)
    - [Batch running showcases](#batch-running-showcases)
    - [Running individual showcases](#running-individual-showcases)
  - [Future works](#future-works)
- [References](#references)


## What is this?

This is an implementation of a modified version of delta debugging

The main idea is that instead of returning the minimum failing test case,
it is better for developers to receive a failing test case that has a minimal
difference from passing test cases.

## How is this achieved
In our modified implementation of Zeller's original delta debugging work [1], [2], [3], 
we achieve this in a 2-step process:

1. **Delta Debugging (dd)**:
   - Minimize the failing test case to isolate the smallest configuration
   that still fails.

1. **Maximal Expansion (ddmax)**:
   - Expand the minimized failing test case by adding elements from the 
   passing test case, ensuring it remains failing, until no further expansion 
   is possible.

The result is a **maximal failing test case** that is as close as possible to 
the passing test case. This test case is more readable for programmers and 
allows them to better discover the root cause of the test failure.

## Algorithm of ddmax

1. **Input**:
   - A failing test case (`c1`) and a passing test case (`c2`).
   - A granularity level (`n`) that determines how the difference 
   between `c1` and `c2` is split.

2. **Initialization**:
   - Compute the difference (`c`) between `c2` and `c1`.
   - Ensure that `c1` is a subset of `c2` and that `c1` fails while `c2` passes.

3. **Iterative Expansion**:
   - Split the difference (`c`) into `n` subsets.
   - For each subset, attempt to add it to `c1` and test the resulting configuration:
     - If the expanded configuration still fails, keep the subset and update `c1`.
     - If it passes, discard the subset.
   - Adjust the granularity (`n`) dynamically based on progress.

4. **Termination**:
   - Stop when no further subsets can be added to `c1` without causing it to pass, 
   or when the granularity exceeds the size of `c`.

5. **Output**:
   - Return the maximal failing test case (`c1`), the remaining difference (`c`), 
   and the original passing test case (`c2`).

This algorithm ensures that the failing test case is expanded as much as possible
while remaining within the boundaries of the passing test case.

---
## Running showcases
The files in this repository marked as `showcase*.py` (* being a number) can be run using the following instructions. Each file contains few test examples to show how our dd algorithm (in `humandeltadebug.py`) works. The descriptions of each showcase are in their respective files. 

### Batch running showcases
You can run all the showcases at once using the provided scripts:

**On Unix/macOS (with `sh`)**:

```shell
./runshowcases.sh
```
**On Windows:**

```shell
.\runshowcases.bat
```

This will execute all `showcase*.py` files in the directory and store their outputs in a folder called `showcase_output` as `showcase*.out` files. 

If you wish to see a more verbose output, albeit hard to interpret, add the `--verbose` flag

**On Unix/macOS (with `sh`)**:

```shell
./runshowcases.sh --verbose
```

**On Windows:**

```shell
.\runshowcases.bat --verbose
```
This would create `verbose-showcase*.out` in `showcase_output` which contain the verbose output of running the showcases.

### Running individual showcases

To run individual showcases, you may run the commands (`python` or `python3` based on the way the command is configured on your system)
```shell
python3 showcase1.py
```
```shell
python3 showcase2.py
```
```shell
python3 showcase3.py
```
This, for example would run the first showcase, second showcase, and third showcase respectfully.

In order to view the verbose output, simply add the `--verbose` flag to the end of the command

For example,
```shell
python3 showcase1.py --verbose
```

## Future works
- Explore using other minimisation/maximisation metrics, for example edit distance or hamming distance.
- Explore minimising the passing test case, as opposed to our current approach of maximising the failing test case.

# References
[1] A. Zeller and R. Hildebrandt, "Simplifying and isolating failure-inducing input," in IEEE Transactions on Software Engineering, vol. 28, no. 2, pp. 183-200, Feb. 2002, doi: 10.1109/32.988498

[2] A. Zeller, Original DD.py implementation, https://www.st.cs.uni-saarland.de/dd/DD.py

[3] grimm-co, “GitHub - grimm-co/delta-debugging: Debugging library to quickly get the minimal crashing test case,” GitHub, 2016. https://github.com/grimm-co/delta-debugging
‌
‌

