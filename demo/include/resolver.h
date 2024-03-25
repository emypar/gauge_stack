/* Resolver interface
*/

#include <stdlib.h>

struct resolver {
    uint32_t min_target, max_target;
    const char** labels;
    int num_labels;
    /* Resolver specific, opaque for users */
    void* _resolver_internal;
};


/* 
Define the resolver interface if not included from a specific resolver code.
*/
#ifndef __is_resolver

/* String describing additional resolver args.
*/
extern const char* resolver_args;

/* Initialize a particular resolver, optionally using command line args.
*/
extern const struct resolver* init_resolver(int argc, char** argv);

/*  Resolver
    Args:
        resolver: the resolver info
        target: the target to resolve as an integer
        blocks: storage space for the labels, it is assumed to be 
                at least num_labels in size.
                If the resolution uses less than num_labels entries then the
                last entry is followed by NULL.

    Return value:
        < 0: Resolution error, the content of blocks is undefined. The error 
             message is assumed to have been displayed to stderr.
        >= 0: Successful resolution.
*/
extern int resolve(const struct resolver* resolver, uint32_t target, const char* blocks[]);

#endif