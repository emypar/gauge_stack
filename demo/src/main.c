/*
Resolver driver, to be linked with a particular resolver.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "resolver.h"

#define LINE_BUF_SZ 256

void help(char* argv0) {
    char* slash = strrchr(argv0, '/'); 
    if (slash != NULL) {
        argv0 = slash + 1;
    }
    fprintf(stderr, "\
Usage: %s -qth RESOLVER_ARGS...\n\
Options:\n\
    -q:\n\
        Quiet, do not print the prompt.\n\
    -t:\n\
        Test, query all targets MIN_TARGET .. MAX_TARGET and print the resolution \n\
        in JSON format:\n\
            {\n\
                \"TARGET\": [\"LABEL\", ...]\n\
            }\n\
    -h:\n\
        This help message.\n\
Resolver args:\n\
        %s\n\
",
        argv0, resolver_args != NULL ? resolver_args: "");
}


void display_blocks(const char* blocks[], int num_labels) {
    uint8_t first_label = 1;
    printf("[");
    for (int k = 0; k < num_labels; k++) {
        if (blocks[k] == NULL) {
            /* Early stop, less than num_labels blocks */
            break;
        }
        if (! first_label) {
            printf(", ");
        } else {
            first_label = 0;
        }
        printf("\"%s\"", blocks[k]);
    }
    printf("]");
}


void generate_test_data(const struct resolver* resolver, const char* blocks[]) {
    printf("{");
    for (uint32_t target = resolver->min_target; target <= resolver->max_target; target++) {
        if (resolve(resolver, target, blocks) < 0) {
            /* Error, message already displayed, cannot continue */
            break;
        }
        if (target > resolver->min_target) {
            /* There was a previous block list, append ',' */
            printf(",");
        }
        printf("\n  \"%u\": ", target);
        display_blocks(blocks, resolver->num_labels);
    }
    printf("\n}\n");
}


int main(int argc, char** argv) {
    int opt, quiet = 0, test=0;

    while ((opt = getopt(argc, argv, "qth")) != -1) {
        switch (opt) {
            case 'q':
                quiet = 1;
                break;
            case 't':
                test = 1;
                break;
            case 'h':
                help(argv[0]);
                exit(1);
        }
    }

    const struct resolver* resolver = init_resolver(argc - optind, argv + optind);
    if (resolver == NULL) {
        exit(1);
    }

    const char** blocks = malloc(resolver->num_labels * sizeof(const char*));

    if (test) {
        generate_test_data(resolver, blocks);
        exit(0);
    }

    while (1) {
        char line_buf[LINE_BUF_SZ];
        int l;
        uint32_t target;

        if (! quiet) {
            printf("Enter target as an integer in %u .. %u interval: ", \
                resolver->min_target, resolver->max_target);
        }
        if (fgets(line_buf, LINE_BUF_SZ, stdin) == NULL) {
            break;
        }
        l = strlen(line_buf);
        if (line_buf[l-1] != '\n') {
            fprintf(stderr, "Line too big, ignored!\n");
            continue;
        } else {
            line_buf[l-1] = 0;
        }
        if (sscanf(line_buf, "%u", &target) < 1) {
            fprintf(stderr, "`%s': invalid/missing target\n", line_buf);
            continue;
        }
        if (target < resolver->min_target || resolver->max_target < target) {
            fprintf(stderr, "%u: invalid target, outside: %u .. %u interval\n", \
                target, resolver->min_target, resolver->max_target);
            continue;
        }

        if (resolve(resolver, target, blocks) < 0) {
            /* Error, message already displayed, ignore */
            continue;
        }

        printf("%u -> ", target);
        display_blocks(blocks, resolver->num_labels);
        printf("\n");
    }

    if (! quiet) {
        printf("\n");
    }
}

