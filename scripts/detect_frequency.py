import sys
import time
from pymodbus.client import AsyncModbusSerialClient as modbus

def write_register(client, address, value):
    status = client.write_register(address, value)
    if status == -1:
        print(f"failed to write register {address}: {client.last_error()}", file=sys.stderr)

def read_register(client, address):
    value, status = client.read_registers(address, 1)
    if status == -1:
        print(f"failed to read register {address}: {client.last_error()}", file=sys.stderr)
    return value

def micros():
    ts = time.monotonic_ns() // 1000
    return ts

if __name__ == "__main__":
    if len(sys.argv) != 2 or int(sys.argv[1]) <= 0:
        print(f"usage: {sys.argv[0]} <desired frequency>", file=sys.stderr)
        sys.exit(-1)

    client = modbus("/dev/ttyUSB0", 115200, 'N', 8, 1)
    if not client:
        print("failed to create modbus context", file=sys.stderr)
        sys.exit(-1)
    else:
        client.set_slave(1)
        if client.connect() == -1:
            print(f"connection failed: {client.last_error()}", file=sys.stderr)
            client.close()
            sys.exit(-1)

    # set zlac mode
    print("setting zlac mode to 3, RPM control")
    write_register(client, 0x200D, 3)

    # set accel time
    print("setting acceleration time to 200 ms")
    write_register(client, 0x2080, 200)
    write_register(client, 0x2081, 200)

    # set decel time
    print("setting deceleration time to 200 ms")
    write_register(client, 0x2082, 200)
    write_register(client, 0x2083, 200)

    # start motor
    print("starting motor")
    write_register(client, 0x200E, 0x08)

    start_time = micros()
    t = 0
    num_points = 20 * int(sys.argv[1])

    class Point:
        def __init__(self, time, rpm):
            self.time = time
            self.rpm = rpm

    points = []

    print(f"collecting data using f = {int(sys.argv[1])} and num_points = {num_points}")
    while t < 20:
        iteration_start = micros()

        # set right wheel rpm
        instruction_start = micros()
        write_register(client, 0x2089, 20 + (len(points) * (100 - 20) / (num_points - 1)))
        print(f"write speed time:\t{(micros() - instruction_start) / 1e6}\t", end="")

        # read right wheel rpm
        instruction_start = micros()
        rpm = read_register(client, 0x20AC)
        print(f"read speed time:\t{(micros() - instruction_start) / 1e6}\t", end="")

        # save point
        instruction_start = micros()
        points.append(Point(t, rpm))
        print(f"save point time:\t{(micros() - instruction_start) / 1e6}\t", end="")

        if len(points) % 100 == 0:
            print(f"time: {t}, rpm: {rpm}, i: {len(points)}")

        print(f"iteration time:\t{(micros() - iteration_start) / 1e6}\t{t}")
        t = (micros() - start_time) * 1e-6

    # stop motor
    print("stopping motor")
    write_register(client, 0x200E, 0x07)

    average_period_of_change = 0
    number_of_changes = 0
    last_rpm = points[0].rpm
    last_time = points[0].time
    for i in range(1, len(points)):
        if points[i].rpm != last_rpm:
            average_period_of_change += points[i].time - last_time
            number_of_changes += 1
            last_rpm = points[i].rpm
            last_time = points[i].time
        print(f"time: {points[i].time}, rpm: {points[i].rpm}")
    average_period_of_change /= number_of_changes

    print(f"average rate of change: {1/average_period_of_change}")