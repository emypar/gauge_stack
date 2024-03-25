SRC_DIR := src/
INCLUDE_DIR := include/
OBJ_DIR := obj/
BIN_DIR := bin/
EXE_SUFFIX := 
DEBUG_SUBDIR := debug/
DEBUG_SUFFIX := .debug

# Certain files are blockset specific:
BLOCKSET := blockset_81
BLOCKSET_SUBDIR := $(BLOCKSET)/

CC := gcc
C_INCLUDE_FLAGS := -I$(INCLUDE_DIR) -I$(INCLUDE_DIR)$(BLOCKSET_SUBDIR)
CFLAGS := -O2 $(C_INCLUDE_FLAGS)
LDFLAGS :=

ifeq ($(DEBUG), 1)
	OBJ_DIR := $(OBJ_DIR)$(DEBUG_SUBDIR)
	EXE_SUFFIX := $(EXE_SUFFIX)$(DEBUG_SUFFIX)
	CFLAGS := -g  $(C_INCLUDE_FLAGS)
endif


all: bitmap_z_mem_resolver bitmap_mem_resolver bitmap_file_resolver


bitmap_z_mem_resolver: $(BIN_DIR)$(BLOCKSET_SUBDIR)bitmap_z_mem_resolver$(EXE_SUFFIX)

$(BIN_DIR)$(BLOCKSET_SUBDIR)bitmap_z_mem_resolver$(EXE_SUFFIX): $(OBJ_DIR)$(BLOCKSET_SUBDIR)bitmap_z_mem_resolver.o $(OBJ_DIR)main.o
	mkdir -p $(dir $@)
	$(CC) -o $@ $^ $(LDFLAGS) -lz

$(OBJ_DIR)bitmap_z_mem_resolver.o:  $(INCLUDE_DIR)$(BLOCKSET_SUBDIR)bbitmap_z.h $(INCLUDE_DIR)resolver.h


bitmap_mem_resolver: $(BIN_DIR)$(BLOCKSET_SUBDIR)bitmap_mem_resolver$(EXE_SUFFIX)

$(BIN_DIR)$(BLOCKSET_SUBDIR)bitmap_mem_resolver$(EXE_SUFFIX): $(OBJ_DIR)$(BLOCKSET_SUBDIR)bitmap_mem_resolver.o $(OBJ_DIR)main.o
	mkdir -p $(dir $@)
	$(CC) -o $@ $^ $(LDFLAGS)

$(OBJ_DIR)$(BLOCKSET_SUBDIR)bitmap_mem_resolver.o: $(INCLUDE_DIR)$(BLOCKSET_SUBDIR)bitmap.h $(INCLUDE_DIR)resolver.h

bitmap_file_resolver: $(BIN_DIR)bitmap_file_resolver$(EXE_SUFFIX)

$(BIN_DIR)bitmap_file_resolver$(EXE_SUFFIX): $(OBJ_DIR)bitmap_file_resolver.o $(OBJ_DIR)main.o
	mkdir -p $(dir $@)
	$(CC) -o $@ $^ $(LDFLAGS)

$(OBJ_DIR)bitmap_file_resolver.o: $(INCLUDE_DIR)resolver.h


$(OBJ_DIR)main.o: $(INCLUDE_DIR)resolver.h

$(OBJ_DIR)$(BLOCKSET_SUBDIR)%.o: $(SRC_DIR)%.c
	mkdir -p $(dir $@)
	$(CC) -c $(CFLAGS) -o $@ $<

$(OBJ_DIR)%.o: $(SRC_DIR)%.c
	mkdir -p $(dir $@)
	$(CC) -c $(CFLAGS) -o $@ $<

clean:
	rm -rf $(OBJ_DIR)*.o $(OBJ_DIR)*/*.o
	if [ -n "$(BIN_DIR)" ]; then rm -rf $(BIN_DIR)* $(BIN_DIR)*/*; fi

.PHONY: bitmap_z_mem_resolver bitmap_mem_resolver bitmap_file_resolver

.SUFFIEXS:

