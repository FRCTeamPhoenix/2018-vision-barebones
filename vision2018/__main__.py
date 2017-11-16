import cv2
from datetime import datetime
from capture import Capture
import zmq
from feed import Feed
from multiprocessing import Queue
import json
from collections import OrderedDict
import config_utils
import logging
import platform
import time
import sys
import os


def main():

    # OrderedDict is used so that the order of capture_props is preserved
    # (setting exposure_absolute before setting exposure_auto will cause an exception, so this is necessary)
    cfg = json.load(open(os.path.dirname(os.path.realpath(__file__)) + '/config.json'), object_pairs_hook=OrderedDict)

    # configure root logger
    logger = logging.getLogger()
    logger.setLevel(config_utils.to_log_level(cfg['log_level']))
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(name)-8s: %(message)s', datefmt='%Y-%m-%d %H:%M:%M')
    if cfg['log_to_console']:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    if cfg['log_to_file']:
        filename = 'log/' + datetime.now().strftime('%Y%m%d-%H:%M') + '.log'
        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # get logger for this file
    logger = logging.getLogger(__name__)
    logger.info('Using OpenCV version %s, Python version %s', cv2.__version__, platform.python_version())

    # is the source a webcam or a video file?
    source_is_webcam = cfg['capture_source'].startswith('/dev')
    logger.info('Initializing capture from source %s (%s)',
                cfg['capture_source'], 'webcam' if source_is_webcam else 'file')

    # continue trying to open camera until it works, maybe the cord was slightly unplugged or something?
    # it's important not to error irrecoverably during a competition
    while True:
        try:
            cap = Capture(source=cfg['capture_source'])
            break
        except IOError:
            if source_is_webcam:
                logger.exception('Opening capture failed!')
                logger.info("Retrying in 3 seconds...")
                time.sleep(3)
            else:
                # if a file isn't found, there's no point in continuing to retry, so we just exit
                logger.exception('File not found!')
                sys.exit(1)

    # set camera hardware properties only if the capture is a webcam
    # (setting the exposure on a video doesn't make sense, etc.)
    if source_is_webcam:
        logger.info('Setting V4L2 capture properties:')
        for prop in cfg['capture_props']:
            try:
                cap.set(config_utils.to_v4l2_prop(prop), cfg['capture_props'][prop])
                logger.info(' * %s: %d', prop, cfg['capture_props'][prop])
            except TypeError:
                logger.error('* Unable to set property %s to %d! skipping...', prop, cfg['capture_props'][prop])

    # initialize feed
    feed_queue = Queue()
    feed = Feed(feed_queue, port=cfg['feed_port'])
    if cfg['feed_enabled']:
        logger.info('Starting live feed')
        feed.start()

    # initialize comms
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    if cfg['comms_enabled']:
        logger.info('Initializing comms on socket %d', cfg['comms_port'])
        socket.bind('tcp://*:%d' % cfg['comms_port'])
    else:
        logger.warn('Comms not enabled!')

    # main targeting loop
    while True:
        frame = cv2.imdecode(cap.read(), cv2.CV_LOAD_IMAGE_COLOR)

        # calculate the average of the value (brightness) channel to get a dummy value so we can test comms
        average_brightness = cv2.mean(frame[2])[0]

        if cfg['comms_enabled']:
            msg = {
                'average_brightness': average_brightness
            }
            logger.debug('Sending message %s', msg)
            socket.send_json(msg)
        if cfg['feed_enabled']:
            feed_queue.put(frame)
        if cfg['gui_enabled']:
            cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info('Exiting main loop')
            break

    logger.info('Closing capture...')
    cap.close()
    if cfg['feed_enabled']:
        logger.info('Terminating live feed thread...')
        feed.terminate()
    logger.info('Done')


if __name__ == '__main__':
    main()
