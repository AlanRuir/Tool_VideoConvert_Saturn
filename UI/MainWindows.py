import av
import ffmpeg
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpinBox, QComboBox, QHBoxLayout, QMessageBox, QFileDialog, QProgressBar, QDesktopWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QTime
from Video.ImageEncoderH26X import ImageEncoderH26X
from Video.ImageDecoderH26X import ImageDecoderH26X

class Worker(QThread):
    finished = pyqtSignal()

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        self.func(*self.args, **self.kwargs)
        self.finished.emit()

class MainWindows(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        icon = QIcon('icon.png')  # 替换为你的图标文件路径
        self.setWindowIcon(icon)
        self.thread_pool = []

    def MP4toYUV420P(self):
        if (self.process_name != ''):
            QMessageBox.warning(self, '警告', '正在进行' + self.process_name + ', 请稍后再试')
            return
        self.mp4_file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'MP4 Files (*.mp4)')
        if self.mp4_file_name == '':
            return
        self.yuv_file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'YUV420P Files (*.yuv)')
        if self.yuv_file_name == '':
            return
        
        self.process_name = '转换'
        self.process_label.setText(self.process_name + '中: ')
        self.process_label.setHidden(False)
        self.progress_bar.setHidden(False)
        self.layout.invalidate()
        self.layout.update()

        self.start_time = QTime.currentTime()  # 记录开始时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)  # 每隔100毫秒更新一次进度条

        worker = Worker(self.MP4toYUV420PThread)
        worker.finished.connect(self.MP4toYUV420PFinished)
        worker.start()
        self.thread_pool.append(worker)
    
    def MP4toYUV420PThread(self):
        if self.mp4_file_name == '':
            return
        if self.yuv_file_name == '':
            return
        ffmpeg.input(self.mp4_file_name).output(self.yuv_file_name, format='rawvideo', pix_fmt='yuv420p', s='3840x2160').run()

    def ShowEncodeWidget(self, encode_type):
        if (self.process_name != ''):
            QMessageBox.warning(self, '警告', '正在进行' + self.process_name + ', 请稍后再试')
            return
        self.input_file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'YUV420P Files (*.yuv)')
        if encode_type == 'h264':
            self.encode_type = 'h264'
        else:
            self.encode_type = 'h265'
        if self.input_file_name == '':
            return

        self.width_label.setHidden(False)
        self.width_spinbox.setHidden(False)
        self.height_label.setHidden(False)
        self.height_spinbox.setHidden(False)
        self.quality_label.setHidden(False)
        self.quality_combobox.setHidden(False)
        self.encode_button.setHidden(False)
        self.layout.invalidate()
        self.layout.update()

    def ShowDecodeWidget(self, encode_type):
        if (self.process_name != ''):
            QMessageBox.warning(self, '警告', '正在进行' + self.process_name + ', 请稍后再试')
            return
        if encode_type == 'h264':
            self.encode_type = 'h264'
            self.input_file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'H.264 Files (*.264)')
        else:
            self.encode_type = 'h265'
            self.input_file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'H.265 Files (*.265)')
        if self.input_file_name == '':
            return
        
        self.width_label.setHidden(False)
        self.width_spinbox.setHidden(False)
        self.height_label.setHidden(False)
        self.height_spinbox.setHidden(False)
        self.decode_button.setHidden(False)
        self.layout.invalidate()
        self.layout.update()

    def YUV420PtoH26X(self):
        self.width_label.setHidden(True)
        self.width_spinbox.setHidden(True)
        self.height_label.setHidden(True)
        self.height_spinbox.setHidden(True)
        self.quality_label.setHidden(True)
        self.quality_combobox.setHidden(True)
        self.encode_button.setHidden(True)

        self.current_position_x = self.pos().x()
        self.current_position_y = self.pos().y()
        self.adjustSize()
        self.setGeometry(self.current_position_x, self.current_position_y, 400, 200)        
        self.layout.invalidate()
        self.layout.update()

        self.cols = self.width_spinbox.value()
        self.rows = self.height_spinbox.value()
        use_quality = self.quality_combobox.currentText()
        if use_quality == '超清':
            self.quality = '40M'
        elif use_quality == '高清':
            self.quality = '20M'
        elif use_quality == '清晰':
            self.quality = '10M'
        if self.encode_type == 'h264':
            self.h264_file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'H.264 Files (*.264)')
            self.encoder = ImageEncoderH26X(self.width_spinbox.value(), self.height_spinbox.value(), 'h264', self.quality)      # 创建H.264编码器
            self.encoder.installCallback(self.SaveH264Frame)                                                                    # 设置编码器的回调函数
        else:
            self.h265_file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'H.265 Files (*.265)')
            self.encoder = ImageEncoderH26X(self.width_spinbox.value(), self.height_spinbox.value(), 'hevc', self.quality)      # 创建H.265编码器
            self.encoder.installCallback(self.SaveH265Frame)                                                                    # 设置编码器的回调函数

        self.process_name = '编码'
        self.process_label.setText(self.process_name + '中: ')
        self.process_label.setHidden(False)
        self.progress_bar.setHidden(False)
        self.layout.invalidate()
        self.layout.update()

        self.start_time = QTime.currentTime()                               # 记录开始时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)                                               # 每隔100毫秒更新一次进度条
        
        worker = Worker(self.YUV420PtoH26XThread)
        worker.finished.connect(self.YUV420PtoH26XFinished)
        worker.start()
        self.thread_pool.append(worker)

    def YUV420PtoH26XThread(self):
        if self.input_file_name == '':                                      # 检查输入文件是否为空
            return
        with open(self.input_file_name, 'rb') as yuv_file:                  # 打开输入文件
            frame_data = yuv_file.read(self.cols * self.rows * 3 // 2)      # 读取第一帧数据
            frame_index = 0
            while frame_data:
                self.encoder.encode(frame_data)                             # 编码
                frame_index += 1
                frame_data = yuv_file.read(self.cols * self.rows * 3 // 2)  # 读取下一帧数据

    def H26XtoYUV420P(self):
        self.width_label.setHidden(True)
        self.width_spinbox.setHidden(True)
        self.height_label.setHidden(True)
        self.height_spinbox.setHidden(True)
        self.decode_button.setHidden(True)

        self.current_position_x = self.pos().x()
        self.current_position_y = self.pos().y()
        self.adjustSize()
        self.setGeometry(self.current_position_x, self.current_position_y, 400, 200)        
        self.layout.invalidate()
        self.layout.update()

        self.output_file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'YUV420P Files (*.yuv)')
        if self.encode_type == 'h264':
            self.decoder = ImageDecoderH26X(self.width_spinbox.value(), self.height_spinbox.value(), 'h264')
        else:
            self.decoder = ImageDecoderH26X(self.width_spinbox.value(), self.height_spinbox.value(), 'hevc')
        self.decoder.installCallback(self.SaveYUV420PFrame)

        self.process_name = '解码'
        self.process_label.setText(self.process_name + '中: ')
        self.process_label.setHidden(False)
        self.progress_bar.setHidden(False)
        self.layout.invalidate()
        self.layout.update()

        self.start_time = QTime.currentTime()  # 记录开始时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)  # 每隔100毫秒更新一次进度条

        worker = Worker(self.H26XtoYUV420PThread)
        worker.finished.connect(self.H26XtoYUV420PFinished)
        worker.start()
        self.thread_pool.append(worker)
        
    def H26XtoYUV420PThread(self):
        if self.input_file_name == '':
            return
        h26x_file = av.open(self.input_file_name)
        for packet in h26x_file.demux():
            self.decoder.decode(packet.to_bytes())

    def SaveH264Frame(self, encode_frame):
        if self.h264_file_name == '':
            return
        with open(self.h264_file_name, 'ab') as file:
            file.write(encode_frame)

    def SaveH265Frame(self, encode_frame):
        if self.h265_file_name == '':
            return
        with open(self.h265_file_name, 'ab') as file:
            file.write(encode_frame)

    def SaveYUV420PFrame(self, decode_frame):
        if self.output_file_name == '':
            return
        with open(self.output_file_name, 'ab') as file:
            file.write(decode_frame)

    def MP4toYUV420PFinished(self):
        self.timer.stop()
        self.progress_bar.setValue(100)
        self.process_label.setHidden(True)
        self.progress_bar.setHidden(True)
        self.process_name = ''
        self.adjustSize()
        self.current_position_x = self.pos().x()
        self.current_position_y = self.pos().y()
        self.setGeometry(self.current_position_x, self.current_position_y, 400, 200)
        self.layout.invalidate()
        self.layout.update()
        QMessageBox.information(self, '提示', '转换完成')
        print('转换完成')

    def YUV420PtoH26XFinished(self):
        self.timer.stop()
        self.progress_bar.setValue(100)
        self.process_label.setHidden(True)
        self.progress_bar.setHidden(True)
        self.process_name = ''
        self.adjustSize()
        self.current_position_x = self.pos().x()
        self.current_position_y = self.pos().y()
        self.setGeometry(self.current_position_x, self.current_position_y, 400, 200)
        self.layout.invalidate()
        self.layout.update()
        QMessageBox.information(self, '提示', '编码完成')
        print('编码完成')

    def H26XtoYUV420PFinished(self):
        self.timer.stop()
        self.progress_bar.setValue(100)
        self.process_label.setHidden(True)
        self.progress_bar.setHidden(True)
        self.process_name = ''
        self.adjustSize()
        self.current_position_x = self.pos().x()
        self.current_position_y = self.pos().y()
        self.setGeometry(self.current_position_x, self.current_position_y, 400, 200)
        self.layout.invalidate()
        self.layout.update()
        QMessageBox.information(self, '提示', '解码完成')
        print('解码完成')

    def closeEvent(self, event):
        for thread in self.thread_pool:
            thread.stop()
            thread.quit()
            thread.wait()
        event.accept()

    def updateProgress(self):
        elapsed_time = self.start_time.elapsed() / 1000  # 已经过的时间，单位：秒

        # 使用指数函数模拟进度条速度的变化
        progress = 100 * (1 - math.exp(-elapsed_time / 30))  # 可以调整指数的参数来控制速度的变化,越大越慢

        if progress >= 99:
            progress = 99
            # self.timer.stop()

        self.progress_bar.setValue(int(progress))

    def initUI(self):
        self.setWindowTitle('视频编解码工具')
        
        # 获取屏幕的尺寸
        screen = QDesktopWidget().screenGeometry()
        screen_width, screen_height = screen.width(), screen.height()

        # 计算窗口在屏幕中心的位置
        self.current_position_x = int((screen_width - self.width()) / 2)
        self.current_position_y = int((screen_height - self.height()) / 2)

        self.process_name = ''
        self.process_label = QLabel(self.process_name)
        self.progress_bar = QProgressBar()
        mp4_to_yuv420p_btn = QPushButton('MP4转YUV420P')
        yuv420p_to_h264_btn = QPushButton('YUV420P转H.264')
        yuv420p_to_h265_btn = QPushButton('YUV420P转H.265')
        h264_to_yuv420p_btn = QPushButton('H.264转YUV420P')
        h265_to_yuv420p_btn = QPushButton('H.265转YUV420P')

        self.width_label = QLabel('宽度:')
        self.width_label.setFixedWidth(self.width_label.sizeHint().width())
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setMinimum(1)
        self.width_spinbox.setMaximum(3840)
        self.width_spinbox.setValue(3840)

        self.height_label = QLabel('高度:')
        self.height_label.setFixedWidth(self.height_label.sizeHint().width())
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setMinimum(1)
        self.height_spinbox.setMaximum(2160)
        self.height_spinbox.setValue(2160)

        self.quality_label = QLabel('画质:')
        self.quality_label.setFixedWidth(self.quality_label.sizeHint().width())
        self.quality_combobox = QComboBox()
        self.quality_combobox.addItems(['超清', '高清', '清晰'])

        self.encode_button = QPushButton('编码')
        self.decode_button = QPushButton('解码')

        self.layout = QVBoxLayout()
        self.process_layout = QHBoxLayout()
        self.process_layout.addWidget(self.process_label)
        self.process_layout.addWidget(self.progress_bar)
        self.layout.addLayout(self.process_layout)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(mp4_to_yuv420p_btn)
        self.layout.addWidget(yuv420p_to_h264_btn)
        self.layout.addWidget(yuv420p_to_h265_btn)
        self.layout.addWidget(h264_to_yuv420p_btn)
        self.layout.addWidget(h265_to_yuv420p_btn)
        self.width_layout = QHBoxLayout()
        self.width_layout.addWidget(self.width_label)
        self.width_layout.addWidget(self.width_spinbox)
        self.layout.addLayout(self.width_layout)
        self.height_layout = QHBoxLayout()
        self.height_layout.addWidget(self.height_label)
        self.height_layout.addWidget(self.height_spinbox)
        self.layout.addLayout(self.height_layout)
        self.quality_layout = QHBoxLayout()
        self.quality_layout.addWidget(self.quality_label)
        self.quality_layout.addWidget(self.quality_combobox)
        self.layout.addLayout(self.quality_layout)
        self.layout.addWidget(self.encode_button)
        self.layout.addWidget(self.decode_button)

        self.process_label.setHidden(True)
        self.progress_bar.setHidden(True)
        self.width_label.setHidden(True)
        self.width_spinbox.setHidden(True)
        self.height_label.setHidden(True)
        self.height_spinbox.setHidden(True)
        self.quality_label.setHidden(True)
        self.quality_combobox.setHidden(True)
        self.encode_button.setHidden(True)
        self.decode_button.setHidden(True)

        self.setLayout(self.layout)

        mp4_to_yuv420p_btn.clicked.connect(self.MP4toYUV420P)
        yuv420p_to_h264_btn.clicked.connect(lambda: self.ShowEncodeWidget('h264'))
        yuv420p_to_h265_btn.clicked.connect(lambda: self.ShowEncodeWidget('h265'))
        h264_to_yuv420p_btn.clicked.connect(lambda: self.ShowDecodeWidget('h264'))
        h265_to_yuv420p_btn.clicked.connect(lambda: self.ShowDecodeWidget('h265'))
        self.encode_button.clicked.connect(self.YUV420PtoH26X)
        self.decode_button.clicked.connect(self.H26XtoYUV420P)

        self.setStyleSheet('''
        QWidget {
            background-color: #f0f0f0;
        }

        QLabel {
            color: #333;
            font-size: 14px;
        }

        QSpinBox, QComboBox {
            background-color: white;
            border: 1px solid #ccc;
            padding: 5px;
            font-size: 14px;
        }
                           
        QSpinBox::up-button, QSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: right;
            width: 0px;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right;
            width: 0px;
        }

        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            margin: 4px 2px;
            border-radius: 5px;
        }

        QPushButton:hover {
            background-color: #45a049;
        }
                           
        QMessageBox {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            min-width: 150px;
            max-width: 150px;
        }

        QMessageBox QLabel {
            color: black;
            font-size: 14px;
            padding: 10px 20px;
        }

        QMessageBox QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            margin: 4px 2px;
            border-radius: 5px;
        }

        QMessageBox QPushButton:hover {
            background-color: #45a049;
        }
        
        QProgressBar {
            border: none;
            background-color: transparent;
            height: 1px; /* 设置进度条的高度 */
            text-align: center; /* 文字居中 */
        }

        QProgressBar::chunk {
            background-color: #4CAF50; /* 设置进度条的颜色 */
            width: 1px; /* 设置进度条的宽度 */
            color: white; /* 设置文字颜色为白色 */
        }
        ''')

        # 设置窗口大小
        self.setGeometry(self.current_position_x, self.current_position_y, 400, 200)
        # 显示窗口
        self.show()

