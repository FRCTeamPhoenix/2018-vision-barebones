import logging
import v4l2

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

def to_v4l2_prop(prop):
    prop = prop.lower()
    if prop == 'brightness':
        return v4l2.V4L2_CID_BRIGHTNESS
    elif prop == 'contrast':
        return v4l2.V4L2_CID_CONTRAST
    elif prop == 'saturation':
        return v4l2.V4L2_CID_SATURATION
    elif prop == 'hue':
        return v4l2.V4L2_CID_HUE
    elif prop == 'white_balance_temperature_auto':
        return v4l2.V4L2_CID_AUTO_WHITE_BALANCE
    elif prop == 'gamma':
        return v4l2.V4L2_CID_GAMMA
    elif prop == 'white_balance_temperature':
        return v4l2.V4L2_CID_WHITE_BALANCE_TEMPERATURE
    elif prop == 'sharpness':
        return v4l2.V4L2_CID_SHARPNESS
    elif prop == 'backlight_compensation':
        return v4l2.V4L2_CID_BACKLIGHT_COMPENSATION
    elif prop == 'exposure_auto':
        return v4l2.V4L2_CID_EXPOSURE_AUTO
    elif prop == 'exposure_absolute':
        return v4l2.V4L2_CID_EXPOSURE_ABSOLUTE
    return None