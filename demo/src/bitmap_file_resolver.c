/* Resolver for bitmap and metadata files.
*/

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#define __is_resolver
#include "resolver.h"

#ifndef PROGMEM
# define PROGMEM
#endif

struct meta {
    int max_label_sz;
    const char* bitmap_file;
    int bitmap_fd;
    int bitmap_num_bytes;
    uint8_t* bitmap;
};

/* The resolver interface (see resolver.h)s:
*/
const char* resolver_args = "BITMAP_FILE META_FILE";


int load_meta(struct resolver* resolver, const char* meta_file) {
    struct meta* meta = (struct meta*)resolver->_resolver_internal;

    FILE* fh;
    int n;

    fh = fopen(meta_file, "r");
    if (fh == NULL) {
        fprintf(stderr, "open(%s): %d (%s)\n", meta_file, errno, strerror(errno));
        return -1;
    }

    int ret_val = 0;

    n = fscanf(fh, "%d %d %d %d %d", &(resolver->num_labels), &(meta->max_label_sz), \
        &(meta->bitmap_num_bytes), &(resolver->min_target), &(resolver->max_target));
    if (n != 5) {
        fprintf(stderr, \
            "%s: missing some of the NUM_LABELS, MAX_LABEL_SZ, BITMAP_NUM_BYTES, MIN_TARGET, MAX_TARGET\n", \
            meta_file);
        ret_val = -1;
    }

    if (ret_val == 0) {
        for (int c = fgetc(fh); c != '\n' && c != EOF; ) {}
        resolver->labels = malloc(resolver->num_labels * sizeof(char*));
        int buf_sz = meta->max_label_sz + 2;
        char* buf = malloc(buf_sz);
        for (int k = 0; k < resolver->num_labels; k++) {
            int l;
            if (fgets(buf, buf_sz, fh) == NULL) {
                fprintf(stderr, "%s: unexpected EOF after %d labels\n", meta_file, k);
                resolver = NULL;
                break;
            }
            l = strlen(buf);
            if (buf[l-1] != '\n') {
                fprintf(stderr, "%s: Truncated label %s\n", meta_file, buf);
                resolver = NULL;
                break;
            }
            buf[l-1] = 0;
            resolver->labels[k] = strdup(buf);
        }
        free(buf);
    }
    fclose(fh);

    return ret_val;
   
}


const struct resolver* init_resolver(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Missing resolver args: %s\n", resolver_args);
        return NULL;
    }
    const char* bitmap_file = argv[0];
    const char* meta_file = argv[1];

    struct resolver* resolver = malloc(sizeof(struct resolver));
    struct meta* meta = malloc(sizeof(struct meta));
    resolver->_resolver_internal = meta;

    int ret_val = load_meta(resolver, meta_file);
    
    if (ret_val  >= 0) {
       meta->bitmap_fd = open(bitmap_file, O_RDONLY);
        if (meta->bitmap_fd == -1) {
            fprintf(stderr, "open(%s): %d (%s)\n", bitmap_file, errno, strerror(errno));
            ret_val = -1;
        }
    }

    if (ret_val < 0) {
        free(resolver->_resolver_internal);
        free(resolver);
        return NULL;
    }

    meta->bitmap_file = strdup(bitmap_file);
    meta->bitmap = malloc(meta->bitmap_num_bytes);

    return resolver;
}

int resolve(const struct resolver* resolver, uint32_t target, const char* blocks[]) {
    struct meta* meta = (struct meta*)resolver->_resolver_internal;
    off_t off, pos;
    int n;

    off = (target - resolver->min_target) * meta->bitmap_num_bytes;

    if ((pos = lseek(meta->bitmap_fd, off, SEEK_SET)) != off) {
        fprintf(stderr, "seek(%s, %lld, SEEK_SET): %d (%s)\n", meta->bitmap_file, off, errno, strerror(errno));
        return -1;
    }

    uint8_t* bitmap = meta->bitmap;

    if ((n = read(meta->bitmap_fd, bitmap, meta->bitmap_num_bytes)) != meta->bitmap_num_bytes) {
        if (n < 0) {
            fprintf(stderr, "read(%s): %d (%s)\n", meta->bitmap_file, errno, strerror(errno));
            return -1;
        } else {
            fprintf(stderr, "read(%s): unexpected EOF\n", meta->bitmap_file);
            return -1;
        }
    }

    int j = 0;
    for (int k = 0; k < resolver->num_labels; k++) {
        if ((bitmap[k >> 3] & (1 << (k & 7))) > 0) {
            blocks[j++] = resolver->labels[k];

        }
    }
    if (j < resolver->num_labels) {
        /* Not all blocks are being used, mark the early end */
        blocks[j] = NULL;
    }

    return 0;
}

