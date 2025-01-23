# bms_can_pcanbasic.py
import threading
import time
import select
import sys
from PCANBasic import *

class BMSPcanListener:
    """
    A combined class that:
      - Opens a PCAN-USB channel on macOS using PCANBasic.
      - Spawns a background thread that continuously reads frames.
      - Parses each relevant BMS frame (0x200..0x301).
      - Updates an internal dictionary bms_data.
      - Calls on_update(bms_data) for the GUI to refresh.
    """

    def __init__(
        self,
        channel=PCAN_USBBUS1,
        baudrate=PCAN_BAUD_250K,
        on_update=None
    ):
        """
        :param channel: which PCAN USB channel to open, e.g. PCAN_USBBUS1
        :param baudrate: e.g. PCAN_BAUD_250K
        :param on_update: callback function bms_data -> None 
                          (called whenever a new BMS frame is parsed)
        """

        self.channel = channel
        self.baudrate = baudrate
        self.on_update = on_update

        # BMS data dictionary – fields from your readme
        self.bms_data = {
            "voltages": [None]*13,        # Cell voltages V1..V13
            "ntc": [None]*3,             # Temperatures from NTC1..NTC3
            "pack_sum": None,            # Vpack (sum of all cells)
            "vmin": None,
            "vmax": None,
            "vbatt": None,
            "alarms": {
                "vmin": False,
                "vmax": False,
                "tmin": False,
                "tmax": False,
                "vbatt": False,
                "sn_error": False
            },
            "serial_number": None,       # from 0x300
            "hw_version": None,          # from 0x301
            "sw_version": None           # from 0x301
        }

        self._stop = threading.Event()
        self._thread = None

        # Create a PCANBasic instance
        self.pcan = PCANBasic()
        self.fd = None  # will store the file descriptor for select()

    def start(self):
        """
        Initialize the PCAN channel and start background reading thread.
        """
        # Initialize the channel at the given baudrate
        result = self.pcan.Initialize(self.channel, self.baudrate)
        if result != PCAN_ERROR_OK:
            err_text = self._get_error_text(result)
            raise RuntimeError(f"Error initializing PCAN channel: {err_text}")

        # Retrieve a file descriptor for 'select' calls
        res = self.pcan.GetValue(self.channel, PCAN_RECEIVE_EVENT)
        if res[0] == PCAN_ERROR_OK:
            self.fd = res[1]
        else:
            self.fd = None

        print(f"BMSPcanListener started on channel {self.channel.value} at {self.baudrate.value}.")

        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """
        Stop the background thread and uninitialize the channel.
        """
        self._stop.set()
        if self._thread:
            self._thread.join()

        result = self.pcan.Uninitialize(self.channel)
        if result != PCAN_ERROR_OK:
            err_text = self._get_error_text(result)
            print(f"Error uninitializing PCAN channel: {err_text}")
        else:
            print("PCAN channel uninitialized cleanly.")

    def _run(self):
        """
        Background loop: read from PCAN in a blocking way.
        Whenever a valid frame arrives, parse it. 
        If we successfully parse 0x200..0x301, call on_update(bms_data).
        """
        while not self._stop.is_set():
            # Attempt to read a CAN frame
            result, can_msg, timestamp = self.pcan.Read(self.channel)
            if result == PCAN_ERROR_OK:
                # We got a message -> parse it
                self._handle_message(can_msg)
            elif result == PCAN_ERROR_QRCVEMPTY:
                # No frame -> block briefly
                if self.fd and self.fd != -1:
                    select.select([self.fd], [], [], 0.1)
                else:
                    time.sleep(0.1)
            else:
                # Possibly a bus error or something else
                # You can debug print it if needed
                pass

    def _handle_message(self, msg):
        """
        Parse an incoming TPCANMsg and update bms_data.
        Then call self.on_update(bms_data).
        """
        can_id = msg.ID
        data = bytes(msg.DATA[:msg.LEN])  # convert from c_ubyte array to a Python bytes object
        # for easy indexing in parse methods

        # Debug print all incoming frames:
        # print(f"RX frame ID=0x{can_id:X}, len={msg.LEN}, data={list(data)}")

        # dispatch parse logic
        if can_id == 0x200:
            self._parse_0x200(data)
        elif can_id == 0x201:
            self._parse_0x201(data)
        elif can_id == 0x202:
            self._parse_0x202(data)
        elif can_id == 0x203:
            self._parse_0x203(data)
        elif can_id == 0x204:
            self._parse_0x204(data)
        elif can_id == 0x205:
            self._parse_0x205(data)
        elif can_id == 0x206:
            self._parse_0x206(data)
        elif can_id == 0x300:
            self._parse_0x300(data)
        elif can_id == 0x301:
            self._parse_0x301(data)
        else:
            # ignore other IDs or handle them
            return

        # If we parsed a BMS frame, call the callback
        if self.on_update:
            self.on_update(self.bms_data)

    ###################################
    #  PARSE FUNCTIONS (like bms_can.py)
    ###################################

    def _parse_0x200(self, data):
        # data[0..1] => V4, data[2..3] => V3, data[4..5] => V2, data[6..7] => V1
        if len(data) < 8:
            return
        v4_raw = (data[0] << 8) | data[1]
        v3_raw = (data[2] << 8) | data[3]
        v2_raw = (data[4] << 8) | data[5]
        v1_raw = (data[6] << 8) | data[7]
        self.bms_data["voltages"][3] = v4_raw * 0.001
        self.bms_data["voltages"][2] = v3_raw * 0.001
        self.bms_data["voltages"][1] = v2_raw * 0.001
        self.bms_data["voltages"][0] = v1_raw * 0.001

    def _parse_0x201(self, data):
        if len(data) < 8:
            return
        v8_raw = (data[0] << 8) | data[1]
        v7_raw = (data[2] << 8) | data[3]
        v6_raw = (data[4] << 8) | data[5]
        v5_raw = (data[6] << 8) | data[7]
        self.bms_data["voltages"][7] = v8_raw * 0.001
        self.bms_data["voltages"][6] = v7_raw * 0.001
        self.bms_data["voltages"][5] = v6_raw * 0.001
        self.bms_data["voltages"][4] = v5_raw * 0.001

    def _parse_0x202(self, data):
        if len(data) < 8:
            return
        v12_raw = (data[0] << 8) | data[1]
        v11_raw = (data[2] << 8) | data[3]
        v10_raw = (data[4] << 8) | data[5]
        v9_raw  = (data[6] << 8) | data[7]
        self.bms_data["voltages"][11] = v12_raw * 0.001
        self.bms_data["voltages"][10] = v11_raw * 0.001
        self.bms_data["voltages"][9]  = v10_raw * 0.001
        self.bms_data["voltages"][8]  = v9_raw * 0.001

    def _parse_0x203(self, data):
        v13_raw = (data[6] << 8) | data[7]
        self.bms_data["voltages"][12] = v13_raw * 0.001

    def _parse_0x204(self, data):
        # NTC3 => data[2..3], NTC2 => data[4..5], NTC1 => data[6..7]
        if len(data) < 8:
            return
        ntc3_raw = (data[2] << 8) | data[3]
        ntc2_raw = (data[4] << 8) | data[5]
        ntc1_raw = (data[6] << 8) | data[7]
        self.bms_data["ntc"][2] = ntc3_raw * 0.1
        self.bms_data["ntc"][1] = ntc2_raw * 0.1
        self.bms_data["ntc"][0] = ntc1_raw * 0.1

    def _parse_0x205(self, data):
        # [0..1] => vpack, [2..3] => vmin, [4..5] => vmax, [6..7] => vbatt
        if len(data) < 8:
            return
        vpack_raw = (data[0] << 8) | data[1]
        vmin_raw  = (data[2] << 8) | data[3]
        vmax_raw  = (data[4] << 8) | data[5]
        vbatt_raw = (data[6] << 8) | data[7]

        self.bms_data["pack_sum"] = vpack_raw * 0.001
        self.bms_data["vmin"]     = vmin_raw  * 0.001
        self.bms_data["vmax"]     = vmax_raw  * 0.001
        self.bms_data["vbatt"]    = vbatt_raw * 0.001

    def _parse_0x206(self, data):
        # alarm bits in data[0..2]
        if len(data) < 3:
            return
        byte0 = data[0]
        byte1 = data[1]
        byte2 = data[2]
        self.bms_data["alarms"]["vmin"]    = bool(byte0 & 0x01)
        self.bms_data["alarms"]["vmax"]    = bool(byte0 & 0x02)
        self.bms_data["alarms"]["tmin"]    = bool(byte1 & 0x01)
        self.bms_data["alarms"]["tmax"]    = bool(byte1 & 0x02)
        self.bms_data["alarms"]["vbatt"]   = bool(byte2 & 0x01)
        self.bms_data["alarms"]["sn_error"]= bool(byte2 & 0x02)

    def _parse_0x300(self, data):
        # serial number stored as hex
        sn_hex = "".join(f"{byte:02X}" for byte in data)
        self.bms_data["serial_number"] = sn_hex

    def _parse_0x301(self, data):
        # data[3..4] => HW, data[5..7] => SW
        if len(data) < 8:
            return
        hw_major = data[3]
        hw_minor = data[4]
        sw_major = data[5]
        sw_minor = data[6]
        sw_patch = data[7]
        self.bms_data["hw_version"] = f"{hw_major}.{hw_minor}"
        self.bms_data["sw_version"] = f"{sw_major}.{sw_minor}.{sw_patch}"

    def _get_error_text(self, error_code):
        """Helper to retrieve text for a PCAN error code."""
        ret, text = self.pcan.GetErrorText(error_code)
        if ret != PCAN_ERROR_OK:
            return f"Unknown error 0x{error_code:X}"
        return text.decode("utf-8", errors="ignore")


if __name__ == "__main__":
    # Quick test usage:
    def print_data(bms_data):
        print("Received BMS data:", bms_data)

    listener = BMSPcanListener(on_update=print_data)
    listener.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        sys.exit(0)
