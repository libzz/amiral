#!/usr/bin/python
# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CRCnet Monitor - Solar Monitoring Support
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
import sys
import time
from uspp import *

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_clientserver import registerPage, registerRecurring
from crcnetd._utils.ccsd_config import config_get
from crcnetd._utils.ccsd_events import registerEvent, triggerEvent

from ccs_monitor_web import registerMenuItem, HTable, returnPage, \
    returnErrorPage, MENU_TOP, MENU_GROUP_GENERAL
import  ccs_monitor_snmp as snmp

registerDynamicOID = snmp.registerDynamicOID

class ccs_solar_error(ccsd_error):
    pass

ccs_mod_type = CCSD_CLIENT

DEFAULT_TRISTAR_PORT = "/dev/ttyS0"
DEFAULT_AV_MAX = 24
DEFAULT_CI_MAX = 45

# Implement the Tristar Solar portion of the CRCnet-MIB
CRCNET_TRISTAR45_MIB = (1,3,6,1,4,1,15120,1,2,1)
# All wireless interface properties
CRCNET_TRISTAR45_PROPS = range(1,26)

# CRC tables for calculating CRC's over the serial packets
CRCtablehi = (
0x0,0xc0,0xc1,0x1,0xc3,0x3,0x2,0xc2,0xc6,0x6,0x7,0xc7,0x5,0xc5,0xc4,0x4,
0xcc,0xc,0xd,0xcd,0xf,0xcf,0xce,0xe,0xa,0xca,0xcb,0xb,0xc9,0x9,0x8,0xc8,
0xd8,0x18,0x19,0xd9,0x1b,0xdb,0xda,0x1a,0x1e,0xde,0xdf,0x1f,0xdd,0x1d,0x1c,0xdc,
0x14,0xd4,0xd5,0x15,0xd7,0x17,0x16,0xd6,0xd2,0x12,0x13,0xd3,0x11,0xd1,0xd0,0x10,
0xf0,0x30,0x31,0xf1,0x33,0xf3,0xf2,0x32,0x36,0xf6,0xf7,0x37,0xf5,0x35,0x34,0xf4,
0x3c,0xfc,0xfd,0x3d,0xff,0x3f,0x3e,0xfe,0xfa,0x3a,0x3b,0xfb,0x39,0xf9,0xf8,0x38,
0x28,0xe8,0xe9,0x29,0xeb,0x2b,0x2a,0xea,0xee,0x2e,0x2f,0xef,0x2d,0xed,0xec,0x2c,
0xe4,0x24,0x25,0xe5,0x27,0xe7,0xe6,0x26,0x22,0xe2,0xe3,0x23,0xe1,0x21,0x20,0xe0,
0xa0,0x60,0x61,0xa1,0x63,0xa3,0xa2,0x62,0x66,0xa6,0xa7,0x67,0xa5,0x65,0x64,0xa4,
0x6c,0xac,0xad,0x6d,0xaf,0x6f,0x6e,0xae,0xaa,0x6a,0x6b,0xab,0x69,0xa9,0xa8,0x68,
0x78,0xb8,0xb9,0x79,0xbb,0x7b,0x7a,0xba,0xbe,0x7e,0x7f,0xbf,0x7d,0xbd,0xbc,0x7c,
0xb4,0x74,0x75,0xb5,0x77,0xb7,0xb6,0x76,0x72,0xb2,0xb3,0x73,0xb1,0x71,0x70,0xb0,
0x50,0x90,0x91,0x51,0x93,0x53,0x52,0x92,0x96,0x56,0x57,0x97,0x55,0x95,0x94,0x54,
0x9c,0x5c,0x5d,0x9d,0x5f,0x9f,0x9e,0x5e,0x5a,0x9a,0x9b,0x5b,0x99,0x59,0x58,0x98,
0x88,0x48,0x49,0x89,0x4b,0x8b,0x8a,0x4a,0x4e,0x8e,0x8f,0x4f,0x8d,0x4d,0x4c,0x8c,
0x44,0x84,0x85,0x45,0x87,0x47,0x46,0x86,0x82,0x42,0x43,0x83,0x41,0x81,0x80,0x80
)
CRCtablelo = (
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x40,0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,
0x0,0xc1,0x81,0x40,0x1,0xc0,0x80,0x41,0x1,0xc0,0x80,0x41,0x0,0xc1,0x81,0x81
)

# Tristar commands
TS_BATT_V_F         = 0x0008    # Battery voltage, filtered (Tau=2.5s)
TS_BATTSENSE_V_F    = 0x0009    # Battery sense voltage, filtered (Tau=2.5s)
TS_ARRAY_V_F        = 0x000A    # Array/Load voltage, filtered (Tau=2.5s)
TS_CHARGE_I_F       = 0x000B    # Battery charge current, filtered (Tau=2.5s)
TS_LOAD_I_F         = 0x000C    # Load current, filtered (Tau=2.5s)
TS_BATT_V_SF        = 0x000D    # Battery voltage, slow filter (Tau=25s)
TS_HSTEMP_DEG       = 0x000E    # Heatsink temperature
TS_BATTEMP_DEG      = 0x000F    # Battery temperature
TS_REF_V            = 0x0010    # Charge regulator reference voltage
TS_AMPHR_AH_HI      = 0x0011    # Ah resetable, HI word
TS_AMPHR_AH_LO      = 0x0012    # Ah resetable, LO word
TS_TOTALAMPHR_AH_HI = 0x0013    # Ah total, HI word
TS_TOTALAMPHR_AH_LO = 0x0014    # Ah total, LO word
TS_HRMETER_HR_HI    = 0x0015    # Hourmeter, HI word
TS_HRMETER_HR_LO    = 0x0016    # Hourmeter, LO word
TS_ALARMBITS_B_LO   = 0x0017    # Alarm bitfield - low bits
TS_FAULTBITS_B      = 0x0018    # Fault bitfield
TS_DIPSWITCH_B      = 0x0019    # Dip switch settings at power on
TS_CONTROLMODE      = 0x001A    # Control mode (0=charge, 1=load, 2=diversion)
TS_CONTROLSTATE     = 0x001B    # Control state
TS_PWMDUT           = 0x001C    # PWM Duty Cycle - 0-255
TS_ALARMBITS_B_HI   = 0x001D    # Alarm bitfield (continued from 0x0017)

# EEPROM registers for the tristar
TS_REGVAT25_V       = 0xE000    # Regulation voltage @ 25 deg C
TS_FLVAT25_V        = 0xE001    # Float voltage @ 25 deg C
TS_TBEFOREFL_S      = 0xE002    # Time before entering float
TS_TBEFOREFLLB_S    = 0xE003    # Time before entering float due to low battery
TS_LBVTRIGFL_V      = 0xE004    # Voltage that triggers low battery float time
TS_FLCANCEL_V       = 0xE005    # Voltage that cancels float
TS_EQUVAT25_V       = 0xE006    # Equalize voltage @ 25 deg C
TS_TBETWEENEQU_D    = 0xE007    # Days between eq cycles
TS_EQUTLIMIT_S      = 0xE008    # Equalize time limit above Vreg
TS_EQUTLIMITATVEQ_S = 0xE009    # Equalize time limit at Veq
TS_EVTEMPCOMP       = 0xE00A    # EV_tempcomp LSB only (note -(2-16) scaling)
TS_HVDCAT25         = 0xE00B    # High Voltage Disconnect @ 25 deg C
TS_HVRC             = 0xE00C    # High Voltage Reconnect
TS_DSLEQU           = 0xE00D    # Days since last equalize
TS_CUMTAT100        = 0xE00E    # Cum. time at 100% duty cycle, exit float
TS_LVDC             = 0xE00F    # Low Voltage Disconnect
TS_LVRC             = 0xE010    # Low Voltage Reconnect
TS_LHVDC            = 0xE011    # Load High Voltage Disconnect
TS_LHVRC            = 0xE012    # Load High Voltage Reconnect
TS_LVDLCC           = 0xE013    # LVD Load current compensation
TS_LVDWT            = 0xE014    # LVD warning timeout
TS_LTASS            = 0xE015    # Lighting Time after sunset
TS_LTASR            = 0xE016    # Lighting time before sunrise
TS_LIGHTCFG_B       = 0xE017    # Lighting Configuration Bits
TS_NTT_V            = 0xE018    # Night time threshold - Array Voc
TS_MTT_V            = 0xE019    # Morning threshold for timing - Array Voc
TS_MTL_V            = 0xE01A    # Morning threshold for lighting - Array Voc
TS_LEDGGY_V         = 0xE01B    # LED green to green/yellow limit
TS_LEDGYY_V         = 0xE01C    # LED green/yellow to yellow limit
TS_LEDYYR_V         = 0xE01D    # LED yellow to yellow/red limit
TS_LEDYRR_V         = 0xE01E    # LED yellow/red to red limit
TS_MAXTCOMP_DEG     = 0xE01F    # Max battery temp compensation limit deg C
TS_MINTCOMP_DEG     = 0xE020    # Min battery temp compensation limit deg C
TS_SERVID           = 0xE021    # Modbus TriStar server ID
TS_DBBSI_D          = 0xE022    # Days between battery service intervals
TS_DSLBS_D          = 0xE023    # Days since last battery service
TS_PHRMETER_HR_LO   = 0xE024    # Hourmeter - low word
TS_PHRMETER_HR_HI   = 0xE025    # Hourmeter - high word
TS_RESAH_AH_LO      = 0xE026    # Resetable Ah low
TS_RESAH_AH_HI      = 0xE027    # Resetable Ah high
TS_TOTAH_AH_LO      = 0xE028    # Total Ah low byte
TS_TOTAH_AH_HI      = 0xE029    # Total Ah high byte
TS_KWH              = 0xE02A    # Kilowatt hours
TS_MINBV_V          = 0xE02B    # Minimum battery voltage
TS_MAXBV_V          = 0xE02C    # Maximum battery voltage

# Calibration registers for the tristar
TS_SERNUM10         = 0xF000    # Serial number (8 byte ascii string) [1][0]
TS_SERNUM32         = 0xF001    # [3][2]
TS_SERNUM54         = 0xF002    # [5][4]
TS_SERNUM76         = 0xF003    # [7][6]
TS_BVDCALAT48_V     = 0xF004    # Battery voltage divider calib., 48V mode
TS_BVDCALAT1224_V   = 0xF005    # Battery voltage divider calib., 12/24V mode
TS_CHARGEICAL_I     = 0xF006    # Charge current calibration
TS_LOADICAL_I       = 0xF007    # Load current calibration
TS_SENSEVCAL_V      = 0xF008    # Sense voltage calibration
TS_ALVDCAL_V        = 0xF009    # Array/Load voltage divider calibration
TS_HWVER            = 0xF00A    # MSB:H/W Version major,LSB:H/W version minor
TS_CALSTATE         = 0xF00B    # MSB:Calibration state (0x5A is calibrated).
                                # LSB is 0x01 for the TS-60, 0x00 for the TS-45

# Time that the amphours were last reset
amphours_reset = 0
# ID String of the tristar
ts_id = "No Tristar Detected"

##############################################################################
# Utility Functions
##############################################################################
def init_serial():
    """Initialises the serial port and connects to the tristar"""

    portname = config_get("status", "tristar_port", DEFAULT_TRISTAR_PORT)

    # Open the port
    p=[1, 0, 2301, 0, 13, 13]
    tty = SerialPort(portname, timeout=100, speed=9600, mode="232", params=p)

    return tty

def write_serial(fd, bytes):
    """Writes the bytes in the supplied tuple to the serial port"""
    fd.write("".join([chr(a) for a in bytes]))

def read_serial(fd):
    """Returns a tuple containing bytes read from the serial port"""

    bytes = ()

    try:
        while 1:
            b = fd.read()
            bytes += (ord(b),)
    except SerialPortException:
        # Timeout raised
        pass

    return bytes

def calc_crc(bytes):
    """Calculates a CRC checksum over the specified bytes"""
    CRC = 0xFFFF

    for i in bytes:
        CRC^=i
        CRC=((CRC>>8)&0xFF)^CRCtablelo[CRC&0xFF]|(CRCtablehi[CRC&0xFF]<<8)

    return CRC&0xFFFF

def ts_do(w_pdu, exp_rcode, no_crc=False):
    """Queries the tristar with the specified packet and reads the result

    The packet passed to this function should have two spare bytes at the end
    for the checksum to be inserted into.

    The exp_rcode should contain a sequence of expected bytes that must be
    found starting at offset 1 of the returned value for the request to succeed

    Some basic checks are performed on the result, if these pass the entire
    result is passed back for further processing.
    """


    # Calculate the checksum and store in the last two positions
    if not no_crc:
        w_pdu = list(w_pdu)
        i = calc_crc(w_pdu[:-2])
        w_pdu[6] = i&0xFF
        w_pdu[7] = (i&0xFF00)>>8

    # Open a connection to the tristar
    tty = init_serial()

    # Try and read 10 times before giving up
    for i in range(0,10):
        write_serial(tty, w_pdu)
        r = read_serial(tty)
        if len(r) <= 2:
            continue

        # Check that the PDU is the response to the request we made
        if r[0] != w_pdu[0]:
            continue

        # Check the checksum
        k=calc_crc(r[:-2])
        if r[-1]!=((k&0xFF00)>>8) and r[-2]!=(k&0xFF):
            continue

        # Check for explicit error
        if r[1] == 0x84:
            log_error("Bad packet received from Tristar")
            del tty
            return None

        # Check the appropriate codes to ensure that this is
        # the response for the request we made
        i = 1
        for val in exp_rcode:
            if r[i] != val:
                continue
            i+=1

        # All OK
        del tty
        return r

    # Timed out
    del tty
    log_error("Tristar Request Timed Out")
    return None

def ts_readreg(reg):
    """Returns the value of the specified register on the tristar unit"""

    # Setup the request
    w_pdu = [0x01,0x04,(reg&0xFF00)>>8,reg&0xFF,0x00,0x01,0x00,0x00]

    # Send the request
    r = ts_do(w_pdu, (0x04, 0x02))
    if r is None:
        return 0xFFFF

    # Return the result
    return (r[3]<<8)|r[4]

def ts_writecoil(reg, val):
    """Writes a value to the specified "coil" on the Tristar unit"""

    # Setup the request
    w_pdu = [0x01,0x05,(reg&0xFF00)>>8,reg&0xFF,(val&0xFF00)>>8,val&0xFF,
        0x00,0x00]

    # Send the request
    r = ts_do(w_pdu, (0x04, 0x02))
    if r is None:
        return 0xFFFF

    # Return the result
    return (r[3]<<8)|r[4]

def find_tristar():
    """Tries to find a Tristar device on the serial port"""
    global ts_id
    
    # Setup the request
    tristar_requestID = (0x01,0x2B,0x0E,0x01,0x00,0x70,0x77)

    # Send the request
    r = ts_do(tristar_requestID, (0x2B, 0x0E, 0x01), True)
    if r is None:
        log_error("Could not detect Tristar unit!")
        return False

    # Filter through the data to find the stuff we want
    tptr=8
    matches=0
    id = ""
    for k in range(0,r[7]):
        start = tptr+2
        end = start + r[tptr+1]
        string = "".join([chr(a) for a in r[start:end]])
        if r[tptr]==0x00:
            # Vendor Name
            if string == "Morningstar Corp.":
                matches+=1
                id = string
        elif r[tptr]==0x01:
            # Product Code
            if string == "TS-45" or string == "TS-60":
                matches+=1
                id = "%s %s" % (id, string)
        elif r[tptr]==0x02:
            id = "%s %s" % (id, string)
        # Move on
        tptr += r[tptr+1]+2

    if matches < 2:
        log_error("Could not detect Tristar unit!")
        return False
    else:
        log_info("Detected Solar Controller: %s" % id)
        ts_id = id
        return True

# Helper functions to read and process data from the tristar
def ts_battv():
    d=ts_readreg(TS_BATT_V_F)
    d*=96.667/32768
    return d*1000
def ts_battsensev():
    d=ts_readreg(TS_BATTSENSE_V_F)
    d*=96.667/32768
    return d*1000
def ts_arrayv():
    av_max = portname = config_get("status", "array_v_max", DEFAULT_AV_MAX)
    for i in range(0,2):
        d=ts_readreg(TS_ARRAY_V_F)
        d*=139.15/32768
        if d <= av_max:
            return d*1000
    return 0
def ts_chargei():
    ci_max = portname = config_get("status", "charge_i_max", DEFAULT_CI_MAX)
    for i in range(0,2):
        d=ts_readreg(TS_CHARGE_I_F)
        d*=66.667/32768
        if d <= ci_max:
            return d*1000
    return 0
def ts_loadi():
    d=ts_readreg(TS_LOAD_I_F)
    d*=316.67/32768
    return d*1000
def ts_battvs():
    d=ts_readreg(TS_BATT_V_SF)
    d*=96.667/32768
    return d*1000
def ts_refv():
    d=ts_readreg(TS_REF_V)
    d*=96.667/32768
    return d*1000
def ts_amphours():
    i=ts_readreg(TS_AMPHR_AH_HI)
    i2=ts_readreg(TS_AMPHR_AH_LO)
    i&=0xFFFF
    i<<=16
    i|=(0xFFFF&i2)
    d=i*0.1
    return d*1000
def ts_totalamphours():
    i=ts_readreg(TS_TOTALAMPHR_AH_HI)
    i2=ts_readreg(TS_TOTALAMPHR_AH_LO)
    i&=0xFFFF
    i<<=16
    i|=(0xFFFF&i2)
    d=i*0.1
    return d*1000
def ts_hrmeter():
    i=ts_readreg(TS_HRMETER_HR_HI)
    i2=ts_readreg(TS_HRMETER_HR_LO)
    i&=0xFFFF
    i<<=16
    i|=(0xFFFF&i2)
    d=i*0.1
    return d*1000
def ts_minbv():
    d=ts_readreg(TS_MINBV_V)
    d*=96.667/32768
    return d*1000
def ts_maxbv():
    d=ts_readreg(TS_MAXBV_V)
    d*=96.667/32768
    return d*1000
def ts_pwm():
    d = ts_readreg(TS_PWMDUT)
    if d>230:
        d = 230
    d/=230
    d*=100
    return d*1000
def ts_serial():
    buf = ""
    i=ts_readreg(TS_SERNUM10)
    buf += chr(i&0xFF)
    buf += chr((i>>8)&0xFF)
    i=ts_readreg(TS_SERNUM32)
    buf += chr(i&0xFF)
    buf += chr((i>>8)&0xFF)
    i=ts_readreg(TS_SERNUM54)
    buf += chr(i&0xFF)
    buf += chr((i>>8)&0xFF)
    i=ts_readreg(TS_SERNUM76)
    buf += chr(i&0xFF)
    buf += chr((i>>8)&0xFF)
    return buf
def ts_hwver():
    i=ts_readreg(TS_SERNUM10)
    min = (0xFF&i)
    max = ((i>>8)&0xFF)
    return "%d.%d" % (max,min)
def ts_controlmode_s():
    i = ts_readreg(TS_CONTROLMODE)
    if i == 0:
        return "Charge"
    elif i == 1:
        return "Load"
    elif i == 2:
        return "Diversion"
    else:
        return "Unknown (%d)" % i
def ts_controlstate_s():
    i = ts_readreg(TS_CONTROLSTATE)
    if i == 0:
        return "Start"
    elif i == 1:
        return "Night Check"
    elif i == 2:
        return "Disconnect"
    elif i == 3:
        return "Night"
    elif i == 4:
        return "Fault"
    elif i == 5:
        return "Bulk"
    elif i == 6:
        return "PWM"
    elif i == 7:
        return "Float"
    elif i == 8:
        return "Equalize"
    else:
        return "Unknown (%d)" % i
    
def reset_amphours():
    """Resets the AMP hour count on the tristar"""
    global amphours_reset
    
    if ts_writecoil(0x0010, 0xFF00) != 0xFFFF:
        amphours_reset = time.time()
        return True
    
    log_warning("Failed to reset AMP hour count")
    return False

@registerRecurring(60)
def monitor_amphours():
    """Called regularly to monitor the amp hours value.

    The main purpose of this function is to reset the amphours to 0 at midnight
    """
    global amphours_reset
    
    t = time.localtime()
    if t[3] != 0:
        # Not midnight hour
        return

    # Midnight hour, if last amphours reset was before midnight, reset
    now = time.time()
    if amphours_reset > (now-((t[4]+1)*60)):
        return

    log_info("Resetting amp hours to 0")
    reset_amphours()
    return

##############################################################################
# Initialisation
##############################################################################
def ccs_init():

    if not find_tristar():
        return

    # Reset the amp hours
    reset_amphours()
    
    # Register the SNMP handler
    @registerDynamicOID(CRCNET_TRISTAR45_MIB)
    def wrapper(o, g): 
        try:
            return solarsnmp(o,g)
        except:
            log_error("Unexpected error handling solarsnmp!", sys.exc_info())
            return None

    # Add a menu entry
    registerMenuItem(MENU_TOP, MENU_GROUP_GENERAL, \
                    "/status/solar", "Solar Controller Status")

##############################################################################
# Content Pages
##############################################################################
@registerPage("/status/solar")
def solarpage(request, method):
    """Returns information about the solar controller attached to this node"""
    global ts_id, amphours_reset
    
    if request.query.find("resetAH=true") != -1:
        log_info("Resetting AMP hours at user request")
        reset_amphours()
    
    ah_reset = time.strftime("%c", time.localtime(amphours_reset))
    info = (ts_id, ts_serial(), ts_hwver(), ts_battv(), ts_battsensev(), \
            ts_arrayv(), ts_chargei(), ts_battvs(), \
            ts_readreg(TS_HSTEMP_DEG), ts_readreg(TS_BATTEMP_DEG), ts_refv(), \
            ah_reset, ts_amphours(), ts_totalamphours(), ts_controlmode_s(), \
            ts_controlstate_s(), ts_pwm(), ts_readreg(TS_KWH))
    
    # Build interfaces information
    output = """<div class="content">
<h2>Solar Controller (%s) Status</h2><br />
<style>
TH {
    width: 20em;
}
</style>
<div>
<table cellpadding=2 cellspacing=1 border=0>
<tbody>
<tr>
    <th>Serial Number:</th>
    <td>%s</td>
</tr>
<tr>
    <th>Hardware Version:</th>
    <td>%s</td>
</tr>
<tr>
    <th>Battery Voltage:</th>
    <td>%2.2fV</td>
</tr>
<tr>
    <th>Battery Sense Voltage:</th>
    <td>%2.2fV</td>
</tr>
<tr>
    <th>Array Voltage:</th>
    <td>%2.2fV</td>
</tr>
<tr>
    <th>Charge Current:</th>
    <td>%2.2fA</td>
</tr>
<tr>
    <th>Battery Voltage (Slow):</th>
    <td>%2.2fV</td>
</tr>
<tr>
    <th>Heatsink Temperature:</th>
    <td>%2.0fC</td>
</tr>
<tr>
    <th>Battery Temperature:</th>
    <td>%2.0fC</td>
</tr>
<tr>
    <th>Reference Voltage:</th>
    <td>%2.2fV</td>
</tr>
<tr>
    <th>Amp Hours<br />(since %s):</th>
    <td valign="top">%s&nbsp;&nbsp;
    <a href="/status/solar?resetAH=true">[reset now]</a>
    </td>
</tr>
<tr>
    <th>Amp Hours (Total):</th>
    <td>%s</td>
</tr>
<tr>
    <th>Control Mode:</th>
    <td>%s</td>
</tr>
<tr>
    <th>Control State:</th>
    <td>%s</td>
</tr>
<tr>
    <th>PWM Duty Cycle:</th>
    <td>%d%%</td>
</tr>
<tr>
    <th>Kilowatt Hours:</th>
    <td>%s</td>
</tr>
</tbody>
</table>
</div>
""" % info

    returnPage(request, "Solar Controller Status", output) 

def solarsnmp(oid, getNext):
    
    iface = None
    
    # Strip off the base of the oid
    base = oid[:len(CRCNET_TRISTAR45_MIB)]
    if base != CRCNET_TRISTAR45_MIB:
        log_warn("Invalid base OID passed to solarsnmp: %s" % str(oid))
        return None
    
    parts = oid[len(CRCNET_TRISTAR45_MIB):]
    if len(parts) < 1:
        # Base OID specified only
        if not getNext:
            # Invalid OID
            log_warn("Invalid OID passed to solarsnmp: %s" % str(oid))
            return None
        else:
            part = 1
        # Assume its the first request in a getNext stream
        oid = CRCNET_TRISTAR45_MIB + (part,)
        item = -1
    else:
        part = parts[0]
        if (part==23 or part==24):
            if len(parts)!=2:
                # Invalid OID 
                log_warn("Invalid OID passed to solarsnmp: %s" % str(oid))
                return None
            else:
                item = parts[1]
                if item < 1 or item > 16:
                    # Invalid OID 
                    log_warn("Invalid OID passed to solarsnmp: %s" % str(oid))
                    return None
        else:
            item = -1
        
        if getNext:
            # Advance
            if part==23 or part==24:
                # Handle bitfields specially
                if item==16:
                    # Move to next field
                    part+=1
                    if part==24:
                        item=1
                    else:
                        item=-1
                else:
                    # Move to next bit in this field
                    item+=1
            else:
                if part==25:
                    # End of MIB
                    return None
                part+=1
                if part==23:
                    item=1
                else:
                    item=-1
            oid = CRCNET_TRISTAR45_MIB + (part,)
            if item != -1:
                oid += (item,)

    if part == 1:
        # Battery Voltage
        return (oid, snmp.Integer("%d" % ts_battv()))
    elif part == 2:
        # Battery Sense Voltage
        return (oid, snmp.Integer("%d" % ts_battsensev()))
    elif part == 3:
        # Array/Load Voltage
        return (oid, snmp.Integer("%d" % ts_arrayv()))
    elif part == 4:
        # Battery Charge Current
        return (oid, snmp.Integer("%d" % ts_chargei()))
    elif part == 5:
        # Load Current
        return (oid, snmp.Integer("%d" % ts_loadi()))
    elif part == 6:
        # Battery Voltage (Slow)
        return (oid, snmp.Integer("%d" % ts_battvs()))
    elif part == 7:
        # Heatsink Temperature
        d=ts_readreg(TS_HSTEMP_DEG)
        return (oid, snmp.Integer("%d" % d))
    elif part == 8:
        # Battery Temperature
        d=ts_readreg(TS_BATTEMP_DEG)
        return (oid, snmp.Integer("%d" % d))
    elif part == 9:
        # Charge Regulator Reference Voltage
        return (oid, snmp.Integer("%d" % ts_refv()))
    elif part == 10:
        # Amp Hours Resetable
        return (oid, snmp.Integer("%d" % ts_amphours()))
    elif part == 11:
        # Amp Hours Total
        return (oid, snmp.Integer("%d" % ts_totalamphours()))
    elif part == 12:
        # Hour Meter
        return (oid, snmp.Integer("%d" % ts_hrmeter()))
    elif part == 13:
        # Control Mode
        return (oid, snmp.Integer(ts_readreg(TS_CONTROLMODE)))
    elif part == 14:
        # Control State
        return (oid, snmp.Integer(ts_readreg(TS_CONTROLSTATE)))
    elif part == 15:
        # PWM Duty Cycle
        return (oid, snmp.Integer("%d" % ts_pwm()))
    elif part == 16:
        # Days since last equalize
        return (oid, snmp.Integer(ts_readreg(TS_DSLEQU)))
    elif part == 17:
        # Days since last battery service
        return (oid, snmp.Integer(ts_readreg(TS_DSLBS_D)))
    elif part == 18:
        # Kilowatt Hours
        return (oid, snmp.Integer("%d" % ts_readreg(TS_KWH)))
    elif part == 19:
        # Minimum Battery Voltage
        return (oid, snmp.Integer("%d" % ts_minbv()))
    elif part == 20:
        # Maximum Battery Voltage
        return (oid, snmp.Integer("%d" % ts_maxbv()))
    elif part == 21:
        # Serial Number
        return (oid, snmp.OctetString("%s" % ts_serial()))
    elif part == 22:
        # Hardware Version
        return (oid, snmp.OctetString("%s" % ts_hwver()))
    elif part == 23:
        # Alarm
        i=(ts_readreg(TS_ALARMBITS_B_HI)&0xFFFF)<<16
        i|=(ts_readreg(TS_ALARMBITS_B_LO)&0xFFFF)
        pos = 2**(item-1)
        if (pos&i)==pos:
            # Set
            return (oid, snmp.Integer(1))
        else:
            return (oid, snmp.Integer(0))
    elif part == 24:
        # Fault
        i=ts_readreg(TS_FAULTBITS_B)
        pos = 2**(item-1)
        if (pos&i)==pos:
            # Set
            return (oid, snmp.Integer(1))
        else:
            return (oid, snmp.Integer(0))
    elif part == 25:
        # Dip Switch Settings
        i=ts_readreg(TS_DIPSWITCH_B)
        return (oid, snmp.Integer(i))
    
    log_warn("Invalid OID passed to solarsnmp: %s" % str(oid))
    return None
