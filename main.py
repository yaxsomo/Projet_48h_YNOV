# main.py
import tkinter as tk
from tkinter import ttk

from bms_can_pcanbasic import BMSPcanListener
from PCANBasic import PCAN_USBBUS1, PCAN_BAUD_250K

class BMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMS Interface")
        self.geometry("1200x800")  # Default size

        # This list holds widgets that we want to auto-resize in _resize_widgets
        self.resizable_widgets = []

        # Configure root for grid geometry
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1) Top label just for demonstration
        #    You can remove this or put it inside your tab frames
        self.info_label = ttk.Label(self, text="Real-Time BMS Data", font=("Arial", 16, "bold"))
        self.info_label.grid(row=0, column=0, pady=10)
        self.resizable_widgets.append(self.info_label)

        # 2) Main Notebook to hold top-level tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        # Create two top-level tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.details_tab, text="Details")

        # Build out the two tabs
        self._build_main_tab(self.main_tab)
        self._build_details_tab(self.details_tab)

        # Bind a callback for window resizing
        self.bind("<Configure>", self._resize_widgets)

        # 3) Instantiate our PCAN listener
        self.can_listener = BMSPcanListener(
            channel=PCAN_USBBUS1,
            baudrate=PCAN_BAUD_250K,
            on_update=self.on_bms_data  # We'll update GUI labels from bms_data
        )
        self.can_listener.start()

        # On close, stop the CAN thread
        self.protocol("WM_DELETE_WINDOW", self.on_closing)


    def _build_main_tab(self, parent):
        """
        MAIN TAB:
         - Big Title
         - Alarm frame
         - Battery Health frame
         - Basic info: SoC, SoH, Wake up, Charger, etc.
         - We will display pack stats (pack_sum, vmin, vmax, vbatt)
           plus a quick reference to alarm states
        """

        # Layout config
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # 1) Big Title
        title_label = ttk.Label(
            parent, text="BMS 13-14S (13S) 150-X Supervisor",
            font=("Arial", 24, "bold")
        )
        title_label.grid(row=0, column=0, pady=10)
        self.resizable_widgets.append(title_label)

        # 2) Main content frame (three columns: left/middle/right)
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # ~~~~ LEFT COLUMN ~~~~
        left_col = ttk.Frame(content_frame, padding=10)
        left_col.grid(row=0, column=0, sticky="nsew")

        # Alarm frame
        alarm_frame = ttk.Labelframe(left_col, text="Alarm")
        alarm_frame.grid(row=0, column=0, sticky="ew", pady=5)
        # We'll show alarm bits for vmin, vmax, tmin, tmax, vbatt, sn_error
        self.alarm_vmin_label = ttk.Label(alarm_frame, text="Vmin Alarm: False", foreground="black")
        self.alarm_vmin_label.grid(row=0, column=0, padx=5, pady=2)

        self.alarm_vmax_label = ttk.Label(alarm_frame, text="Vmax Alarm: False", foreground="black")
        self.alarm_vmax_label.grid(row=1, column=0, padx=5, pady=2)

        self.alarm_tmin_label = ttk.Label(alarm_frame, text="Tmin Alarm: False", foreground="black")
        self.alarm_tmin_label.grid(row=2, column=0, padx=5, pady=2)

        self.alarm_tmax_label = ttk.Label(alarm_frame, text="Tmax Alarm: False", foreground="black")
        self.alarm_tmax_label.grid(row=3, column=0, padx=5, pady=2)

        self.alarm_vbatt_label = ttk.Label(alarm_frame, text="Vbatt Alarm: False", foreground="black")
        self.alarm_vbatt_label.grid(row=4, column=0, padx=5, pady=2)

        self.alarm_sn_label = ttk.Label(alarm_frame, text="SN Alarm: False", foreground="black")
        self.alarm_sn_label.grid(row=5, column=0, padx=5, pady=2)

        # Wake up & Charger frames
        wake_frame = ttk.Labelframe(left_col, text="Wake up")
        wake_frame.grid(row=1, column=0, sticky="ew", pady=5)
        ttk.Label(wake_frame, text="Switch: OFF").grid(row=0, column=0, padx=5, pady=5)

        charger_frame = ttk.Labelframe(left_col, text="Charger")
        charger_frame.grid(row=2, column=0, sticky="ew", pady=5)
        ttk.Label(charger_frame, text="Detected: NO").grid(row=0, column=0, padx=5, pady=5)

        # ~~~~ MIDDLE COLUMN ~~~~
        middle_col = ttk.Frame(content_frame, padding=10)
        middle_col.grid(row=0, column=1, sticky="nsew")

        battery_frame = ttk.Labelframe(middle_col, text="Battery Health")
        battery_frame.grid(row=0, column=0, sticky="ew")

        # Pack Voltage
        ttk.Label(battery_frame, text="Pack Voltage:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.pack_voltage_val = ttk.Label(battery_frame, text="-- V")
        self.pack_voltage_val.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # vmin, vmax
        ttk.Label(battery_frame, text="Vmin:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.vmin_val = ttk.Label(battery_frame, text="-- V")
        self.vmin_val.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(battery_frame, text="Vmax:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.vmax_val = ttk.Label(battery_frame, text="-- V")
        self.vmax_val.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # Battery measured "Vbatt"
        ttk.Label(battery_frame, text="Vbatt:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.vbatt_val = ttk.Label(battery_frame, text="-- V")
        self.vbatt_val.grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # SoH is not directly in the frames, but let's keep a placeholder
        ttk.Label(battery_frame, text="SoH:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.soh_val = ttk.Label(battery_frame, text="-- %")
        self.soh_val.grid(row=4, column=1, sticky="w", padx=5, pady=2)

        # ~~~~ RIGHT COLUMN ~~~~
        right_col = ttk.Frame(content_frame, padding=10)
        right_col.grid(row=0, column=2, sticky="nsew")

        # For demonstration, some placeholders
        ttk.Label(right_col, text="Time before relay opens:").grid(row=0, column=0, sticky="w", padx=5)
        self.time_val = ttk.Label(right_col, text="-- s")
        self.time_val.grid(row=0, column=1, sticky="w", padx=5)

        # SOC placeholders
        ttk.Label(right_col, text="% (User SOC):").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.user_soc_val = ttk.Label(right_col, text="-- %")
        self.user_soc_val.grid(row=1, column=1, padx=5)

        ttk.Label(right_col, text="% (Real SOC):").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        self.real_soc_val = ttk.Label(right_col, text="-- %")
        self.real_soc_val.grid(row=2, column=1, padx=5)

        # Footer with "Com Activity" + "Restart" button
        bottom_bar = ttk.Frame(parent)
        bottom_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        bottom_bar.grid_columnconfigure(0, weight=1)

        self.comm_label = ttk.Label(bottom_bar, text="Com activity : ")
        self.comm_label.grid(row=0, column=0, sticky="w")

        restart_button = ttk.Button(bottom_bar, text="Restart")
        restart_button.grid(row=0, column=1, sticky="e", padx=10)

        # Add all dynamic labels to self.resizable_widgets if desired
        for w in (
            self.alarm_vmin_label, self.alarm_vmax_label, self.alarm_tmin_label,
            self.alarm_tmax_label, self.alarm_vbatt_label, self.alarm_sn_label,
            self.pack_voltage_val, self.vmin_val, self.vmax_val, self.vbatt_val,
            self.soh_val, self.time_val, self.user_soc_val, self.real_soc_val,
            self.comm_label
        ):
            self.resizable_widgets.append(w)

    def _build_details_tab(self, parent):
        """
        DETAILS TAB: A sub-notebook with multiple pages (Live view, etc.).
        We'll show the "Live view" with:
          - Cell voltages V1..V13
          - NTC temperatures
          - Global measures (pack sum, vmin, vmax, vbatt)
          - Alerts
          - Customer info (Serial #)
          - Board info (HW / SW version)
        """
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        sub_notebook = ttk.Notebook(parent)
        sub_notebook.grid(row=0, column=0, sticky="nsew")

        live_view_tab = ttk.Frame(sub_notebook)
        parameters_tab = ttk.Frame(sub_notebook)
        blackbox_journal_tab = ttk.Frame(sub_notebook)
        blackbox_events_tab = ttk.Frame(sub_notebook)

        sub_notebook.add(live_view_tab, text="Live view")
        sub_notebook.add(parameters_tab, text="Parameters")
        sub_notebook.add(blackbox_journal_tab, text="Blackbox - Journal")
        sub_notebook.add(blackbox_events_tab, text="Blackbox - Events log")

        self._build_live_view(live_view_tab)

        ttk.Label(parameters_tab, text="(Parameters UI goes here)").pack(padx=20, pady=20)
        ttk.Label(blackbox_journal_tab, text="(Blackbox - Journal UI goes here)").pack(padx=20, pady=20)
        ttk.Label(blackbox_events_tab, text="(Blackbox - Events log UI goes here)").pack(padx=20, pady=20)

    def _build_live_view(self, parent):
        """
        LIVE VIEW TAB:
         - Display each cell voltage V1..V13
         - Display NTC1..NTC3
         - Show global battery measures (already in main, but repeated here)
         - Show alarms or other info
         - Show SN, HW, SW
        """

        # We'll keep references to each label for V1..V13, NTC1..3, SN, HW, SW
        self.cell_labels = []  # list of labels for V1..V13

        top_frame = ttk.LabelFrame(parent, text="Cell voltages (V1..V13)")
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Lay out V1..V13 in a grid or multiple rows
        # We'll do a 4-column approach: V1..V4 in row0, V5..V8 in row1, V9..V12 in row2, and V13 alone in row3
        for i in range(13):
            row = i // 4
            col = i % 4
            label_name = f"V{i+1}"
            lbl = ttk.Label(top_frame, text=f"{label_name}: -- V", width=12)
            lbl.grid(row=row, column=col, padx=5, pady=3)
            self.cell_labels.append(lbl)
            self.resizable_widgets.append(lbl)

        # NTC frame
        ntc_frame = ttk.LabelFrame(parent, text="Temperatures (NTC1..NTC3)")
        ntc_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        self.ntc1_label = ttk.Label(ntc_frame, text="NTC1: -- °C")
        self.ntc1_label.grid(row=0, column=0, padx=5, pady=3)
        self.ntc2_label = ttk.Label(ntc_frame, text="NTC2: -- °C")
        self.ntc2_label.grid(row=0, column=1, padx=5, pady=3)
        self.ntc3_label = ttk.Label(ntc_frame, text="NTC3: -- °C")
        self.ntc3_label.grid(row=0, column=2, padx=5, pady=3)
        self.resizable_widgets.extend([self.ntc1_label, self.ntc2_label, self.ntc3_label])

        # Board info (pack stats, SN, HW, SW)
        board_frame = ttk.LabelFrame(parent, text="Board / BMS Info")
        board_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.pack_sum_label = ttk.Label(board_frame, text="Pack sum: -- V")
        self.pack_sum_label.grid(row=0, column=0, padx=5, pady=3)

        self.vmin_label = ttk.Label(board_frame, text="Vmin: -- V")
        self.vmin_label.grid(row=0, column=1, padx=5, pady=3)

        self.vmax_label = ttk.Label(board_frame, text="Vmax: -- V")
        self.vmax_label.grid(row=0, column=2, padx=5, pady=3)

        self.vbatt_label2 = ttk.Label(board_frame, text="Vbatt: -- V")
        self.vbatt_label2.grid(row=1, column=0, padx=5, pady=3)

        # SN
        self.sn_label = ttk.Label(board_frame, text="SN: --")
        self.sn_label.grid(row=1, column=1, padx=5, pady=3)

        # HW/SW
        self.hw_label = ttk.Label(board_frame, text="HW: --")
        self.hw_label.grid(row=2, column=0, padx=5, pady=3)

        self.sw_label = ttk.Label(board_frame, text="SW: --")
        self.sw_label.grid(row=2, column=1, padx=5, pady=3)

        self.resizable_widgets.extend([
            self.pack_sum_label, self.vmin_label, self.vmax_label,
            self.vbatt_label2, self.sn_label, self.hw_label, self.sw_label
        ])
        

    def on_bms_data(self, data):
        """
        Called whenever a new BMS frame (0x200..0x301) is parsed.
        'data' is a dictionary with:
          data["voltages"][0..12]   -> V1..V13
          data["ntc"][0..2]         -> NTC1..3
          data["pack_sum"], data["vmin"], data["vmax"], data["vbatt"]
          data["alarms"]["vmin"].. etc.
          data["serial_number"], data["hw_version"], data["sw_version"]
        Update the GUI accordingly.
        """
        # --- Update cell voltages (live_view) ---
        for i, val in enumerate(data["voltages"]):
            if val is not None:
                txt = f"V{i+1}: {val:.2f} V"
            else:
                txt = f"V{i+1}: -- V"
            # self.cell_labels[i] = the label for that cell
            self.after_idle(lambda lb=self.cell_labels[i], t=txt: lb.config(text=t))

        # --- Update NTC ---
        ntc1, ntc2, ntc3 = data["ntc"]
        if ntc1 is not None:
            self.after_idle(lambda: self.ntc1_label.config(text=f"NTC1: {ntc1:.1f} °C"))
        if ntc2 is not None:
            self.after_idle(lambda: self.ntc2_label.config(text=f"NTC2: {ntc2:.1f} °C"))
        if ntc3 is not None:
            self.after_idle(lambda: self.ntc3_label.config(text=f"NTC3: {ntc3:.1f} °C"))

        # --- Update pack stats ---
        if data["pack_sum"] is not None:
            self.after_idle(lambda: self.pack_sum_label.config(text=f"Pack sum: {data['pack_sum']:.2f} V"))
            self.after_idle(lambda: self.pack_voltage_val.config(text=f"{data['pack_sum']:.2f} V"))
        if data["vmin"] is not None:
            self.after_idle(lambda: self.vmin_label.config(text=f"Vmin: {data['vmin']:.2f} V"))
            self.after_idle(lambda: self.vmin_val.config(text=f"{data['vmin']:.2f} V"))
        if data["vmax"] is not None:
            self.after_idle(lambda: self.vmax_label.config(text=f"Vmax: {data['vmax']:.2f} V"))
            self.after_idle(lambda: self.vmax_val.config(text=f"{data['vmax']:.2f} V"))
        if data["vbatt"] is not None:
            self.after_idle(lambda: self.vbatt_label2.config(text=f"Vbatt: {data['vbatt']:.2f} V"))
            self.after_idle(lambda: self.vbatt_val.config(text=f"{data['vbatt']:.2f} V"))

        # --- Update alarms ---
        def update_alarm(label_widget, triggered):
            if triggered:
                label_widget.config(text=label_widget.cget("text").split(":")[0] + ": True", foreground="red")
            else:
                label_widget.config(text=label_widget.cget("text").split(":")[0] + ": False", foreground="black")

        alarms = data["alarms"]
        self.after_idle(lambda: update_alarm(self.alarm_vmin_label, alarms["vmin"]))
        self.after_idle(lambda: update_alarm(self.alarm_vmax_label, alarms["vmax"]))
        self.after_idle(lambda: update_alarm(self.alarm_tmin_label, alarms["tmin"]))
        self.after_idle(lambda: update_alarm(self.alarm_tmax_label, alarms["tmax"]))
        self.after_idle(lambda: update_alarm(self.alarm_vbatt_label, alarms["vbatt"]))
        self.after_idle(lambda: update_alarm(self.alarm_sn_label, alarms["sn_error"]))

        # --- Update SN, HW, SW ---
        if data["serial_number"] is not None:
            self.after_idle(lambda: self.sn_label.config(text=f"SN: {data['serial_number']}"))
        if data["hw_version"] is not None:
            self.after_idle(lambda: self.hw_label.config(text=f"HW: {data['hw_version']}"))
        if data["sw_version"] is not None:
            self.after_idle(lambda: self.sw_label.config(text=f"SW: {data['sw_version']}"))

    def on_closing(self):
        """ Stop the CAN listener and then close the application. """
        self.can_listener.stop()
        self.destroy()

    def _resize_widgets(self, event):
        """
        Dynamically adjust font sizes based on window size.
        We'll keep it simple: scale relative to 1200x800 reference.
        """
        w = self.winfo_width()
        h = self.winfo_height()
        scale_factor = min(w / 1200, h / 800)

        base_size = 14
        new_size = int(base_size * scale_factor)
        if new_size < 10:
            new_size = 10
        new_font = ("Arial", new_size)

        for widget in self.resizable_widgets:
            try:
                widget.configure(font=new_font)
            except tk.TclError:
                pass

if __name__ == "__main__":
    app = BMSApp()
    app.mainloop()
