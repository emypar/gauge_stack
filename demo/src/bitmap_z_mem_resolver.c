/* Query in memory zlib compressed bitamp resolver.
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "bitmap_z.h"

#include "zlib.h"

#include "resolver.h"

#ifndef PROGMEM
# define PROGMEM
#endif


#define  BITMAP_NUM_BYTES ((BITMAP_NUM_BITS + 7) >> 3)

/*
The size of the bitmap read buffer, it should be greater than BITMAP_NUM_BYTES,
preferably a couple of K, R/W memory permitting. 
*/
#ifndef BITMAP_BUF_SZ
# define BITMAP_BUF_SZ 1 * 1024
#endif


char* expand_z_err(int z_err) {
    switch (z_err) {
        case Z_OK: return "Z_OK";
        case Z_STREAM_END: return "Z_STREAM_END";
        case Z_NEED_DICT: return "Z_NEED_DICT";
        case Z_ERRNO: return "Z_ERRNO";
        case Z_STREAM_ERROR: return "Z_STREAM_ERROR";
        case Z_DATA_ERROR: return "Z_DATA_ERROR";
        case Z_MEM_ERROR: return "Z_MEM_ERROR";
        case Z_BUF_ERROR: return "Z_BUF_ERROR";
        case Z_VERSION_ERROR: return "Z_VERSION_ERROR";
    }
    return "Z_UNKNOWN_ERROR";   
}

int get_z_bitmap(uint32_t bit_off_base, uint8_t* buf, size_t buf_sz) {
    uint32_t skip_bytes_sz = bit_off_base >> 3;
    int z_ret, z_ret1;

    z_stream z_stream = {
        .next_in = (Bytef*)bitmaps_z,
        .avail_in = sizeof(bitmaps_z),
        .zalloc = Z_NULL,
        .zfree = Z_NULL
    };

    z_ret = inflateInit(&z_stream);
    while (skip_bytes_sz > 0 && z_ret == Z_OK) {
        uint32_t to_read = skip_bytes_sz;
        if (to_read > buf_sz) {
            to_read = buf_sz;
        }
        z_stream.next_out = (Bytef*)buf;
        z_stream.avail_out = to_read;
        z_ret = inflate(&z_stream, Z_NO_FLUSH);
        if (z_ret == Z_OK) {
            skip_bytes_sz -= to_read;
        }
    }
    if (z_ret == Z_OK) {
        z_stream.next_out = (Bytef*)buf;
        z_stream.avail_out = BITMAP_NUM_BITS;
        z_ret = inflate(&z_stream, Z_SYNC_FLUSH);
    }
    z_ret1 = inflateEnd(&z_stream);
    return z_ret != Z_OK ? z_ret : z_ret1;
}

static const struct resolver _resolver PROGMEM = {
    .min_target = MIN_TARGET,
    .max_target = MAX_TARGET,
    .labels = labels,
    .num_labels = sizeof(labels) / sizeof(char*),
    ._resolver_internal = NULL,

};

/* The resolver interface (see resolver.h)s:
*/
const char* resolver_args = NULL;

const struct resolver* init_resolver(int argc, char** argv) {
    return &_resolver;
}

int resolve(const struct resolver* resolver, uint32_t target, const char* blocks[]) {
    int j, z_ret, bs_start, bs_end;
    uint32_t bit_off_base, bit_off;
    uint8_t buf[BITMAP_BUF_SZ];

    bs_start = 0;
    bs_end = NUM_RANGES - 1;
    j = 0;
    while (bs_start <= bs_end) {
        int i = (bs_start + bs_end) / 2;
        if (ranges[i].start <= target && target <= ranges[i].end) {
            bit_off_base = ranges[i].bit_off_base + (target - ranges[i].start) * BITMAP_NUM_BITS;
            z_ret = get_z_bitmap(bit_off_base, buf, sizeof(buf));
            if (z_ret < 0) {
                fprintf(stderr, "%u: zlib error: %d (%s)\n", target, z_ret, expand_z_err(z_ret));
                return -1;
            }
            bit_off_base &= 7; /* Since already on the byte */
            for (uint32_t k = 0; k < BITMAP_NUM_BITS; k++) {
                bit_off = bit_off_base + k;
                if (buf[bit_off >> 3] & (1 << (bit_off & 7))) {
                    blocks[j++] =  labels[k];
                }
            }
            break;
        } else if (target < ranges[i].start) {
            bs_end = i - 1;
        } else {
            bs_start = i + 1;
        }
    }
    if (j < resolver->num_labels) {
        /* Not all blocks are being used, mark the early end */
        blocks[j] = NULL;
    }

    return 0;
}