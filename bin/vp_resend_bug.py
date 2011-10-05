"""Demonstrates DMPAFT "resend" bug. 

The Davis documentation says that a page can be resent on request, but it
does not seem to work.

Requires package "pyserial". This can be downloaded on Debian (Ubuntu) using

  apt-get install python-serial
  
To demonstrate the bug, simply run this file:

  python vp_resend_bug.py

AUTHOR:
    Tom Keffer (tkeffer@gmail.com)
    
DATE: 
    5-Oct-2011
"""
#    $Revision$
#    $Author$
#    $Date$
import serial
import struct
import time

# A few handy constants:
_ack    = chr(0x06)
_resend = chr(0x21)

# The time to request for the "DMPAFT" command:
year   = 2011
month  =   10
day    =   05
hour   =   00
minute =   00

# Main entry point:
def main():
    print "Demonstrates resend bug in the DMPAFT command"
    # Open up the port:
    serial_port = serial.Serial("/dev/ttyS0", baudrate=19200, timeout=5)
    
    # Wake it up:
    serial_port.write('\n\n\n')
    # Give it time to react
    time.sleep(0.5)
    # Flush the input
    serial_port.flushInput()
    
    # Now that we have its attention, look for the formal acknowledgment:
    serial_port.write('\n')
    # Get the response:
    response = serial_port.read(2)
    if response != '\n\r':
        print "Unable to wake up console"
        exit()
        
    print "Successfully woke up console"
    
    # Now send the DMPAFT command:
    serial_port.write('DMPAFT\n')
    
    # Get the response:
    response = serial_port.read(1)
    if response != _ack:
        print "Unable to get ACK from console after sending DMPAFT"
        exit()
        
    print "Got <ACK> after sending DMPAFT <ACK>"
    
    # Form the date & time using the Davis format:
    vantageDateStamp = day + (month<<5) + ((year-2000)<<9)
    vantageTimeStamp = hour *100 + minute
    
    #Pack the date and time into a string, little-endian order
    datestr = struct.pack("<HH", vantageDateStamp, vantageTimeStamp)
    
    #Calculate the crc for the date:
    crc = crc16(datestr)
        
    # ...and pack that on to the end of the date string in big-endian order:
    datestr_with_crc = datestr + struct.pack(">H", crc)
    
    # Write the date string with crc to the port:
    serial_port.write(datestr_with_crc)
    # Look for the acknowledgment.
    response = serial_port.read()
    if response != _ack:
        print "Unable to get <ACK> after sending encoded date/time string"
        exit()

    print "Got <ACK> after sending encoded date/time string"
    
    # Look for the number of pages that will be sent, 
    # the location of the first page, and a 2 byte CRC.
    _buffer = serial_port.read(6)
    # Unpack it (ignore the CRC):
    (_npages, _start_index) = struct.unpack("<HH", _buffer[:4])
    print "DMPAFT says that there will be %d pages with starting index %d" %(_npages, _start_index)

    # Start the download by sending an <ACK>
    serial_port.write(_ack)
    
    # Download the first page:
    _page = serial_port.read(267)
    
    # Get the page sequence number:
    _page_no = ord(_page[0])
    
    print "Successfully downloaded page number %d. Length is %d" % (_page_no, len(_page))
    
    print "HOWEVER, I will pretend the CRC is in error and ask for it again"
    
    # Request a resend
    serial_port.write(_resend)
    
    # Try to read it again. Unfortunately, the console does not respond
    # and the request times out.
    _page = serial_port.read(267)
    
    if len(_page) == 0:
        print "After asking for resend, an empty buffer was returned."
    else:
        print "No problem after asking for resend! Downloaded page number %d, length is %d" % (_page_no, len(_page))

#===============================================================================
#                                    UTILITIES
#===============================================================================

import array

_table=(
0x0000,  0x1021,  0x2042,  0x3063,  0x4084,  0x50a5,  0x60c6,  0x70e7,  # 0x00
0x8108,  0x9129,  0xa14a,  0xb16b,  0xc18c,  0xd1ad,  0xe1ce,  0xf1ef,  # 0x08  
0x1231,  0x0210,  0x3273,  0x2252,  0x52b5,  0x4294,  0x72f7,  0x62d6,  # 0x10
0x9339,  0x8318,  0xb37b,  0xa35a,  0xd3bd,  0xc39c,  0xf3ff,  0xe3de,  # 0x18
0x2462,  0x3443,  0x0420,  0x1401,  0x64e6,  0x74c7,  0x44a4,  0x5485,  # 0x20
0xa56a,  0xb54b,  0x8528,  0x9509,  0xe5ee,  0xf5cf,  0xc5ac,  0xd58d,  # 0x28
0x3653,  0x2672,  0x1611,  0x0630,  0x76d7,  0x66f6,  0x5695,  0x46b4,  # 0x30
0xb75b,  0xa77a,  0x9719,  0x8738,  0xf7df,  0xe7fe,  0xd79d,  0xc7bc,  # 0x38
0x48c4,  0x58e5,  0x6886,  0x78a7,  0x0840,  0x1861,  0x2802,  0x3823,  # 0x40
0xc9cc,  0xd9ed,  0xe98e,  0xf9af,  0x8948,  0x9969,  0xa90a,  0xb92b,  # 0x48
0x5af5,  0x4ad4,  0x7ab7,  0x6a96,  0x1a71,  0x0a50,  0x3a33,  0x2a12,  # 0x50
0xdbfd,  0xcbdc,  0xfbbf,  0xeb9e,  0x9b79,  0x8b58,  0xbb3b,  0xab1a,  # 0x58
0x6ca6,  0x7c87,  0x4ce4,  0x5cc5,  0x2c22,  0x3c03,  0x0c60,  0x1c41,  # 0x60
0xedae,  0xfd8f,  0xcdec,  0xddcd,  0xad2a,  0xbd0b,  0x8d68,  0x9d49,  # 0x68
0x7e97,  0x6eb6,  0x5ed5,  0x4ef4,  0x3e13,  0x2e32,  0x1e51,  0x0e70,  # 0x70
0xff9f,  0xefbe,  0xdfdd,  0xcffc,  0xbf1b,  0xaf3a,  0x9f59,  0x8f78,  # 0x78
0x9188,  0x81a9,  0xb1ca,  0xa1eb,  0xd10c,  0xc12d,  0xf14e,  0xe16f,  # 0x80
0x1080,  0x00a1,  0x30c2,  0x20e3,  0x5004,  0x4025,  0x7046,  0x6067,  # 0x88
0x83b9,  0x9398,  0xa3fb,  0xb3da,  0xc33d,  0xd31c,  0xe37f,  0xf35e,  # 0x90
0x02b1,  0x1290,  0x22f3,  0x32d2,  0x4235,  0x5214,  0x6277,  0x7256,  # 0x98
0xb5ea,  0xa5cb,  0x95a8,  0x8589,  0xf56e,  0xe54f,  0xd52c,  0xc50d,  # 0xA0
0x34e2,  0x24c3,  0x14a0,  0x0481,  0x7466,  0x6447,  0x5424,  0x4405,  # 0xA8
0xa7db,  0xb7fa,  0x8799,  0x97b8,  0xe75f,  0xf77e,  0xc71d,  0xd73c,  # 0xB0
0x26d3,  0x36f2,  0x0691,  0x16b0,  0x6657,  0x7676,  0x4615,  0x5634,  # 0xB8
0xd94c,  0xc96d,  0xf90e,  0xe92f,  0x99c8,  0x89e9,  0xb98a,  0xa9ab,  # 0xC0
0x5844,  0x4865,  0x7806,  0x6827,  0x18c0,  0x08e1,  0x3882,  0x28a3,  # 0xC8
0xcb7d,  0xdb5c,  0xeb3f,  0xfb1e,  0x8bf9,  0x9bd8,  0xabbb,  0xbb9a,  # 0xD0
0x4a75,  0x5a54,  0x6a37,  0x7a16,  0x0af1,  0x1ad0,  0x2ab3,  0x3a92,  # 0xD8
0xfd2e,  0xed0f,  0xdd6c,  0xcd4d,  0xbdaa,  0xad8b,  0x9de8,  0x8dc9,  # 0xE0
0x7c26,  0x6c07,  0x5c64,  0x4c45,  0x3ca2,  0x2c83,  0x1ce0,  0x0cc1,  # 0xE8
0xef1f,  0xff3e,  0xcf5d,  0xdf7c,  0xaf9b,  0xbfba,  0x8fd9,  0x9ff8,  # 0xF0
0x6e17,  0x7e36,  0x4e55,  0x5e74,  0x2e93,  0x3eb2,  0x0ed1,  0x1ef0,  # 0xF8
)

table = array.array('H',_table)

def crc16(string, crc=0):
    """ Calculate CRC16 sum"""

    for ch in string:
        crc = (table[((crc>>8)^ord(ch)) & 0xff] ^ (crc<<8)) & 0xffff
    return crc

# Invoke the entry point:
main()