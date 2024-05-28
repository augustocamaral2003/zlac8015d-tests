#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <modbus.h>

void write_register(modbus_t *client, int address, int value) {
	int status = modbus_write_register(client, address, value);
	if (status == -1) {
		fprintf(stderr, "failed to write register %d: %s\n", address, modbus_strerror(errno));
	}
}

int read_register(modbus_t *client, int address) {
	uint16_t value;
	int status = modbus_read_registers(client, address, 1, &value);
	if (status == -1) {
		fprintf(stderr, "failed to read register %d: %s\n", address, modbus_strerror(errno));
	}
	return value;
}

double micros() {
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1e6 + ts.tv_nsec / 1e3;
}

int main(int argc, char *argv[]) {
	if (argc != 2 || atoi(argv[1]) <= 0) {
		fprintf(stderr, "usage: %s <desired frequency>\n", argv[0]);
		return -1;
	}

    modbus_t *client;
    client = modbus_new_rtu("/dev/ttyUSB0", 115200, 'N', 8, 1);
	if (client == NULL) {
		fprintf(stderr, "failed to create modbus context\n");
        return -1;
	} else {
		modbus_set_slave(client, 1);
		if (modbus_connect(client) == -1) {
			fprintf(stderr, "connection failed: %s\n", modbus_strerror(errno));
            modbus_free(client);
            return -1;
		}
	}
	modbus_set_debug(client, 1);

	// set zlac mode
	printf("setting zlac mode to 3, RPM control\n");
	write_register(client, 0x200D, 3);

	// set accel time
	printf("setting acceleration time to 200 ms\n");
	write_register(client, 0x2080, 200);
	write_register(client, 0x2081, 200);

	// set decel time
	printf("setting deceleration time to 200 ms\n");
	write_register(client, 0x2082, 200);
	write_register(client, 0x2083, 200);

	// start motor
	printf("starting motor\n");
	write_register(client, 0x200E, 0x08);

	double start_time = micros();
	double t = 0;
	int num_points = 20 * atoi(argv[1]);

	struct point {
		double time;
		int rpm;
	} points[num_points];

	//double instruction_start;
	//double iteration_start;

	printf("collecting data using f = %d and num_points = %d\n", atoi(argv[1]), num_points);
	for (int i = 0; t < 20; i++) {
		break;
		//iteration_start = micros();

		// set right wheel rpm
		//instruction_start = micros();
		write_register(client, 0x2089, 20 + (i * (100 - 20) / (num_points - 1)));
		//printf("write speed time:\t%lf\t", (micros() - instruction_start) / 1e6);

		// read right wheel rpm
		//instruction_start = micros();
		int rpm = read_register(client, 0x20AC);
		//printf("read speed time:\t%lf\t", (micros() - instruction_start) / 1e6);

		// save point
		//instruction_start = micros();
		points[i].time = t;
		points[i].rpm = rpm;
		//printf("save point time:\t%lf\t", (micros() - instruction_start) / 1e6);

		if (i % 100 == 0)
			printf("time: %lf, rpm: %d, i: %d\n", t, rpm, i);

		//printf("iteration time:\t%lf\t%lf\n", (micros() - iteration_start) / 1e6, t);
		t = (micros() - start_time) * 1e-6;
	}

	// stop motor
	printf("stopping motor\n");
	write_register(client, 0x200E, 0x07);

	double average_period_of_change = 0;
	int number_of_changes = 0;
	int last_rpm = points[0].rpm;
	double last_time = points[0].time;
	for (int i = 1; i < num_points; i++) {
		if (points[i].rpm != last_rpm) {
			average_period_of_change += points[i].time - last_time;
			number_of_changes++;
			last_rpm = points[i].rpm;
			last_time = points[i].time;
		}
		//printf("time: %lf, rpm: %d\n", points[i].time, points[i].rpm);
	}
	average_period_of_change /= number_of_changes;

	printf("average rate of change: %lf\n", 1/average_period_of_change);

	
}