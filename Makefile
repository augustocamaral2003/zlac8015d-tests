CC := gcc
CFLAGS := -Wall -Wextra -Werror `pkg-config --cflags --libs libmodbus`

all: detect_frequency

detect_frequency: scripts/detect_frequency.c
	$(CC) -o $@ $^ $(CFLAGS)

.PHONY: clean
clean:
	rm -f detect_frequency

.PHONY: run
run: detect_frequency
	chmod +x detect_frequency
	./detect_frequency 300