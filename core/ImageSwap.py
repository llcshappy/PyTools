from PyQt5.QtWidgets import QToolBar, QAction, QActionGroup, QWidget, QHBoxLayout, QButtonGroup, QPushButton, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class ImageSelector(QWidget):
    """Widget for selecting active image in the comparison view"""
    selectionChanged = pyqtSignal(list)  # Signal emitted when selection changes, sends list of selected indices
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_indices = []  # Store selected indices (up to 2)
        self.max_images = 2  # Default is 2-image mode
        self.buttons = []
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def updateLayout(self, mode):
        """Update the selector buttons based on comparison mode"""
        # Clear existing buttons
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.buttons.clear()
        
        # Reset selections
        self.selected_indices = []
        
        # Store new mode
        self.max_images = mode
        
        # Create new buttons based on the mode
        for i in range(mode):
            button = ImageSelectorButton(i, self)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.onButtonClicked(idx, checked))
            self.layout().addWidget(button)
            self.buttons.append(button)
            
        # Update layouts
        self.layout().update()
        
    def onButtonClicked(self, index, checked):
        """Handle button click events with multi-selection (up to 2)"""
        if checked:
            # Add to selection if not already present
            if index not in self.selected_indices:
                # If already have 2 selected, remove the oldest one
                if len(self.selected_indices) >= 2:
                    oldest = self.selected_indices.pop(0)
                    self.buttons[oldest].setChecked(False)
                
                # Add the new selection
                self.selected_indices.append(index)
        else:
            # Remove from selection
            if index in self.selected_indices:
                self.selected_indices.remove(index)
                
        # Emit the signal with current selection
        self.selectionChanged.emit(self.selected_indices)
                
    def getSelectedIndices(self):
        """Get the currently selected image indices"""
        return self.selected_indices
        
    def clearSelection(self):
        """Clear all selections"""
        for i, btn in enumerate(self.buttons):
            btn.setChecked(False)
        self.selected_indices = []
        self.selectionChanged.emit(self.selected_indices)


class ImageSelectorButton(QPushButton):
    """Custom button for selecting images in the comparison tool"""
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setIcon(self.createImageIcon())
        self.setCheckable(True)
        self.setIconSize(QSize(24, 24))
        self.setFixedSize(32, 32)
        self.setToolTip(f"Select Image {index+1}")
        
        # Style the button
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #888;
                border-radius: 3px;
                padding: 2px;
                background-color: #f0f0f0;
            }
            QPushButton:checked {
                background-color: #3879d9;
                border: 1px solid #1c3b66;
            }
            QPushButton:hover:!checked {
                background-color: #e0e0e0;
            }
        """)
        
    def createImageIcon(self):
        """Create a custom icon representing an image panel"""
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw image panel representation
        panel_color = QColor(60, 120, 200, 200)
        painter.setPen(Qt.NoPen)
        painter.setBrush(panel_color)
        
        # Draw a rectangle with number
        painter.drawRect(2, 2, size-4, size-4)
        
        # Draw the index number
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, str(self.index + 1))
        
        painter.end()
        return QIcon(pixmap)


class ImageSwapHandler:
    """Handler for image swapping functionality"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.image_selector = ImageSelector()
        self.setup_toolbar()
        
        # Connect to layout change events
        self.main_window.twoImagesAction.triggered.connect(lambda: self.updateLayout(2))
        self.main_window.threeImagesAction.triggered.connect(lambda: self.updateLayout(3))
        self.main_window.fourImagesAction.triggered.connect(lambda: self.updateLayout(4))
        
        # Set initial state based on current mode
        self.updateLayout(self.main_window.comparison_mode)
        
        # Connect selection changed signal
        self.image_selector.selectionChanged.connect(self.onSelectionChanged)
        
    def setup_toolbar(self):
        """Add image selector to toolbar"""
        # Create toolbar for image selection
        self.select_toolbar = QToolBar("Image Selection")
        self.select_toolbar.setIconSize(QSize(24, 24))
        
        # Add a label for the selection toolbar
        label = QWidget()
        label_layout = QHBoxLayout(label)
        label_layout.setContentsMargins(5, 0, 5, 0)
        
        # Create styled label
        text_label = QLabel("Select Panels:")
        text_label.setStyleSheet("font-weight: bold; color: #444;")
        label_layout.addWidget(text_label)
        
        # Add the label to toolbar
        self.select_toolbar.addWidget(label)
        
        # Add the image selector
        self.select_toolbar.addWidget(self.image_selector)
        
        # Add space after buttons
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.select_toolbar.addWidget(spacer)
        
        # Add hint about space key
        hint_label = QLabel("Select two panels and press [Space] to swap them")
        hint_label.setStyleSheet("font-style: italic; color: #666;")
        self.select_toolbar.addWidget(hint_label)
        
        # Add the toolbar to main window
        self.main_window.addToolBar(self.select_toolbar)
        
    def updateLayout(self, mode):
        """Update layout when comparison mode changes"""
        self.image_selector.updateLayout(mode)
        
    def onSelectionChanged(self, indices):
        """Handle selection change"""
        # Store the active indices in main window
        if hasattr(self.main_window, 'active_image_index'):
            delattr(self.main_window, 'active_image_index')
        self.main_window.active_image_indices = indices
        
        # Update status bar with selection info
        if not indices:
            self.main_window.statusBar.showMessage('No panels selected', 2000)
        elif len(indices) == 1:
            self.main_window.statusBar.showMessage(f'Panel {indices[0]+1} selected. Select another to swap.', 2000)
        else:
            self.main_window.statusBar.showMessage(f'Panels {indices[0]+1} and {indices[1]+1} selected. Press Space to swap.', 2000)
        
    def handle_keypress(self, event):
        """Handle key press events for image swapping"""
        if event.key() == Qt.Key_Space:
            try:
                # Need at least 2 images loaded to swap
                loaded_images = [i for i, img in enumerate(self.main_window.images) if img is not None]
                if len(loaded_images) < 2:
                    self.main_window.statusBar.showMessage('Need at least 2 loaded images to swap', 3000)
                    return True
                
                # Get the selected indices
                selected_indices = self.image_selector.getSelectedIndices()
                
                # Need exactly 2 panels selected
                if len(selected_indices) != 2:
                    self.main_window.statusBar.showMessage('Select exactly 2 panels to swap', 3000)
                    return True
                
                # If we have a selection rectangle, remember it
                had_rect = not self.main_window.rect.isNull() and self.main_window.rect.width() > 0 and self.main_window.rect.height() > 0
                old_rect = self.main_window.rect
                
                # Perform the swap
                self.swap_images(selected_indices[0], selected_indices[1])
                
                # Restore rectangle if we had one
                if had_rect:
                    self.main_window.rect = old_rect
                
                # Update the display
                self.main_window.updatePixmap()
                self.main_window.statusBar.showMessage(f'Swapped images {selected_indices[0]+1} and {selected_indices[1]+1}', 3000)
                
                return True  # Event handled
                
            except Exception as e:
                # Catch any errors to prevent app from hanging
                import traceback
                print(f"Error swapping images: {e}")
                print(traceback.format_exc())
                self.main_window.statusBar.showMessage(f'Error swapping images: {str(e)}', 5000)
                return True  # Event handled
        
        return False  # Event not handled
    
    def swap_images(self, index1, index2):
        """Swap two images and their metadata"""
        if index1 == index2:
            return
            
        if index1 < 0 or index1 >= 4 or index2 < 0 or index2 >= 4:
            return
        
        # Make sure both indices have images loaded
        if not self.main_window.images[index1] or not self.main_window.images[index2]:
            self.main_window.statusBar.showMessage('Cannot swap - one or both panels have no image', 3000)
            return
        
        # Swap images and paths
        self.main_window.images[index1], self.main_window.images[index2] = \
            self.main_window.images[index2], self.main_window.images[index1]
            
        self.main_window.image_paths[index1], self.main_window.image_paths[index2] = \
            self.main_window.image_paths[index2], self.main_window.image_paths[index1] 