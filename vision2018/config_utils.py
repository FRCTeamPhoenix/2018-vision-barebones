import logging

def to_log_level(level):
    level = level.lower()
    if level == 'critical':
        return logging.CRITICAL
    elif level == 'error':
        return logging.ERROR
    elif level == 'warning' or level == 'warn':
        return logging.WARNING
    elif level == 'info':
        return logging.INFO
    else:
        return logging.DEBUG

# these are V4L2 property IDs, e.g. V4L2_CID_BRIGHTNESS, etc.
# https://www.linuxtv.org/downloads/legacy/video4linux/API/V4L2_API/spec-single/v4l2.html#control
def to_v4l2_prop(prop):
    prop = prop.lower()
    if prop == 'brightness':
        return 9963776
    elif prop == 'contrast':
        return 9963777
    elif prop == 'saturation':
        return 9963778
    elif prop == 'hue':
        return 9963779
    elif prop == 'white_balance_temperature_auto':
        return 9963788
    elif prop == 'gamma':
        return 9963792
    elif prop == 'white_balance_temperature':
        return 9963802
    elif prop == 'sharpness':
        return 9963803
    elif prop == 'backlight_compensation':
        return 9963804
    elif prop == 'exposure_auto':
        return 10094849
    elif prop == 'exposure_absolute':
        return 10094850
    return None