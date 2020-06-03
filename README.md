# mirQAt - Medical Imaging Research QA Toolkit

The original method implemented here was developed by Riqiang Gao and other members of the MASI lab and is available [here](https://github.com/MASILab/QA_tool). I would encourage users to use that tool as it is much more comprehensive. This package contains only a subset of methods that I used for my own QA-ing tasks. This package contains only these tools, with some modifications (fewer dependencies, list comprehension when possible, `pathlib.Path` instead of `os`, etc.) to be more lean and user-friendly command-line interface.

# Image File Structure

I had used the following file structure, but I tried to modify the code to be more file structure agnostic. Please let me know if you have any issues or submit a PR to improve upon the current implementation.

File structure used:

```
. (root)
├── 123456789 (subject_ID)
│   ├── 5555555 (accession_number)
│   │   ├── 2 (instance)
│   │   │   ├── 1234.dcm
│   │   │   ├── 1235.dcm
│   │   │   ├── 1236.dcm
│   │   ├── 3 (another instance)
```

# Checks

## Instance number check

`dcm-instance`

## Slice distance check

`dcm-slicedistance`

## Generate QA report and Check instance number

`instancen-fold`

## Filter sessions with few slices but that pass the instance number check

`filter-few-slices`
