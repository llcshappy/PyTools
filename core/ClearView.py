import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QAction, QFileDialog, QWidget, QHBoxLayout, QStatusBar,
    QVBoxLayout, QGridLayout, QActionGroup, QSizePolicy, QToolBar, QMessageBox)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage, QCursor, QColor, QLinearGradient, QIcon, QDragEnterEvent, QFont
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QMimeData, QUrl

class DropLabel(QLabel):
    """Custom QLabel that accepts drag and drop operations"""
    def __init__(self, parent=None, index=0):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.index = index  # Store the image index this label corresponds to
        self.parent = parent

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Accept drag event if it contains image files
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.fileName().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                    event.acceptProposedAction()
                    return
        
    def dropEvent(self, event):
        # Process the dropped image file
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]  # Get the first URL
            if url.isLocalFile() and url.fileName().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                file_path = url.toLocalFile()
                
                # Pass the file to the parent to handle loading the image
                if self.parent:
                    self.parent.loadImageFromPath(file_path, self.index)
                
                event.acceptProposedAction()

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Multi-Image Comparison Tool')
        # List of images
        self.images = [None, None, None, None]  # Support up to 4 images
        self.image_paths = ["", "", "", ""]  # Store the image paths
        self.begin = None
        self.end = None
        self.rect = QRect()
        self.is_drawing = False
        self.can_draw_rect = False
        self.pixmap_rects = [QRect(), QRect(), QRect(), QRect()]  # To store actual image rects
        self.labels = []  # To store all image labels
        self.comparison_mode = 2  # Default: 2 images comparison
        self.show_image_info = True  # Default: show image information
        self.initUI()

    def initUI(self):
        # Create actions
        # File menu actions
        openActions = []
        for i in range(4):
            action = QAction(f'Upload Image {i+1}', self)
            action.triggered.connect(lambda checked, idx=i: self.openImage(idx))
            action.setShortcut(f'Ctrl+{i+1}')
            openActions.append(action)
        
        # Drawing tool action
        self.rectAction = QAction('Enable Rect Tool', self)
        self.rectAction.setCheckable(True)
        self.rectAction.triggered.connect(self.enableDrawing)
        self.rectAction.setShortcut('Ctrl+R')
        
        # Screenshot action
        screenshotAction = QAction('Screenshot', self)
        screenshotAction.triggered.connect(self.saveScreenshotToClipboard)
        screenshotAction.setShortcut('Ctrl+S')
        
        # Reset action
        resetAction = QAction('Reset All Images', self)
        resetAction.setIcon(self.createResetIcon())
        resetAction.triggered.connect(self.resetImages)
        resetAction.setShortcut('Ctrl+X')
        resetAction.setToolTip('Clear all loaded images')
        
        # Image info toggle action
        self.infoAction = QAction('Image Information', self)
        self.infoAction.setCheckable(True)
        self.infoAction.setChecked(self.show_image_info)
        self.infoAction.triggered.connect(self.toggleImageInfo)
        self.infoAction.setIcon(self.createInfoIcon())
        self.infoAction.setToolTip('Show/Hide Image Information')
        self.infoAction.setShortcut('Ctrl+I')

        # Create comparison mode actions with icons
        # Create layout icons programmatically
        self.twoImagesAction = QAction(self)
        self.twoImagesAction.setCheckable(True)
        self.twoImagesAction.setChecked(True)
        self.twoImagesAction.triggered.connect(lambda: self.setComparisonMode(2))
        self.twoImagesAction.setToolTip('2 Images Comparison')
        self.twoImagesAction.setIcon(self.createLayoutIcon(2))
        
        self.threeImagesAction = QAction(self)
        self.threeImagesAction.setCheckable(True)
        self.threeImagesAction.triggered.connect(lambda: self.setComparisonMode(3))
        self.threeImagesAction.setToolTip('3 Images Comparison')
        self.threeImagesAction.setIcon(self.createLayoutIcon(3))
        
        self.fourImagesAction = QAction(self)
        self.fourImagesAction.setCheckable(True)
        self.fourImagesAction.triggered.connect(lambda: self.setComparisonMode(4))
        self.fourImagesAction.setToolTip('4 Images Comparison')
        self.fourImagesAction.setIcon(self.createLayoutIcon(4))
        
        # Make the comparison actions exclusive
        viewActionGroup = QActionGroup(self)
        viewActionGroup.addAction(self.twoImagesAction)
        viewActionGroup.addAction(self.threeImagesAction)
        viewActionGroup.addAction(self.fourImagesAction)
        viewActionGroup.setExclusive(True)

        # Create menus
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        for action in openActions:
            fileMenu.addAction(action)
        fileMenu.addSeparator()
        fileMenu.addAction(resetAction)  # Add reset action to file menu as well
        
        editMenu = menubar.addMenu('&Edit')
        editMenu.addAction(self.rectAction)
        editMenu.addAction(self.infoAction)  # Add info toggle to edit menu
        
        toolMenu = menubar.addMenu('&Tool')
        toolMenu.addAction(screenshotAction)
        
        # Add toolbar for layout selection
        layoutToolbar = QToolBar("Layout Selection")
        layoutToolbar.setIconSize(QSize(32, 32))  # Set icon size
        self.addToolBar(layoutToolbar)
        
        # Add layout actions to toolbar
        layoutToolbar.addAction(self.twoImagesAction)
        layoutToolbar.addAction(self.threeImagesAction)
        layoutToolbar.addAction(self.fourImagesAction)
        
        # Add separator and other buttons
        layoutToolbar.addSeparator()
        layoutToolbar.addAction(resetAction)
        layoutToolbar.addAction(self.infoAction)

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Ready')

        # Set up the central widget 
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # Initialize image labels with drop support
        for i in range(4):
            label = DropLabel(self, i)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid grey; background-color: #f0f0f0;")
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.setMinimumSize(200, 200)  # Set a minimum size for the labels
            self.labels.append(label)
        
        # Set initial layout for 2 images
        self.setupLayout()
        
        # Enable drag and drop for the main window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Accept drag event if it contains image files
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.fileName().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        # Find which panel to load the image into
        for i in range(self.comparison_mode):
            if not self.images[i]:  # Find the first empty slot
                if event.mimeData().hasUrls():
                    url = event.mimeData().urls()[0]
                    if url.isLocalFile():
                        file_path = url.toLocalFile()
                        self.loadImageFromPath(file_path, i)
                        event.acceptProposedAction()
                        return
                
        # If all slots are filled, use the first one
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                self.loadImageFromPath(file_path, 0)
                event.acceptProposedAction()

    def loadImageFromPath(self, file_path, index):
        """Load an image from a file path into the specified index"""
        if index < 0 or index >= 4:
            return False
            
        image = QImage(file_path)
        if not image.isNull():
            self.images[index] = image
            self.image_paths[index] = file_path
            self.statusBar.showMessage(f'Image {index+1} loaded: {file_path}', 3000)
            
            # Reset rectangle when new images are loaded
            self.rect = QRect()
            self.updatePixmap()
            return True
        else:
            self.statusBar.showMessage(f'Failed to load image: {file_path}', 3000)
            return False

    def createLayoutIcon(self, mode):
        """Create a custom icon for the layout modes"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw layout representation
        pen = QPen(Qt.darkGray, 2)
        painter.setPen(pen)
        
        # Different layout based on mode
        if mode == 2:
            # Draw two rectangles side by side
            painter.drawRect(4, 10, 24, 44)
            painter.drawRect(36, 10, 24, 44)
        elif mode == 3:
            # Draw three rectangles side by side
            painter.drawRect(4, 10, 16, 44)
            painter.drawRect(24, 10, 16, 44)
            painter.drawRect(44, 10, 16, 44)
        else:  # mode == 4
            # Draw four rectangles in a grid
            painter.drawRect(4, 4, 24, 24)
            painter.drawRect(36, 4, 24, 24)
            painter.drawRect(4, 36, 24, 24)
            painter.drawRect(36, 36, 24, 24)
        
        painter.end()
        return QIcon(pixmap)

    def setupLayout(self):
        """Set up the layout based on the current comparison mode"""
        # Remove any existing layout
        if self.container.layout():
            # Clear existing layout safely
            old_layout = self.container.layout()
            # First remove all widgets from the layout
            for i in reversed(range(old_layout.count())):
                item = old_layout.itemAt(i)
                if item.widget():
                    item.widget().setParent(None)
            
            # Delete the old layout
            QWidget().setLayout(old_layout)
        
        # Create new layout based on comparison mode
        if self.comparison_mode == 2:
            # Two images side by side
            layout = QHBoxLayout()
            layout.addWidget(self.labels[0], 1)
            layout.addWidget(self.labels[1], 1)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
        elif self.comparison_mode == 3:
            # Three images in horizontal layout (side by side)
            layout = QHBoxLayout()
            layout.addWidget(self.labels[0], 1)
            layout.addWidget(self.labels[1], 1)
            layout.addWidget(self.labels[2], 1)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
        else:  # 4 images
            # Four images in a 2x2 grid
            layout = QGridLayout()
            layout.addWidget(self.labels[0], 0, 0, 1, 1)
            layout.addWidget(self.labels[1], 0, 1, 1, 1)
            layout.addWidget(self.labels[2], 1, 0, 1, 1)
            layout.addWidget(self.labels[3], 1, 1, 1, 1)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
        
        # Set label visibility based on the current mode
        for i in range(4):
            self.labels[i].setVisible(i < self.comparison_mode)
        
        # Apply the new layout
        self.container.setLayout(layout)
        
        # Ensure layout is applied immediately
        self.container.layout().activate()
        
        # Update status message
        self.statusBar.showMessage(f'{self.comparison_mode} images comparison mode activated', 3000)
        
        # Update all pixmaps
        self.updatePixmap()

    def setComparisonMode(self, mode):
        """Change the comparison mode (2, 3, or 4 images)"""
        if mode != self.comparison_mode and mode in [2, 3, 4]:
            self.comparison_mode = mode
            self.setupLayout()

    def saveScreenshotToClipboard(self):
        # Get the entire window content
        screenshot = QPixmap(self.size())
        screenshot.fill(Qt.transparent)
        painter = QPainter(screenshot)
        self.render(painter)
        painter.end()
        
        # Save to clipboard
        QApplication.clipboard().setPixmap(screenshot)
        self.statusBar.showMessage('Screenshot copied to clipboard', 3000)

    def openImage(self, index):
        """Open an image file for the specified panel index (0-3)"""
        if index < 0 or index >= 4:
            return
            
        imagePath, _ = QFileDialog.getOpenFileName(
            self, 
            f"Open Image for panel {index+1}", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if imagePath:
            self.loadImageFromPath(imagePath, index)

    def enableDrawing(self):
        self.can_draw_rect = self.rectAction.isChecked()
        if self.can_draw_rect:
            self.statusBar.showMessage('Rectangle drawing enabled - click and drag to draw', 3000)
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.statusBar.showMessage('Rectangle drawing disabled', 3000)

    def updatePixmap(self):
        """Update all image labels based on the current images"""
        for i in range(self.comparison_mode):
            if self.images[i]:
                self.drawBoxOnImage(self.images[i], self.labels[i], i)
            else:
                # Clear the label if no image
                self.labels[i].clear()
                self.labels[i].setText(f"Image {i+1}\nClick File > Upload Image {i+1}\nor drag & drop an image file here")
            
    def drawBoxOnImage(self, image, label, index):
        if not image:
            return
            
        # Get the label's size for scaling
        label_size = label.size()
        
        # Create a scaled pixmap that fits the label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            label_size.width(), 
            label_size.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Calculate the actual position and size of the scaled image in the label
        x_offset = (label_size.width() - scaled_pixmap.width()) // 2
        y_offset = (label_size.height() - scaled_pixmap.height()) // 2
        
        # Update the pixmap rect to reflect the actual image position in the label
        self.pixmap_rects[index] = QRect(
            x_offset, 
            y_offset, 
            scaled_pixmap.width(), 
            scaled_pixmap.height()
        )
        
        # Create a new pixmap the size of the label (not just the scaled image)
        temp_pixmap = QPixmap(label_size)
        # Use a more neutral, subtle background color
        temp_pixmap.fill(Qt.transparent)  # Start with transparent background
        
        painter = QPainter(temp_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smoother lines
        
        # Optional: Draw a subtle checkerboard pattern for transparent areas
        if True:  # Can be made into a preference option later
            # Draw checkerboard pattern for transparent background
            square_size = 10
            for x in range(0, label_size.width(), square_size*2):
                for y in range(0, label_size.height(), square_size*2):
                    painter.fillRect(x, y, square_size, square_size, Qt.lightGray)
                    painter.fillRect(x+square_size, y+square_size, square_size, square_size, Qt.lightGray)
        
        # Draw the scaled image centered in the label
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        
        # Add image information if enabled
        if self.show_image_info and self.image_paths[index]:
            info_text = self.getImageInfo(image, self.image_paths[index])
            
            # Create a semi-transparent background for the text
            info_rect = QRect(x_offset + 10, y_offset + 10, 250, 120)
            painter.fillRect(info_rect, QColor(0, 0, 0, 150))  # Semi-transparent black
            
            # Draw the text with a small shadow for better visibility
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            
            # Shadow
            painter.setPen(QPen(QColor(0, 0, 0, 180)))
            text_rect = info_rect.adjusted(6, 6, 0, 0)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, info_text)
            
            # Actual text
            painter.setPen(QPen(QColor(255, 255, 255, 230)))
            text_rect = info_rect.adjusted(5, 5, 0, 0)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, info_text)
        
        # If we have a valid rectangle, draw it with enhanced styling
        if not self.rect.isNull() and self.rect.width() > 0 and self.rect.height() > 0:
            # Scale the rectangle to match the displayed image size
            scaled_rect = QRect(
                int(self.rect.left() * scaled_pixmap.width() / image.width()) + x_offset,
                int(self.rect.top() * scaled_pixmap.height() / image.height()) + y_offset,
                int(self.rect.width() * scaled_pixmap.width() / image.width()),
                int(self.rect.height() * scaled_pixmap.height() / image.height())
            )
            
            # Create semi-transparent highlight effect
            highlight_color = QColor(0, 120, 215, 40)  # Blue with alpha
            painter.fillRect(scaled_rect, highlight_color)
            
            # Draw animated dashed border
            pen = QPen(QColor(0, 120, 215))  # Blue color for modern look
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(scaled_rect)
            
            # Draw outer glow effect
            glow_pen = QPen(QColor(255, 255, 255, 180))
            glow_pen.setWidth(1)
            painter.setPen(glow_pen)
            painter.drawRect(scaled_rect.adjusted(-2, -2, 2, 2))
            
            # Draw corner control points
            control_point_size = 6
            control_point_color = QColor(0, 120, 215)
            
            # Helper function to draw a control point
            def draw_control_point(x, y):
                painter.fillRect(
                    x - control_point_size//2, 
                    y - control_point_size//2, 
                    control_point_size, 
                    control_point_size, 
                    control_point_color
                )
                painter.setPen(QPen(Qt.white, 1))
                painter.drawRect(
                    x - control_point_size//2, 
                    y - control_point_size//2, 
                    control_point_size, 
                    control_point_size
                )
            
            # Draw control points at corners
            draw_control_point(scaled_rect.left(), scaled_rect.top())
            draw_control_point(scaled_rect.right(), scaled_rect.top())
            draw_control_point(scaled_rect.left(), scaled_rect.bottom())
            draw_control_point(scaled_rect.right(), scaled_rect.bottom())
            
            # Draw dimensions text
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            
            # Shadow for better visibility
            painter.setPen(QPen(Qt.black, 1))
            dimension_text = f"{self.rect.width()}×{self.rect.height()}"
            text_rect = scaled_rect.adjusted(1, 1, 0, 0)
            painter.drawText(text_rect, Qt.AlignTop | Qt.AlignLeft, dimension_text)
            
            # Actual text
            painter.setPen(QPen(Qt.white, 1))
            text_rect = scaled_rect.adjusted(0, 0, 0, 0)
            painter.drawText(text_rect, Qt.AlignTop | Qt.AlignLeft, dimension_text)
            
            # Get the cropped image with red border
            cropped_with_border_pixmap = self.drawCroppedImageWithBorder(image, self.rect, label)
            
            # Draw the cropped image in the top-right corner if it's valid
            if not cropped_with_border_pixmap.isNull():
                painter.drawPixmap(
                    temp_pixmap.width() - cropped_with_border_pixmap.width() - 10, 
                    10,  # Top margin
                    cropped_with_border_pixmap
                )
                
        painter.end()
        label.setPixmap(temp_pixmap)

    def drawCroppedImageWithBorder(self, original, rect, label):
        # Check if rect is valid
        if rect.width() <= 0 or rect.height() <= 0:
            return QPixmap()
        
        # First crop the image
        cropped = original.copy(rect)
        
        # Calculate a better preview size based on crop dimensions and label size
        label_width = label.width()
        label_height = label.height()
        
        # Determine the optimal preview size (not more than 30% of the label)
        max_preview_width = int(label_width * 0.3)
        max_preview_height = int(label_height * 0.3)
        
        # Calculate scaled dimensions while preserving aspect ratio
        aspect_ratio = rect.width() / rect.height()
        
        if aspect_ratio > 1:  # Wider than tall
            preview_width = min(rect.width(), max_preview_width)
            preview_height = int(preview_width / aspect_ratio)
            if preview_height > max_preview_height:
                preview_height = max_preview_height
                preview_width = int(preview_height * aspect_ratio)
        else:  # Taller than wide or square
            preview_height = min(rect.height(), max_preview_height)
            preview_width = int(preview_height * aspect_ratio)
            if preview_width > max_preview_width:
                preview_width = max_preview_width
                preview_height = int(preview_width / aspect_ratio)
        
        # Ensure minimum size
        preview_width = max(preview_width, 100)
        preview_height = max(preview_height, 100)
        
        # Define padding for more professional look
        padding = 8  # Padding around the image
        
        # Create the final image with shadow space
        shadow_blur = 12
        final_size = QSize(preview_width, preview_height) + QSize(padding * 2 + shadow_blur, padding * 2 + shadow_blur)
        final_image = QImage(final_size, QImage.Format_ARGB32)
        final_image.fill(Qt.transparent)
        
        # Scale the cropped image with high quality
        scaled_cropped = cropped.scaled(
            preview_width, 
            preview_height, 
            Qt.IgnoreAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Set up painter for final image
        painter = QPainter(final_image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Draw shadow (more sophisticated)
        shadow_color = QColor(0, 0, 0, 70)
        for i in range(shadow_blur):
            opacity = 0.5 - (i / shadow_blur / 2.0)
            painter.setPen(QPen(QColor(0, 0, 0, int(opacity * 255)), 1))
            painter.drawRoundedRect(
                shadow_blur - i + padding,
                shadow_blur - i + padding,
                preview_width + i*2,
                preview_height + i*2,
                3, 3
            )
        
        # Draw white background for the image (optional, gives a photo-like appearance)
        shadow_offset = int(shadow_blur/2)  # Convert to int
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawRect(
            padding + shadow_offset,
            padding + shadow_offset,
            preview_width,
            preview_height
        )
        
        # Draw image with slight inset
        painter.drawImage(
            padding + shadow_offset,
            padding + shadow_offset,
            scaled_cropped
        )
        
        # Draw elegant border
        border_gradient = QLinearGradient(
            padding + shadow_offset, 
            padding + shadow_offset, 
            padding + shadow_offset + preview_width, 
            padding + shadow_offset + preview_height
        )
        border_gradient.setColorAt(0, QColor(220, 20, 60))  # Crimson red
        border_gradient.setColorAt(1, QColor(139, 0, 0))    # Dark red
        
        painter.setPen(QPen(border_gradient, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(
            padding + shadow_offset,
            padding + shadow_offset,
            preview_width,
            preview_height
        )
        
        painter.end()
        
        # Return as pixmap
        return QPixmap.fromImage(final_image)

    def isPointInImage(self, point, index):
        """Check if a point is within the specified image area"""
        if index >= len(self.labels) or not self.labels[index].isVisible():
            return False
            
        global_pos = self.labels[index].mapToGlobal(QPoint(0, 0))
        local_pos = self.mapFromGlobal(global_pos)
        
        # Create a rect for the label in the main window coordinates
        label_rect = QRect(local_pos, self.labels[index].size())
        
        # Check if the point is within the label first
        if not label_rect.contains(point):
            return False
            
        # Convert to label coordinate space
        label_pos = self.labels[index].mapFromParent(point)
        
        # Check if the point is within the actual image area
        return self.pixmap_rects[index].contains(label_pos)

    def scalePoint(self, point, image, pixmap_rect):
        """Convert a point from label coordinates to image coordinates"""
        if pixmap_rect.width() == 0 or pixmap_rect.height() == 0 or not image:
            return 0, 0
            
        # Adjust point coordinates to be relative to the pixmap rect
        adjusted_x = point.x() - pixmap_rect.left()
        adjusted_y = point.y() - pixmap_rect.top()
        
        # Calculate the scale factors
        scale_x = image.width() / pixmap_rect.width()
        scale_y = image.height() / pixmap_rect.height()
        
        # Calculate the point in image coordinates
        image_x = int(adjusted_x * scale_x)
        image_y = int(adjusted_y * scale_y)
        
        # Ensure the point is within the image bounds
        image_x = max(0, min(image_x, image.width() - 1))
        image_y = max(0, min(image_y, image.height() - 1))
        
        return image_x, image_y

    def findImageAtPoint(self, point):
        """Find which image is under the cursor"""
        for i in range(self.comparison_mode):
            if self.images[i] and self.isPointInImage(point, i):
                return i
        return -1  # No image found

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.can_draw_rect:
            # Find which image is under the cursor
            image_index = self.findImageAtPoint(event.pos())
            if image_index >= 0:
                # Map to label coordinate space
                label_pos = self.labels[image_index].mapFromParent(event.pos())
                
                # Convert to image coordinate space
                image_x, image_y = self.scalePoint(label_pos, self.images[image_index], self.pixmap_rects[image_index])
                self.begin = QPoint(image_x, image_y)
                self.end = self.begin
                
                # Set up the rectangle
                self.rect.setTopLeft(self.begin)
                self.rect.setBottomRight(self.end)
                self.is_drawing = True
                self.updatePixmap()

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.can_draw_rect:
            # Find which image is under the cursor
            image_index = self.findImageAtPoint(event.pos())
            if image_index >= 0:
                # Map to label coordinate space
                label_pos = self.labels[image_index].mapFromParent(event.pos())
                
                # Convert to image coordinate space
                image_x, image_y = self.scalePoint(label_pos, self.images[image_index], self.pixmap_rects[image_index])
                self.end = QPoint(image_x, image_y)
                
                # Update the rectangle
                self.rect = QRect(self.begin, self.end).normalized()  # Normalize to handle drawing in any direction
                self.updatePixmap()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing and self.can_draw_rect:
            # Finalize the rectangle
            self.rect = QRect(self.begin, self.end).normalized()  # Normalize to handle drawing in any direction
            self.is_drawing = False
            
            # Show the rectangle dimensions in the status bar
            if self.rect.width() > 0 and self.rect.height() > 0:
                self.statusBar.showMessage(
                    f'Rectangle: ({self.rect.left()}, {self.rect.top()}) to ({self.rect.right()}, {self.rect.bottom()}) - ' +
                    f'Size: {self.rect.width()} x {self.rect.height()}', 
                    5000
                )
            
            self.updatePixmap()
            
    def resizeEvent(self, event):
        """Handle window resize events to update the display"""
        super().resizeEvent(event)
        self.updatePixmap()  # Update all images when window is resized

    def createResetIcon(self):
        """Create a reset icon with circular arrows"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw circular arrow 
        center_x, center_y = 32, 32
        radius = 24
        
        # Use a gradient for the arrow
        gradient = QLinearGradient(8, 8, 56, 56)
        gradient.setColorAt(0, QColor(30, 144, 255))  # Dodger blue
        gradient.setColorAt(1, QColor(0, 90, 170))    # Darker blue
        
        pen = QPen(gradient, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        
        # Draw 3/4 of a circle
        painter.drawArc(center_x - radius, center_y - radius, 
                       radius * 2, radius * 2, 
                       135 * 16, 270 * 16)  # Qt uses 1/16th of a degree
        
        # Draw the arrow head
        arrow_size = 10
        arrow_angle = 135  # Degrees
        arrow_rad = arrow_angle * 3.14159 / 180  # Convert to radians
        
        # Calculate arrow tip position
        tip_x = center_x + radius * 0.9 * 0.7071  # cos(45°)
        tip_y = center_y - radius * 0.9 * 0.7071  # sin(45°)
        
        # Calculate arrow head points
        arrow_p1_x = tip_x - arrow_size * 0.7071
        arrow_p1_y = tip_y - arrow_size * 0.7071
        arrow_p2_x = tip_x + arrow_size * 0.7071
        arrow_p2_y = tip_y + arrow_size * 0.7071
        
        # Draw arrowheads
        painter.drawLine(int(tip_x), int(tip_y), int(arrow_p1_x), int(tip_y)) 
        painter.drawLine(int(tip_x), int(tip_y), int(tip_x), int(arrow_p2_y))
        
        painter.end()
        return QIcon(pixmap)
        
    def resetImages(self):
        """Clear all loaded images after confirmation"""
        reply = QMessageBox.question(
            self, 
            'Reset Confirmation',
            'Are you sure you want to clear all images?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear all images and related data
            self.images = [None, None, None, None]
            self.image_paths = ["", "", "", ""]
            self.rect = QRect()
            self.begin = None
            self.end = None
            self.is_drawing = False
            
            # Update the UI
            self.updatePixmap()
            self.statusBar.showMessage('All images have been cleared', 3000)

    def createInfoIcon(self):
        """Create an icon for the info toggle button"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw a blue "i" in a circle
        painter.setPen(QPen(QColor(30, 144, 255), 2))  # Dodger blue
        painter.setBrush(QColor(220, 240, 255))
        painter.drawEllipse(8, 8, 48, 48)
        
        # Draw the "i"
        font = QFont("Arial", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRect(8, 8, 48, 48), Qt.AlignCenter, "i")
        
        painter.end()
        return QIcon(pixmap)
    
    def toggleImageInfo(self):
        """Toggle displaying of image information"""
        self.show_image_info = self.infoAction.isChecked()
        self.updatePixmap()  # Redraw all images with or without info
        
        if self.show_image_info:
            self.statusBar.showMessage('Image information enabled', 3000)
        else:
            self.statusBar.showMessage('Image information hidden', 3000)

    def getImageInfo(self, image, path):
        """Get formatted information about an image"""
        filename = os.path.basename(path)
        width = image.width()
        height = image.height()
        depth = image.depth()
        format_name = self.getImageFormatName(image.format())
        file_size = 0
        
        if path and os.path.exists(path):
            file_size = os.path.getsize(path) / 1024  # KB
            
        # Format the info text
        info = [
            f"File: {filename}",
            f"Size: {width}×{height} px",
            f"Format: {format_name}",
            f"Depth: {depth} bits",
        ]
        
        if file_size > 0:
            if file_size > 1024:
                info.append(f"File size: {file_size/1024:.1f} MB")
            else:
                info.append(f"File size: {file_size:.1f} KB")
                
        return "\n".join(info)
    
    def getImageFormatName(self, format_code):
        """Convert QImage format code to readable string"""
        formats = {
            QImage.Format_Invalid: "Invalid",
            QImage.Format_Mono: "Mono",
            QImage.Format_MonoLSB: "MonoLSB",
            QImage.Format_Indexed8: "Indexed8",
            QImage.Format_RGB32: "RGB32",
            QImage.Format_ARGB32: "ARGB32",
            QImage.Format_ARGB32_Premultiplied: "ARGB32_Premultiplied",
            QImage.Format_RGB16: "RGB16",
            QImage.Format_ARGB8565_Premultiplied: "ARGB8565_Premultiplied",
            QImage.Format_RGB666: "RGB666",
            QImage.Format_ARGB6666_Premultiplied: "ARGB6666_Premultiplied",
            QImage.Format_RGB555: "RGB555",
            QImage.Format_ARGB8555_Premultiplied: "ARGB8555_Premultiplied",
            QImage.Format_RGB888: "RGB888",
            QImage.Format_RGB444: "RGB444",
            QImage.Format_ARGB4444_Premultiplied: "ARGB4444_Premultiplied",
            QImage.Format_RGBX8888: "RGBX8888",
            QImage.Format_RGBA8888: "RGBA8888",
            QImage.Format_RGBA8888_Premultiplied: "RGBA8888_Premultiplied"
        }
        return formats.get(format_code, "Unknown")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.showMaximized()  # Show the window maximized
    sys.exit(app.exec_())
