from pymodbus.client import ModbusSerialClient
from pymodbus.transaction import ModbusRtuFramer
import time

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

client = ModbusSerialClient(port='/dev/ttyUSB0', baudrate=115200, framer=ModbusRtuFramer)
client.connect()

assert client.connect()

print('setting zlac mode to 3, rpm control')
status = client.write_register(0x200D, 3)
if status.isError():
    print('error setting zlac mode')

print('setting acceleration time to 200 m/s')
status = client.write_registers(0x2080, [200, 200])
if status.isError():
    print('error setting acceleration time')

print('setting deceleration time to 200 m/s')
status =client.write_registers(0x2082, [200, 200])
if status.isError():
    print('error setting deceleration time')
    
