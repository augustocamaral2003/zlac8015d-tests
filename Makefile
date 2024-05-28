CC := gcc
CFLAGS := -Wall -Wextra -Werror `pkg-config --cflags --libs libmodbus`

all: detect_frequency

detect_frequency: scripts/detect_frequency.c
	$(CC) -o $@ $^ $(CFLAGS)
	chomod +x detect_frequency
	./detect_frequency 300

async:
	python3 scripts/async_modbus.py

.PHONY: clean
clean:
	rm -f detect_frequency