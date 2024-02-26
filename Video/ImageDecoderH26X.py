import ffmpeg
import numpy as np

class ImageDecoderH26X:
    def __init__(self, cols, rows, video_codec):
        self.cols = cols
        self.rows = rows
        self.video_codec = video_codec

    def decode(self, h26x_frame):
        try:
            out, _ = (
                ffmpeg.input('pipe:0', format='{}'.format(self.video_codec), analyzeduration='1M', probesize='1M')
                .output('pipe:1', format='rawvideo', pix_fmt='yuv420p', s='{}x{}'.format(self.cols, self.rows))
                .run(input=h26x_frame, capture_stdout=True)
            )

            if (self.callback):
                self.callback(out)
            return out
        except ffmpeg.Error as e:
            print(e.stderr)
    
    def installCallback(self, callback):
        self.callback = callback
