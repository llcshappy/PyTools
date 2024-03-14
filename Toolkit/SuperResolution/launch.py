import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QAction, QFileDialog, QWidget, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt5.QtCore import Qt, QRect, QPoint, QSize

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Dual Image Rect and Display')
        self.image_left = None
        self.image_right = None
        self.begin = None
        self.end = None
        self.rect = QRect()
        self.is_drawing = False
        self.can_draw_rect = False
        self.initUI()

    def initUI(self):
        openLeftAction = QAction('Upload Left', self)
        openLeftAction.triggered.connect(lambda: self.openImage('left'))
        openRightAction = QAction('Upload Right', self)
        openRightAction.triggered.connect(lambda: self.openImage('right'))
        rectAction = QAction('Rect', self)
        rectAction.triggered.connect(self.enableDrawing)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openLeftAction)
        fileMenu.addAction(openRightAction)
        editMenu = menubar.addMenu('&Edit')
        editMenu.addAction(rectAction)

        self.label_left = QLabel(self)
        self.label_right = QLabel(self)

        layout = QHBoxLayout()
        layout.addWidget(self.label_left)
        layout.addWidget(self.label_right)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # 添加 Screenshot 动作
        screenshotAction = QAction('Screenshot', self)
        screenshotAction.triggered.connect(self.saveScreenshotToClipboard)
        
        # 创建 Tool 菜单并添加 Screenshot 动作
        toolMenu = menubar.addMenu('&Tool')
        toolMenu.addAction(screenshotAction)
        
    def saveScreenshotToClipboard(self):
        # 获取整个窗口的内容
        screenshot = QPixmap(self.size())
        # 定义 QPainter 对象，并将截图 QPixmap 作为画布
        painter = QPainter(screenshot)
        self.render(painter)  # 将窗口的内容渲染到画布上
        painter.end()  # 绘制结束
        QApplication.clipboard().setPixmap(screenshot)  # 将 QPixmap 存储到剪贴板
        

    def openImage(self, side):
        imagePath, _ = QFileDialog.getOpenFileName()
        if imagePath:
            image = QImage(imagePath)
            if side == 'left':
                self.image_left = image
            else:
                self.image_right = image
            self.updatePixmap()

    def enableDrawing(self):
        self.can_draw_rect = not self.can_draw_rect

    def updatePixmap(self):
        if self.image_left and self.image_right:
            self.drawBoxOnImage(self.image_left, self.label_left)
            self.drawBoxOnImage(self.image_right, self.label_right)
            
    def drawCroppedImageWithBorder(self, original, rect, label):
        # 首先进行裁剪操作
        cropped = original.copy(rect)
        # 然后根据裁剪图的尺寸，创建一个新的QImage，留出边框空间
        border_size = 2  # Define the size of the border
        bordered_image_size = cropped.size() + QSize(border_size * 2, border_size * 2)
        bordered_image = QImage(bordered_image_size, QImage.Format_ARGB32)
        bordered_image.fill(Qt.transparent)  # Start with a transparent image

        # 在带边框的图像上进行绘制操作
        painter = QPainter(bordered_image)
        # 画上红色的边框
        painter.setPen(QPen(Qt.red, border_size, Qt.SolidLine))
        painter.drawRect(0, 0, bordered_image.width() - 1, bordered_image.height() - 1)
        # 绘制裁剪的图像在边框内
        painter.drawImage(border_size, border_size, cropped)
        painter.end()

        # Scale the bordered image to fit label width (1/3 of original label width)
        scaled_bordered_image = QPixmap.fromImage(bordered_image).scaled(
            label.width() // 3, label.height() // 3, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Return the scaled bordered image as QPixmap
        return scaled_bordered_image

    def drawBoxOnImage(self, image, label):
        temp_pixmap = QPixmap.fromImage(image.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        painter = QPainter(temp_pixmap)

        if not self.rect.isNull():
            scaled_rect = QRect(
                int(self.rect.left() * temp_pixmap.width() / image.width()),
                int(self.rect.top() * temp_pixmap.height() / image.height()),
                int(self.rect.width() * temp_pixmap.width() / image.width()),
                int(self.rect.height() * temp_pixmap.height() / image.height())
            )

            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(scaled_rect)

            # Get the cropped image with the red border
            cropped_with_border_pixmap = self.drawCroppedImageWithBorder(image, self.rect, label)

            # Draw the cropped image with the border on the top-right
            painter.drawPixmap(temp_pixmap.width() - cropped_with_border_pixmap.width(), 0, cropped_with_border_pixmap)

        painter.end()
        label.setPixmap(temp_pixmap)

    def scalePoint(self, point, image, label):
        # 转换点从标签坐标系到图像的坐标系
        label_rect = label.rect()
        scale_x = image.width() / label_rect.width()
        scale_y = image.height() / label_rect.height()
        transposed_x = point.x() * scale_x
        transposed_y = point.y() * scale_y
        return int(transposed_x), int(transposed_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.can_draw_rect and self.image_left and self.image_right:
            pos = event.pos()
            # 将鼠标位置映射到label_left上，并适当缩放
            mapped_begin = self.label_left.mapFromParent(pos)
            self.begin = QPoint(*self.scalePoint(mapped_begin, self.image_left, self.label_left))
            self.end = self.begin
            self.rect.setTopLeft(self.begin)
            self.rect.setBottomRight(self.end)
            self.is_drawing = True
            self.updatePixmap()

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.can_draw_rect:
            pos = event.pos()
            # 将鼠标位置映射到label_left上，并适当缩放
            mapped_end = self.label_left.mapFromParent(pos)
            self.end = QPoint(*self.scalePoint(mapped_end, self.image_left, self.label_left))
            self.rect.setBottomRight(self.end)
            self.updatePixmap()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.can_draw_rect:
            pos = event.pos()
            # 将鼠标位置映射到label_left上，并适当缩放
            mapped_end = self.label_left.mapFromParent(pos)
            self.end = QPoint(*self.scalePoint(mapped_end, self.image_left, self.label_left))
            self.rect.setBottomRight(self.end)
            self.is_drawing = False
            self.updatePixmap()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.showMaximized()  # Show the window maximized
    sys.exit(app.exec_())
