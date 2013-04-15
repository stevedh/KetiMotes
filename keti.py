"""
Copyright (c) 2013 Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions 
are met:

 - Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
 - Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
OF THE POSSIBILITY OF SUCH DAMAGE.
"""
"""
Keti mote protocol implementation and sMAP driver.

@author Stephen Dawson-Haggerty <stevedh@eecs.berkeley.edu>
"""

import uuid
import struct

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.python import log

from smap.iface.tinyos import TOSSerialClient
from smap.driver import SmapDriver


class KetiMoteReceiver(TOSSerialClient):
    TYPE_TH = 0x64
    TYPE_PIR = 0x65
    TYPE_CO2 = 0x66

    # SDH : not sure these are exactly right: should be changed to
    # match the SHT11 settings based on Table 6 and Table 8 in the
    # SHT11 data sheet.
    SHT11_D1 = -40.1
    SHT11_D2 = 0.01

    SHT11_C1 = -4.0
    SHT11_C2 = 0.0405
    SHT11_C3 = -2.8e-6
    SEQUENCE_CACHE = set([])

    def __init__(self, consumer):
        self.consumer = consumer
        TOSSerialClient.__init__(self)
    
    def packetReceived(self, pkt):
        if len(pkt) != 29:
            return

        # pull apart the packet header, ignoring the tinyos part
        typ, serial_id, node_id, seq, bat, sensor = struct.unpack(">H6sHHH6s", pkt[9:29])
        if (node_id, seq) in KetiMoteReceiver.SEQUENCE_CACHE:
            return
        else:
            KetiMoteReceiver.SEQUENCE_CACHE.add((node_id, seq))

        data  = {
            'serial_id': serial_id,
            'node_id': node_id,
            'sequence': seq,
            'battery': bat
            }

        # unpack the payload and calibrate if necessary
        if typ == self.TYPE_TH:
            temp, humid, lx = struct.unpack(">HHH", sensor)

            # calibrate the readings
            temp = self.SHT11_D1 + self.SHT11_D2 * temp
            humid_linear = (self.SHT11_C1 +
                            (self.SHT11_C2 * humid) +
                            (self.SHT11_C3 * (humid ** 2)))
            # skip temperatue compensation for now
            # indoor temperatures should be close to the 77DegF
            # recommended in the sht11 data sheet.            
            data.update({
                'temperature': temp,
                'humidity': humid_linear,
                'light': lx})
        elif typ == self.TYPE_PIR:
            pir, = struct.unpack(">H", sensor[:2])
            data.update({
                'pir': pir
                })
        elif typ == self.TYPE_CO2:
            ppm, = struct.unpack(">H", sensor[:2])
            data.update({
                'co2': ppm
                })
        self.consumer.dataReceived(data)


class KetiDriver(SmapDriver):
    CHANNELS = [('temperature', 'C', 'double'),
                ('humidity', '%RH', 'double'),
                ('light', 'lx', 'long'),
                ('pir', '#', 'long'),
                ('co2', 'ppm', 'long')]
    
    def setup(self, opts):
        self.port = opts.get('SerialPort', '/dev/ttyrd00')
        self.baud = int(opts.get('BaudRate', 115200))
        self.namespace = opts.get('Namespace', None)
        if self.namespace: self.namespace = uuid.UUID(self.namespace)

    def uuid(self, serial_id, channel):
        # create consistent uuids for data based on the serial id
        key = serial_id + '-' + channel
        if self.namespace:
            return uuid.uuid5(self.namespace, key)
        else:
            return SmapDriver.uuid(self, key)

    def start(self):
        self.serial = SerialPort(KetiMoteReceiver(self), self.port,
                                 reactor, baudrate=self.baud)

    def stop(self):
        return self.serial.loseConnection()

    def create_channels(self, msg):
        if not self.get_collection('/' + str(msg['node_id'])):
            for (name, unit, dtype) in self.CHANNELS:
                self.add_timeseries('/' + str(msg['node_id']) + '/' + name,
                                    self.uuid(msg['serial_id'], name),
                                    unit, data_type=dtype)
            self.set_metadata('/' + str(msg['node_id']), {
                'Metadata/Instrument/PartNumber': str(msg['node_id']),
                'Metadata/Instrument/SerialNumber': ':'.join(map(lambda x: hex(ord(x))[2:],
                                                                msg['serial_id']))
                })

    def dataReceived(self, msg):
        self.create_channels(msg)
        for (name, _, __) in self.CHANNELS:
            if name in msg:
                self._add('/' + str(msg['node_id']) + '/' + name,
                          msg[name])

