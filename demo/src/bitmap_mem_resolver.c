/* Query in memory bitmap resolver.
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "bitmap.h"

#define __is_resolver
#include "resolver.h"

#ifndef PROGMEM
# define PROGMEM
#endif


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

    bs_start = 0;
    bs_end = NUM_RANGES - 1;
    j = 0;
    while (bs_start <= bs_end) {
        int i = (bs_start + bs_end) / 2;
        if (ranges[i].start <= target && target <= ranges[i].end) {
            bit_off_base = ranges[i].bit_off_base + (target - ranges[i].start) * BITMAP_NUM_BITS;
            for (uint32_t k = 0; k < BITMAP_NUM_BITS; k++) {
                bit_off = bit_off_base + k;
                if (bitmaps[bit_off >> 3] & (1 << (bit_off & 7))) {
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