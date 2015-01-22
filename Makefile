# Perhaps one of the simplest Makefiles there is...

CFLAGS=-Wall
TARGET=roguemonsters

.PHONY: all default clean run

all: default

default: $(TARGET)

$(TARGET):

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$(TARGET)
