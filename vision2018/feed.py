from flask import Flask, render_template, Response
from multiprocessing import Process
import threading
import time
import cv2

class Feed(Process):

    def __init__(self, queue, port=5000):
        super(Feed, self).__init__()
        self.queue = queue
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'index', self.__index)
        self.app.add_url_rule('/video_feed', 'video_feed', self.__video_feed)
        self.frame = None
        self.port = port

    def run(self):
        threading.Thread(target=self.__consume_frames).start()
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)

    def __consume_frames(self):
        while True:
            frame = self.queue.get()
            self.frame = cv2.imencode('.jpg', frame)[1].tostring()

    def __index(self):
        return render_template('./index.html')

    def __video_feed(self):
        def gen():
            while True:
                time.sleep(0.01)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + self.frame + b'\r\n\r\n')

        return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
