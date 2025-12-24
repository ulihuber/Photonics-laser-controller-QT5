# main_gui.py
import sys
import threading
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QPixmap
from Laser import Laser
import laserconstants as const

class LaserControllerGUI(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.laser = Laser(findCom = False,com = "com22", verbose = True, debug = True)
        self.update_timer = QTimer()
        #self.setup_timers()
        self.InUpdateFlag = 0
        self.diode_state = 0
        self.shutter_state = 0
        self.current = 10.0
        button_base_style = "QPushButton { padding: 10px; font-weight: bold; font-size: 14px; "
        self.button_base_style_red = button_base_style + "background-color: orangered; }"
        self.button_base_style_green = button_base_style + "background-color: lime; }"
        self.init_ui()
        self.on_reset()
        #QTimer.singleShot(100, self.main_loop)
        self.init_update_loop()


    def init_update_loop(self): 
        self.ui_timer = QTimer()        # Fast timer for UI responsiveness (e.g., 16ms = ~60 FPS)
        self.ui_timer.timeout.connect(self.update_ui_only)
        self.ui_timer.start(16) 


        self.data_timer = QTimer()       # Slower timer for data processing
        self.data_timer.timeout.connect(self.process_data)
        self.data_timer.start(100)  # Update data every second

    def update_ui_only(self):
        if hasattr(self, 'cached_data'):    
            self.update_display(self.cached_data)

        
    def init_ui(self):
        # Main window setup
        self.setWindowTitle('Laser Controller')
        self.setGeometry(100, 100, 400, 800)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. TOP BUTTONS
        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton('RESET')
        self.diode_btn = QPushButton('DIODE')
        self.shutter_btn = QPushButton('SHUTTER')
        
        # Style buttons (optional)
        #self.button_base_style = "QPushButton { padding: 10px; font-weight: bold; font-size: 14px; "
        self.reset_btn.setStyleSheet(self.button_base_style_red)  # + "background-color: orangered; }")
        self.diode_btn.setStyleSheet(self.button_base_style_red)  #+ "background-color: orangered; }")
        self.shutter_btn.setStyleSheet(self.button_base_style_red) #+ "background-color: orangered; }")
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.diode_btn)
        button_layout.addWidget(self.shutter_btn)
        main_layout.addLayout(button_layout)
        
        # 2. CURRENT DISPLAY (Big digits)
        current_frame = QFrame()
        # current_frame.setFrameStyle(QFrame.Box)
        current_layout = QHBoxLayout(current_frame)

        self.image_label = QLabel()
        pixmap = QPixmap("check.jpg")  # Pfad zu deinem Bild
        self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
                
        self.current_label = QLabel("Safe")
        self.current_label.width = 10
        font = QFont()
        font.setPointSize(32)
        font.setBold(True)
        self.current_label.setFont(font)

        power_layout = QHBoxLayout()
        current_layout.addWidget(self.image_label)
        current_layout.addWidget(self.current_label)
        
        main_layout.addWidget(current_frame)
        
        # 3. CURRENT SLIDER (10-28A)
        current_slider_layout = QVBoxLayout()

        # Create a horizontal layout for the label and value
        label_value_layout = QHBoxLayout()
        current_slider_label = QLabel("Diode set current:")
        current_slider_label.setFont(QFont("", 10, QFont.Bold))
        self.current_value_label = QLabel("10.0 A")
        self.current_value_label.setFont(QFont("", 10, QFont.Bold))
        label_value_layout.addWidget(current_slider_label)
        label_value_layout.addWidget(self.current_value_label)
        label_value_layout.addStretch()  # This pushes everything to the left

        
        current_slider_layout.addLayout(label_value_layout) # Add the horizontal layout to the vertical layout
        self.current_slider = QSlider(Qt.Horizontal) # Add the slider below
        self.current_slider.setRange(10, 28)  
        self.current_slider.setValue(10)  
        self.current_slider.valueChanged.connect(self.on_current_changed)

        current_slider_layout.addWidget(self.current_slider)
        main_layout.addLayout(current_slider_layout)

        # 4. FREQUENCY SLIDER (5-50 kHz)
        freq_slider_layout = QVBoxLayout()
        label_value_layout = QHBoxLayout()
        freq_slider_label = QLabel("Frequency:")
        freq_slider_label.setFont(QFont("", 10, QFont.Bold))
        self.freq_value_label = QLabel("5 kHz")
        self.freq_value_label.setFont(QFont("", 10, QFont.Bold))
        label_value_layout.addWidget(freq_slider_label)
        label_value_layout.addWidget(self.freq_value_label)
        label_value_layout.addStretch()  # This pushes everything to the left
        freq_slider_layout.addLayout(label_value_layout) # Add the horizontal layout to the vertical layout
        self.freq_slider = QSlider(Qt.Horizontal) # Add the slider below
        self.freq_slider.setRange(5, 50)  
        self.freq_slider.setValue(5)  
        self.freq_slider.valueChanged.connect(self.on_freq_changed)

        freq_slider_layout.addWidget(self.freq_slider)
        main_layout.addLayout(freq_slider_layout)
        
        # 5. TEMPERATURE DISPLAY
        temp_frame = QFrame()
        temp_frame.setFrameStyle(QFrame.Box)
        temp_layout = QGridLayout(temp_frame)
        
        self.temp_labels = {}
        temp_sensors = ["Diode", "SHG", "THG"]
        for i, sensor in enumerate(temp_sensors):
            temp_name_label = QLabel(f"{sensor}:")
            temp_name_label.setFont(QFont("", 10, QFont.Bold))
            temp_name_label.setFixedWidth(50)
            temp_layout.addWidget(temp_name_label, i, 0)
            temp_label = QLabel("--.- °C")
            temp_label.setFont(QFont("", 12, QFont.Bold))
            temp_layout.addWidget(temp_label, i, 1)
            self.temp_labels[sensor] = temp_label
        
        main_layout.addWidget(temp_frame)
        
        # 6. BOTTOM: ERRORS AND STATES
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        
        # Left: Errors (9 indicators)
        error_group = QGroupBox("Errors")
        error_layout = QVBoxLayout()
        
        self.error_widgets = []
        for i in range(16):  # First 9 errors from your list
            if not i in (4,5,9,10,11,13):
                widget = QWidget()
                error_label = QLabel(const.err_text[i]) #(f"Error {i}")
                error_label.setFont(QFont("", 10, QFont.Bold))
                error_label.setFixedWidth(150)
                error_label.setFrameStyle(QLabel.Box | QLabel.Plain)
                error_label.setStyleSheet(f"background-color: orangered;")
                error_layout.addWidget(error_label)
            self.error_widgets.append({
                        'ErrLabel': error_label,
                        'widget': widget
            })

        error_group.setLayout(error_layout)
        bottom_layout.addWidget(error_group)
        
        # Right: States (5 indicators)
        state_group = QGroupBox("States")
        state_layout = QVBoxLayout()
        
        self.state_widgets = []
        for i in range(8):  # First 5 states from your list
            if not i in (3,4,5):
                widget = QWidget()
                state_label = QLabel(const.state_text[i]) #(f"Error {i}")
                state_label.setFont(QFont("", 10, QFont.Bold))
                state_label.setFixedWidth(150)
                state_label.setFrameStyle(QLabel.Box | QLabel.Plain)
                state_label.setStyleSheet(f"background-color: orangered;")
                state_layout.addWidget(state_label)
            self.state_widgets.append({
                'StateLabel': state_label,
                'widget': widget
            })
            
        state_group.setLayout(state_layout)
        bottom_layout.addWidget(state_group)
        
        main_layout.addWidget(bottom_frame)
      
        # Connect button signals
        self.reset_btn.clicked.connect(self.on_reset)
        self.diode_btn.clicked.connect(self.toggle_diode)
        self.shutter_btn.clicked.connect(self.toggle_shutter)

############################################################################
    
    def process_data(self):
        
        self.InUpdateFlag += 1
        
        if self.InUpdateFlag == 1:
            self.updateSafety()
##            if (self.diode_state and self.shutter_state):
##                pixmap = QPixmap("Warning.gif")  # Pfad zu deinem Bild
##                self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
##            else:
##                pixmap = QPixmap("Check.jpg")  # Pfad zu deinem Bild
##                self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
##                #self.image_label.setVisible(False)
                       
        if self.InUpdateFlag == 2:
            print("in 2")
            if (self.diode_state and self.shutter_state):
                self.current = self.laser.GetCurrent()
                #print("----------------Current Return: ", self.current)
                self.current_label.setText(f"{self.current:.0f} A")
            else:
                self.current_label.setText("Safe") 
        
        if self.InUpdateFlag == 3:
            temps = self.laser.GetTemps()
            if len(temps) >= 3:
                self.temp_labels["Diode"].setText(f"{temps[0]:.1f} °C")
                self.temp_labels["SHG"].setText(f"{temps[1]:.1f} °C")
                self.temp_labels["THG"].setText(f"{temps[2]:.1f} °C")

        if self.InUpdateFlag == 4:        
            error_flags = self.laser.GetErrors()
            for i in range(16):
                if not i in (4,5,9,10,11,13):
                    has_error = (error_flags & (1 << i)) != 0
                    if has_error:
                        self.error_widgets[i]['ErrLabel'].setStyleSheet(f"background-color: orangered;")
                    else:
                        self.error_widgets[i]['ErrLabel'].setStyleSheet(f"background-color: lime;")

        if self.InUpdateFlag == 5:
            state_flags = self.laser.GetStates()
            for i in range(8):  
                if not i in (3,4,5):
                    is_set = (state_flags & (1 << i)) != 0
                    if is_set:
                        self.state_widgets[i]['StateLabel'].setStyleSheet(f"background-color: lime;")
                    else:
                        self.state_widgets[i]['StateLabel'].setStyleSheet(f"background-color: orangered;")                   
            self.InUpdateFlag = 0
   

    def on_current_changed(self, value):
        current = value
        self.current_value_label.setText(f"{current:.0f} A")
        
        # Send to laser (debounced or with delay to avoid flooding)
        if hasattr(self, '_current_timer'):
            self._current_timer.stop()
        
        self._current_timer = QTimer()
        self._current_timer.setSingleShot(True)
        self._current_timer.timeout.connect(lambda: self.send_current_to_laser(current))
        self._current_timer.start(300)  # Wait 300ms before sending
    
    def send_current_to_laser(self, current):
        print("send Laser current")
        try:
            self.laser.SetCurrent(current)
        except:
            QMessageBox.warning(self, "Error", "Failed to set laser current")
    
    def on_freq_changed(self, value):
        self.freq_value_label.setText(f"{value} kHz")
        
        # Debounce frequency changes
        if hasattr(self, '_freq_timer'):
            self._freq_timer.stop()
        
        self._freq_timer = QTimer()
        self._freq_timer.setSingleShot(True)
        self._freq_timer.timeout.connect(lambda: self.send_freq_to_laser(value))
        self._freq_timer.start(300)
    
    def send_freq_to_laser(self, freq):
        try:
            self.laser.SetFrequency(freq)  # Convert kHz to Hz
        except:
            QMessageBox.warning(self, "Error", "Failed to set laser frequency")

    def updateSafety(self):
        
        if (self.diode_state and self.shutter_state):
            pixmap = QPixmap("Warning.gif")  # Pfad zu deinem Bild
            self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
            self.current_label.setText(f"{self.current:.0f} A")
        else:
            pixmap = QPixmap("Check.jpg")  # Pfad zu deinem Bild
            self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
            self.current_label.setText("Safe")
        QApplication.processEvents()
            

    def on_reset(self):
        try:
            self.current_slider.setValue(10)
            self.send_current_to_laser(10)
            self.diode_state = 0
            self.laser.Switch("Diode", 0)
            self.diode_btn.setStyleSheet(self.button_base_style_red)
            self.state_widgets[0]['StateLabel'].setStyleSheet(f"background-color: orangered;")
            self.shutter_state = 0
            self.laser.Switch("Shutter", 0)
            self.shutter_btn.setStyleSheet(self.button_base_style_red)
            self.state_widgets[1]['StateLabel'].setStyleSheet(f"background-color: orangered;")
            self.reset_btn.setStyleSheet(self.button_base_style_green)
            self.updateSafety()
            QApplication.processEvents()
            self.laser.Switch("Reset", 1)
            #time.sleep(0.1)
            self.reset_btn.setStyleSheet(self.button_base_style_red)
            QApplication.processEvents()   
        except:
            QMessageBox.warning(self, "Error", "Reset failed")
            
    
    def toggle_diode(self):    # Toggle diode state
        try:
            if self.diode_state:
                self.diode_state = 0
                self.diode_btn.setStyleSheet(self.button_base_style_red)
                self.state_widgets[0]['StateLabel'].setStyleSheet(f"background-color: orangered;")
            else:
                self.diode_state = 1
                self.diode_btn.setStyleSheet(self.button_base_style_green)
                self.state_widgets[0]['StateLabel'].setStyleSheet(f"background-color: lime;")

            self.updateSafety()
               
            self.laser.Switch("Diode", self.diode_state)
            print("Toggle Diode", "on" if self.diode_state else "off" )
                
        except:
            QMessageBox.warning(self, "Error", "Diode control failed")
        
        

    def toggle_shutter(self):    # Toggle shutter state
        try:
            if self.shutter_state:
                if self.diode_state:
                    self.toggle_diode()
                self.shutter_state = 0
                self.shutter_btn.setStyleSheet(self.button_base_style_red)
                self.state_widgets[1]['StateLabel'].setStyleSheet(f"background-color: orangered;")
            else:
                if self.diode_state:
                    self.shutter_state = 1
                    self.shutter_btn.setStyleSheet(self.button_base_style_green)
                    self.state_widgets[1]['StateLabel'].setStyleSheet(f"background-color: lime;")
                     
            self.updateSafety()
                
            self.laser.Switch("Shutter", self.shutter_state)
            print("Toggle Shutter", "on" if self.shutter_state else "off" )
           
        except:
            QMessageBox.warning(self, "Error", "Shutter control failed")
        
    def closeEvent(self, event):
        # Cleanup on close
        self.ui_timer.stop()
        self.data_timer.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    gui = LaserControllerGUI()
    gui.show()
        
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
