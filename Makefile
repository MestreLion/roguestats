# Perhaps one of the simplest Makefiles there is...

CFLAGS=-Wall
TARGETS=roguemonsters xplevels

.PHONY: all default clean run

all: default

default: $(TARGETS)

$(TARGETS):

clean:
	rm -f $(TARGETS)

run: $(TARGET)
	./$(TARGETS)
