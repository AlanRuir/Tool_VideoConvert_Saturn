import ffmpeg

class ImageEncoderH26X:
    def __init__(self, cols, rows, video_codec, bitrate):
        self.cols = cols
        self.rows = rows
        self.video_codec = video_codec
        self.bitrate = bitrate

    def encode(self, yuv420p_data):
        try:
            out, _ = (
                ffmpeg.input('pipe:0', format='rawvideo', pix_fmt='yuv420p', s='{}x{}'.format(self.cols, self.rows))
                .output('pipe:1', format='{}'.format(self.video_codec), pix_fmt='yuv420p', preset='ultrafast', threads=4, b='{}'.format(self.bitrate), g=1)
                .run(input=yuv420p_data, capture_stdout=True)
            )

            if self.callback:
                self.callback(out)

            return out
        except ffmpeg.Error as e:
            print(e.stderr)
    
    def installCallback(self, callback):
        self.callback = callback
