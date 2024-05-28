from pymodbus.client import AsyncModbusSerialClient
from pymodbus.transaction import ModbusRtuFramer
import asyncio
import time
import csv

async def main(rate):
	client = AsyncModbusSerialClient(method='rtu', port='/dev/ttyUSB0', baudrate=115200)
	await client.connect()

	assert client.connected

	print('setting zlac mode to 3, rpm control')
	await client.write_register(0x200D, 3, 1)

	print('setting acceleration time to 200 m/s')
	await client.write_registers(0x2080, [200, 200], 1)
	
	print('setting deceleration time to 200 m/s')
	await client.write_registers(0x2082, [200, 200], 1)
	
	print('starting zlac')
	await client.write_register(0x200E, 0x08, 1)
	
	start_time = time.time_ns()
	data = {}
	while time.time_ns() - start_time < 10e9:
		# set speed to [20-100] rpm
		rpm = int(20 + 80 * (time.time_ns() - start_time) * 1e-9 % 80)
		await client.write_register(0x2089, rpm, 1)

		#await asyncio.sleep(1/rate)

		# read speed
		result = await client.read_holding_registers(0x20AC, 1, 1)
		
		data[(time.time_ns() - start_time) * 1e-9] = result.registers[0]

		#print(f'{((time.time_ns() - start_time) * 1e-9):.4f}: {rpm}, {result.registers[0]}')

	await client.write_register(0x200E, 0x07, 1)
	client.close()

	return data

if __name__ == '__main__':
	data = asyncio.run(main(200))

	last_rpm = 0
	last_t = 0
	average_rate = 0
	number_of_changes = 0
	for t, rpm in data.items():
		if rpm != last_rpm:
			average_rate += t - last_t
			number_of_changes += 1
			last_rpm = rpm
			last_t = t

	average_rate /= number_of_changes
	print(f'average rate of change: {1/(average_rate):.5f} Hz')

	time_values = list(data.keys())
	average_change = sum(time_values[i+1] - time_values[i] for i in range(len(time_values)-1)) / (len(time_values)-1)
	print(f'average change between time values: {average_change:.5f} seconds')

	# Export data to CSV file
	filename = '/home/robote/zlac8015d-tests/scripts/data.csv'
	with open(filename, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['Time', 'RPM'])
		for t, rpm in data.items():
			writer.writerow([t, rpm])

	print(f'Data exported to {filename}')