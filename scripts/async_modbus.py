from pymodbus.client import AsyncModbusSerialClient
import asyncio
import time

async def main(rate):
	client = AsyncModbusSerialClient(method='rtu', port='/dev/ttyUSB0', baudrate=115200)
	await client.connect()

	assert client.connected

	print('setting zlac mode to 3, rpm control')
	status = await client.write_register(0x200D, 3)
	if status.isError():
		print('error setting zlac mode')
		await client.close()
		return

	print('setting acceleration time to 200 m/s')
	status = await client.write_registers(0x2080, [200, 200])
	if status.isError():
		print('error setting acceleration time')
		await client.close()
		return
	
	print('setting deceleration time to 200 m/s')
	status = await client.write_registers(0x2082, [200, 200])
	if status.isError():
		print('error setting deceleration time')
		await client.close()
		return
	
	start_time = time.time_ns()
	data = {}
	while time.time_ns() - start_time < 20e9:
		# set speed to [20-100] rpm
		rpm = 20 + 80 * (time.time_ns() - start_time) % 80
		await client.write_register(0x2089, rpm)

		# read speed
		result = await client.read_holding_registers(0x20AC, 1)
		if not result.isError():
			data[time.time_ns() - start_time] = result.registers[0]
		else:
			print('error reading speed')
			break

		await asyncio.sleep(1/rate)
	
	return data


if __name__ == '__main__':
	data = asyncio.run(main(100))

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
	print(f'average rate of change: {1/(average_rate/1e9):.5f} Hz')