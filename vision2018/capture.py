from v4l2 import *
from fcntl import ioctl
import mmap
import select
import time
import numpy as np
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

"""
This class has similar functionality to OpenCV's cv2.VideoCapture. It was rewritten here in Python due to the large
amount of added complexity involved with using the built-in VideoCapture class, namely because of the way that it
handles setting camera properties. On initialization, cv2.VideoCapture resets all available V4L2 properties to their
default values. Additionally, the version of OpenCV used in opencv4tegra contains a bug which does not allow users
to set the value of exposure_absolute using the cv2.VideoCapture class. The combination of these two things means
that using the built-in class would not allow us to set our camera's exposure at all, thus necessitating the rewrite
found in this file. This class accesses the camera through V4L2 directly and allows setting built-in V4L2 properties
using the property ID constants found in the v4l2 module. 
"""


class Capture:

    def __init__(self, source='/dev/video0', codec=V4L2_PIX_FMT_MJPEG):
        # path to the camera device or source video
        self.source = source

        # file descriptor of the device
        self.fd = open(source, 'rb+', buffering=0)

        # query capabilities
        cp = v4l2_capability()
        try:
            ioctl(self.fd, VIDIOC_QUERYCAP, cp)
        except:
            raise IOError('capabilities of device %s could not be read (%d)' % source)

        if not cp.capabilities & V4L2_CAP_VIDEO_CAPTURE:
            raise IOError('device %s does not support video capture' % source)

        if not cp.capabilities & V4L2_CAP_STREAMING:
            raise IOError('device %s does not support streaming' % source)

        # query format info
        formats = {}

        fmtdesc = v4l2_fmtdesc()
        frmsize = v4l2_frmsizeenum()
        frmival = v4l2_frmivalenum()
        fmtdesc.index = 0
        fmtdesc.type = V4L2_BUF_TYPE_VIDEO_CAPTURE

        while True:
            try:
                ioctl(self.fd, VIDIOC_ENUM_FMT, fmtdesc)
            except IOError:
                break
            else:
                formats[fmtdesc.pixelformat] = OrderedDict()
                frmsize.pixel_format = fmtdesc.pixelformat
                frmsize.index = 0
                while True:
                    try:
                        ioctl(self.fd, VIDIOC_ENUM_FRAMESIZES, frmsize)
                    except IOError:
                        break
                    else:
                        if frmsize.type == V4L2_FRMSIZE_TYPE_DISCRETE:
                            width, height = frmsize.discrete.width, frmsize.discrete.height
                        else:  # frmsize.type == V4L2_FRMSIZE_TYPE_STEPWISE
                            width, height = frmsize.stepwise.max_width, frmsize.stepwise.max_height

                        formats[fmtdesc.pixelformat][(width, height)] = []

                        frmival.pixel_format = fmtdesc.pixelformat
                        frmival.index = 0
                        frmival.width = width
                        frmival.height = height
                        while True:
                            try:
                                ioctl(self.fd, VIDIOC_ENUM_FRAMEINTERVALS, frmival)
                            except IOError:
                                break
                            else:
                                if frmival.type == V4L2_FRMIVAL_TYPE_DISCRETE:
                                    fps = frmival.discrete.denominator / frmival.discrete.numerator
                                else:  # frmival.type == V4L2_FRMIVAL_TYPE_STEPWISE
                                    fps = 1 / frmival.stepwise.max

                                formats[fmtdesc.pixelformat][(width, height)].append(fps)

                            frmival.index += 1

                        frmsize.index += 1
                fmtdesc.index += 1

        # set format
        self.__format = v4l2_format()
        self.__format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
        ioctl(self.fd, VIDIOC_G_FMT, self.__format)  # get current settings

        # modify current settings to use requested codec and resolution
        if codec in formats:
            if len(formats[codec]) < 1:
                raise IOError('device %s does appear to support any resolutions for pixformat %d', (source, codec))
            self.__format.fmt.pix.pixelformat = codec
            self.__format.fmt.pix.width = formats[codec].keys()[0][0]
            self.__format.fmt.pix.height = formats[codec].keys()[0][1]

            # set some properties for the user while we're here
            self.frame_width = formats[codec].keys()[0][0]
            self.frame_height = formats[codec].keys()[0][1]
            self.resolutions = []
            for k in formats[codec]:
                self.resolutions.append(k)

        else:
            raise IOError('device %s does not support codec %d', (source, codec))

        ioctl(self.fd, VIDIOC_S_FMT, self.__format)  # apply changed settings

        # init mmap video capture
        req = v4l2_requestbuffers()
        req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
        req.memory = V4L2_MEMORY_MMAP
        req.count = 2  # nr of buffer frames
        ioctl(self.fd, VIDIOC_REQBUFS, req)  # tell the driver that we want some buffers

        # retrieve buffers and queue them
        self.buffers = []
        for ind in range(req.count):
            # setup a buffer
            buf = v4l2_buffer()
            buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
            buf.memory = V4L2_MEMORY_MMAP
            buf.index = ind
            ioctl(self.fd, VIDIOC_QUERYBUF, buf)

            mm = mmap.mmap(self.fd.fileno(), buf.length, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                           offset=buf.m.offset)
            self.buffers.append(mm)

            # queue the buffer for capture
            ioctl(self.fd, VIDIOC_QBUF, buf)

        # prepare to begin streaming
        buf_type = v4l2_buf_type(V4L2_BUF_TYPE_VIDEO_CAPTURE)
        ioctl(self.fd, VIDIOC_STREAMON, buf_type)

        # wait for camera ready
        t0 = time.time()
        max_t = 1
        ready_to_read, ready_to_write, in_error = ([], [], [])
        while len(ready_to_read) == 0 and time.time() - t0 < max_t:
            ready_to_read, ready_to_write, in_error = select.select([self.fd], [], [], max_t)

        if not ready_to_read:
            raise IOError('device %s could not be opened for reading', source)

    def read(self):
        # get image from the driver queue
        buf = v4l2_buffer()
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
        buf.memory = V4L2_MEMORY_MMAP
        ioctl(self.fd, VIDIOC_DQBUF, buf)
        mm = self.buffers[buf.index]

        frame = np.frombuffer(mm, dtype=np.uint8)
        ioctl(self.fd, VIDIOC_QBUF, buf)  # requeue the buffer

        return frame

    def set(self, propid, value):
        ctrl = v4l2_control()
        ctrl.id = propid
        ctrl.value = value
        ioctl(self.fd, VIDIOC_S_CTRL, ctrl)

    def close(self):
        ioctl(self.fd, VIDIOC_STREAMOFF, v4l2_buf_type(V4L2_BUF_TYPE_VIDEO_CAPTURE))
        self.fd.close()
