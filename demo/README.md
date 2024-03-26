# C Sample Code For Lookup Based Resolvers

## General Info

These resolvers use the data derived from `../best.pkl` to lookup the resolution for a given target.


## Build Instructions

Pre-requisites: gcc and libz

    cd demo
    make

## Resolvers

### bitmap_file_resolver

This resolver is blockset agnostic and it will use the data from `data/blockset_81.bmp` bitmap file and [data/blockset_81.meta](data/blockset_81.meta) metadata file.

    bin/bitmap_file_resolver \
        data/blockset_81.bmp \
        data/blockset_81.meta

`bitmap_file_resolver` has the smallest memory footprint, it is reasonably fast but it requires external storage.

### bitmap_mem_resolver

This resolver was compiled with the blockset information and resolution from the [include/blockset_81/bitmap.h](include/blockset_81/bitmap.h)

    bin/blockset_81/bitmap_mem_resolver

`bitmap_mem_resolver` has the largest memory footprint (~2.8 MiB), it doesn't require storage at all and it is the fastest.

### bitmap_z_mem_resolver

This resolver was compiled with the blockset information and resolution from the [include/blockset_81/bitmap_z.h](include/blockset_81/bitmap_z.h), It is similar to `bitmap_mem_resolver` but the in-memory bitmap has been zlib compressed.

    bin/blockset_81/bitmap_z_mem_resolver

`bitmap_z_mem_resolver` has a smaller memory footprint (~ 0.6MiB), it doesn't require storage at all, but it is the slowest, especially for large targets since the compressed information has to fully uncompressed to reach the desired offset.

## Validation

Each resolver accepts `-t` flag to auto-resolve the entire range of targets and to display the resolution in JSON format.

[tools/validate_resolution.py](tools/validate_resolution.py) can then be used to compare the desired resolution from `../best.pkl` against the actual one from .json files.

    mkdir .work
 
    bin/bitmap_file_resolver -t \
        data/blockset_81.bmp \
        data/blockset_81.meta  \
        > .work/bitmap_file_resolver.json
    tools/validate_resolution.py \
        ../best.pkl \
        .work/bitmap_file_resolver.json

    
    bin/blockset_81/bitmap_mem_resolver -t \
        > .work/bitmap_mem_resolver.json
    tools/validate_resolution.py \
        ../best.pkl \
        .work/bitmap_mem_resolver.json

    
    bin/blockset_81/bitmap_z_mem_resolver -t \
        > .work/bitmap_z_mem_resolver.json
    tools/validate_resolution.py \
        ../best.pkl \
        .work/bitmap_z_mem_resolver.json


