import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, QMessageBox, QScrollArea,QHBoxLayout
import os

class UdevRuleGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.rules_file = '/etc/udev/rules.d/batman.rules'
        self.rules = self.read_rules()
        self.usb_devices = self.get_usb_devices()
        self.name_inputs = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Udev Rule Setup')
        self.setStyleSheet('background-color: #f0f0f0;')  # Set background color

        self.old_devices_label = QLabel('Saved Devices')
        self.old_devices_label.setStyleSheet('font-weight: bold;')  # Set bold font
        self.layout = QVBoxLayout()

        # Create a scroll area for the existing rules
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout()

        self.populate_rules()

        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)

        self.layout.addWidget(self.old_devices_label)
        self.layout.addWidget(self.scroll_area)

        # Add the section for new devices
        self.new_devices_label = QLabel('New Devices')
        self.new_devices_label.setStyleSheet('font-weight: bold;')  # Set bold font
        self.new_devices_layout = QGridLayout()
        self.new_device_inputs = []

        self.populate_new_devices()

        self.layout.addWidget(self.new_devices_label)
        self.layout.addLayout(self.new_devices_layout)

        # Add the update and finish buttons
        self.button_layout = QHBoxLayout()  # Use horizontal layout for buttons

        self.update_button = QPushButton('Update All')
        self.update_button.setStyleSheet('background-color: #4CAF50; color: white;')  # Green button
        self.update_button.clicked.connect(self.update_all_rules)
        self.button_layout.addWidget(self.update_button)

        self.finish_button = QPushButton('Finish')
        self.finish_button.setStyleSheet('background-color: #f44336; color: white;')  # Red button
        self.finish_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.finish_button)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def get_usb_devices(self):
        usb_devices = {}
        try:
            lsusb_output = subprocess.check_output(['lsusb']).decode('utf-8')
            for line in lsusb_output.split('\n'):
                if line:
                    parts = line.split()
                    bus = parts[1]
                    device = parts[3].rstrip(':')
                    vendor_id, product_id = parts[5].split(':')
                    device_name = ' '.join(parts[6:])
                    usb_devices[(vendor_id, product_id)] = device_name
        except subprocess.CalledProcessError:
            pass
        return usb_devices

    def read_rules(self):
        rules = []
        try:
            with open(self.rules_file, 'r') as f:
                for line in f:
                    parts = [part.strip() for part in line.split(',')]
                    vendor_id = product_id = serial_attr = mode = custom_name = None
                    for part in parts:
                        if 'ATTRS{idVendor}' in part:
                            vendor_id = part.split('==')[1].strip('"')
                        elif 'ATTRS{idProduct}' in part:
                            product_id = part.split('==')[1].strip('"')
                        elif 'ATTRS{serial}' in part:
                            serial_attr = part.split('==')[1].strip('"')
                        elif 'MODE' in part:
                            mode = part.split('=')[1].strip('"')
                        elif 'SYMLINK+=' in part:
                            custom_name = part.split('+=')[1].strip('"')
                    if vendor_id and product_id and mode and custom_name:
                        rules.append((vendor_id, product_id, serial_attr, mode, custom_name))
        except FileNotFoundError:
            pass
        return rules

    def populate_rules(self):
        self.scroll_layout.addWidget(QLabel('Device Name'), 0, 0)
        self.scroll_layout.addWidget(QLabel('Vendor ID'), 0, 1)
        self.scroll_layout.addWidget(QLabel('Product ID'), 0, 2)
        self.scroll_layout.addWidget(QLabel('Serial'), 0, 3)
        self.scroll_layout.addWidget(QLabel('Mode'), 0, 4)
        self.scroll_layout.addWidget(QLabel('Custom Name'), 0, 5)

        for i, (vendor_id, product_id, serial_attr, mode, custom_name) in enumerate(self.rules):
            usb_device_name = self.usb_devices.get((vendor_id, product_id), 'Not Connected')

            # Populate details
            self.scroll_layout.addWidget(QLabel(usb_device_name), i + 1, 0)
            self.scroll_layout.addWidget(QLabel(vendor_id), i + 1, 1)
            self.scroll_layout.addWidget(QLabel(product_id), i + 1, 2)
            self.scroll_layout.addWidget(QLabel(serial_attr), i + 1, 3)
            self.scroll_layout.addWidget(QLabel(mode), i + 1, 4)
            name_input = QLineEdit(custom_name)
            self.name_inputs.append(name_input)
            self.scroll_layout.addWidget(name_input, i + 1, 5)

    def populate_new_devices(self):
        self.new_devices_layout.addWidget(QLabel('Device Name'), 0, 0)
        self.new_devices_layout.addWidget(QLabel('Vendor ID'), 0, 1)
        self.new_devices_layout.addWidget(QLabel('Product ID'), 0, 2)
        self.new_devices_layout.addWidget(QLabel('Serial'), 0, 3)
        self.new_devices_layout.addWidget(QLabel('Mode'), 0, 4)
        self.new_devices_layout.addWidget(QLabel('Custom Name'), 0, 5)

        existing_devices = {(vendor_id, product_id) for vendor_id, product_id, _, _, _ in self.rules}
        new_devices = [(vendor_id, product_id, name) for (vendor_id, product_id), name in self.usb_devices.items() if (vendor_id, product_id) not in existing_devices]

        for i, (vendor_id, product_id, device_name) in enumerate(new_devices):
            self.new_devices_layout.addWidget(QLabel(device_name), i + 1, 0)
            self.new_devices_layout.addWidget(QLabel(vendor_id), i + 1, 1)
            self.new_devices_layout.addWidget(QLabel(product_id), i + 1, 2)
            serial_input = QLineEdit('')
            self.new_devices_layout.addWidget(serial_input, i + 1,3)
            mode_input = QLineEdit('0777')
            self.new_devices_layout.addWidget(mode_input, i + 1, 4)
            name_input = QLineEdit()
            self.new_devices_layout.addWidget(name_input, i + 1, 5)
            self.new_device_inputs.append((vendor_id, product_id, serial_input, mode_input, name_input))

    def restart_application(self):
        python = sys.executable
        os.execv(python, [python] + sys.argv)

    def update_all_rules(self):
        try:
            with open(self.rules_file, 'w') as f:
                # Update existing rules
                for i, (vendor_id, product_id, serial_attr,mode, old_custom_name) in enumerate(self.rules):
                    new_custom_name = self.name_inputs[i].text()
                    if new_custom_name:  # Check if custom name is provided
                        if serial_attr:
                            rule = f'SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ATTRS{{idVendor}}=="{vendor_id}", ATTRS{{idProduct}}=="{product_id}", ATTRS{{serial}}=="{serial_attr}", MODE="{mode}", SYMLINK+="{new_custom_name}"\n'
                        else:
                            rule = f'SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ATTRS{{idVendor}}=="{vendor_id}", ATTRS{{idProduct}}=="{product_id}", MODE="{mode}", SYMLINK+="{new_custom_name}"\n'
                        f.write(rule)

                # Add new devices if custom name is provided
                for vendor_id, product_id, serial_input, mode_input, name_input in self.new_device_inputs:
                    custom_name = name_input.text()
                    if custom_name:  # Check if custom name is provided
                        serial_attr = serial_input.text()
                        mode = mode_input.text()
                        if serial_attr:
                            rule = f'SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ATTRS{{idVendor}}=="{vendor_id}", ATTRS{{idProduct}}=="{product_id}", ATTRS{{serial}}=="{serial_attr}", MODE="{mode}", SYMLINK+="{custom_name}"\n'
                        else:
                            rule = f'SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ATTRS{{idVendor}}=="{vendor_id}", ATTRS{{idProduct}}=="{product_id}", MODE="{mode}", SYMLINK+="{custom_name}"\n'
                        f.write(rule)

            subprocess.run(['sudo','udevadm', 'control', '--reload-rules'])
            subprocess.run(['sudo','udevadm', 'trigger'])

            QMessageBox.information(self, 'Success', 'Udev rules updated successfully')

            self.restart_application()  # Call the refresh_ui method to reload the UI

        except PermissionError:
            QMessageBox.critical(self, 'Permission Denied', 'You need to run this application as root')


def main():
    app = QApplication(sys.argv)
    ex = UdevRuleGUI()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
