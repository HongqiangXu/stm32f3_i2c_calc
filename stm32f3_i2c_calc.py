#!/usr/bin/env python2.7

"""
Displays usable I2C timing settings.
"""

import math

i2c_freq = float(raw_input('Enter desired I2C frequency (kHz): '))
i2c_freq *= 1e3

if i2c_freq <= 100e3:
    t_HD_DAT_max = 3.45e-6
    t_SU_DAT_min = 250e-9
    t_LOW_min = 4.7e-6
    t_HIGH_min = 4.0e-6
    print('Detected I2C standard mode')
elif i2c_freq <= 400e3:
    t_HD_DAT_max = 0.9e-6
    t_SU_DAT_min = 100e-9
    t_LOW_min = 1.3e-6
    t_HIGH_min = 0.6e-6
    print('Detected I2C fast mode')
elif i2c_freq <= 1000e3:
    t_HD_DAT_max = 0.45e-6
    t_SU_DAT_min = 50e-9
    t_LOW_min = 0.5e-6
    t_HIGH_min = 0.26e-6
    print('Detected I2C fast mode plus')
else:
    raise Exception('Detected I2C too damn fast mode')

# SCLL and SCLH are not equal to keep the minimum high and low times within I2C spec
SCLL_ratio = (t_LOW_min / (t_LOW_min + t_HIGH_min))
SCLH_ratio = (t_HIGH_min / (t_LOW_min + t_HIGH_min))

t_HD_DAT_min = 0

i2c_mhz = float(raw_input('Enter I2CCLK (MHz): '))
t_I2CCLK = 1.0 / (i2c_mhz * 1e6)

t_rise = float(raw_input('Enter max SCL/SDA rise time (ns): '))
t_rise *= 1e-9

t_fall = float(raw_input('Enter max SCL/SDA fall time (ns): '))
t_fall *= 1e-9

analog_filter = raw_input('Analog 50-260ns filter on? (y/n): ')
DFN = int(raw_input('Digital filter DFN value (0-15): '))

if DFN < 0 or DFN > 15:
    raise Exception('DFN out of valid range (0-15)')

if analog_filter.lower() == 'y':
    t_delay_min = 50e-9 # 50ns
    t_delay_max = 260e-9 # 260ns
else:
    t_delay_min = 0
    t_delay_max = 0

t_delay_min += (DFN + 2) * t_I2CCLK
t_delay_max += (DFN + 3) * t_I2CCLK

t_SYNC1_max = t_fall + t_delay_max
t_SYNC1_min = 0.0 + t_delay_min

t_SYNC2_max = t_rise + t_delay_max
t_SYNC2_min = 0.0 + t_delay_min

for PRESC in range(0, 16):
    SDADEL_min = (t_fall + t_HD_DAT_min - t_delay_min) / ((PRESC + 1) * t_I2CCLK)
    SDADEL_max = (t_HD_DAT_max - t_delay_max) / ((PRESC + 1) * t_I2CCLK)

    SCLDEL_min = (t_rise + t_SU_DAT_min) / ((PRESC + 1) * t_I2CCLK)
    

    print('PRESC = %d' % (PRESC))

    if math.ceil(SDADEL_min) > 15:
        print('    ***DONT USE THIS PRESC***')
    elif math.ceil(SDADEL_min) > math.floor(SDADEL_max):
        print('    ***DONT USE THIS PRESC***')
    elif math.ceil(SDADEL_min) == math.floor(SDADEL_max):
        print('    SDADEL = %d' % (math.ceil(SDADEL_min)))
    else:
        print('    %d <= SDADEL <= %d%s' % (math.ceil(SDADEL_min), math.floor(SDADEL_max), '' if math.floor(SDADEL_max) <= 15 else '(15 [only 4 bits for SDADEL]) ***PROBABLY SHOULDN\'T USE THIS PRESC***'))

    print('    %d <= SCLDEL' % (SCLDEL_min))
    print('')

    for i in range(0, 255 + 1):
        SCLL = int(i * SCLL_ratio + 0.5)
        SCLH = int(i * SCLH_ratio + 0.5)

        t_low_min = t_SYNC1_min + ((SCLL+1) * (PRESC+1) * t_I2CCLK)
        t_low_max = t_SYNC1_max + ((SCLL+1) * (PRESC+1) * t_I2CCLK)

        t_high_min = t_SYNC2_min + ((SCLH+1) * (PRESC+1) * t_I2CCLK)
        t_high_max = t_SYNC2_max + ((SCLH+1) * (PRESC+1) * t_I2CCLK)

        t_SCL_min = t_low_min + t_high_min
        t_SCL_max = t_low_max + t_high_max

        scl_freq_max = 1.0 / t_SCL_min
        scl_freq_min = 1.0 / t_SCL_max

        #TIMINGR = ((PRESC & 0x0F) << 28) | ((SCLDEL & 0x0F) << 20) | ((SDADEL & 0x0F) << 16) | ((SCLH & 0xFF) << 8) | ((SCLL & 0xFF) << 0)
        TIMINGR = ((PRESC & 0x0F) << 28) | ((SCLH & 0xFF) << 8) | ((SCLL & 0xFF) << 0)

        if t_low_min > t_LOW_min and t_high_min > t_HIGH_min and scl_freq_min > (i2c_freq * 0.85) and scl_freq_max < (i2c_freq * 1.15):
            print('        SCLL = %d, SCLH = %d' % (SCLL, SCLH))
            print('            SCL_freq_min (kHz): %.03f, SCL_freq_max (kHz): %0.3f' % (scl_freq_min * 1e-3, scl_freq_max * 1e-3))
            print('            t_LOW_min (us): %.04f, t_LOW_max (us): %0.4f' % (t_low_min * 1e6, t_low_max * 1e6))
            print('            t_HIGH_min (us): %.04f, t_HIGH_max (us): %0.4f' % (t_high_min * 1e6, t_high_max * 1e6))
            print('            I2Cx->TIMINGR = 0x%08X | ((your_SCLDEL & 0x0F) << 20) | ((your_SDADEL & 0x0F) << 16);' % (TIMINGR))
            print('')
            
        
    
    print('')
