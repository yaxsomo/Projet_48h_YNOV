import tkinter as tk
from ttkbootstrap import Style
from ttkbootstrap.widgets import Meter

from data_handler import BMSPcanListener
from PCANBasic import PCAN_USBBUS1, PCAN_BAUD_250K

class BMSApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Choose a ttkbootstrap theme
        self.style = Style("superhero")  # e.g. "superhero", "cyborg", "darkly", etc.

        self.title("BMS Interface - Single Window (ttkbootstrap + circular meters)")
        self.geometry("1200x800")

        # Keep references for dynamic resizing
        self.resizable_widgets = []

        # Window layout
        self.grid_rowconfigure(0, weight=0)  # Title row
        self.grid_rowconfigure(1, weight=1)  # Main content row
        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label = tk.Label(
            self,
            text="BMS 13-14S (13S) 150-X Supervisor",
            font=("TkDefaultFont", 18, "bold"),
            bg=self.style.colors.get('bg'),
            fg=self.style.colors.get('primary')
        )
        self.title_label.grid(row=0, column=0, pady=10)
        self.resizable_widgets.append(self.title_label)

        # Main content frame
        main_frame = tk.Frame(self, bg=self.style.colors.get('bg'))
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left column: 13 cell voltages + Alarms
        left_col = tk.Frame(main_frame, bg=self.style.colors.get('bg'))
        left_col.grid(row=0, column=0, sticky="nsew", padx=10)

        # ---------------------------------------------------------------------
        # A) 13 Cell Voltages as circular meters, with outside labels
        # ---------------------------------------------------------------------
        self.cell_meters = []
        cell_volt_frame = tk.LabelFrame(
            left_col,
            text="Cell Voltages",
            fg=self.style.theme.colors.info,
            bg=self.style.theme.colors.bg
        )
        cell_volt_frame.pack(side="top", fill="both", expand=False)
        cell_volt_frame.grid_columnconfigure((0,1,2,3), weight=1)

        max_cell_volt = 5.0  # e.g. assume 5.0 V max per cell
        for i in range(13):
            row = i // 4
            col = i % 4

            # Container to hold the meter + label
            m_container = tk.Frame(cell_volt_frame, bg=self.style.colors.get('bg'))
            m_container.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            m = Meter(
                m_container,
                metersize=100,
                amountused=0,
                amounttotal=max_cell_volt,
                # Show only the numeric reading in the circle
                # 'textright' or 'textleft' can hold your numeric value
                textright="-- V",
                textfont="-size 10 -weight bold",
                # No subtext => we won't place "Cell X" inside the meter
                subtext=None,
                bootstyle="info",
                stripethickness=4,
                arcrange=300,
            )
            m.pack(side="top")

            # A separate Label below for "Cell #"
            cell_label = tk.Label(
                m_container,
                text=f"Cell {i+1}",
                bg=self.style.colors.get('bg'),
                fg="white"
            )
            cell_label.pack(side="top")

            # Keep references
            self.cell_meters.append(m)
            # If you want them to scale, add both to resizable_widgets
            self.resizable_widgets.append(m)
            self.resizable_widgets.append(cell_label)

        # ---------------------------------------------------------------------
        # B) Alarms as text
        # ---------------------------------------------------------------------
        alarm_frame = tk.LabelFrame(
            left_col, text="Alarms",
            bg=self.style.theme.colors.bg,
            fg=self.style.theme.colors.info
        )
        alarm_frame.pack(side="top", fill="both", pady=10)

        self.alarm_vmin_label = tk.Label(alarm_frame, text="Vmin Alarm: False",
                                         bg=self.style.theme.colors.bg, fg="white")
        self.alarm_vmin_label.pack(anchor="w", padx=5)

        self.alarm_vmax_label = tk.Label(alarm_frame, text="Vmax Alarm: False",
                                         bg=self.style.theme.colors.bg, fg="white")
        self.alarm_vmax_label.pack(anchor="w", padx=5)

        self.alarm_tmin_label = tk.Label(alarm_frame, text="Tmin Alarm: False",
                                         bg=self.style.theme.colors.bg, fg="white")
        self.alarm_tmin_label.pack(anchor="w", padx=5)

        self.alarm_tmax_label = tk.Label(alarm_frame, text="Tmax Alarm: False",
                                         bg=self.style.theme.colors.bg, fg="white")
        self.alarm_tmax_label.pack(anchor="w", padx=5)

        self.alarm_vbatt_label = tk.Label(alarm_frame, text="Vbatt Alarm: False",
                                          bg=self.style.theme.colors.bg, fg="white")
        self.alarm_vbatt_label.pack(anchor="w", padx=5)

        self.alarm_sn_label = tk.Label(alarm_frame, text="SN Alarm: False",
                                       bg=self.style.theme.colors.bg, fg="white")
        self.alarm_sn_label.pack(anchor="w", padx=5)

        for w in (
            self.alarm_vmin_label,
            self.alarm_vmax_label,
            self.alarm_tmin_label,
            self.alarm_tmax_label,
            self.alarm_vbatt_label,
            self.alarm_sn_label
        ):
            self.resizable_widgets.append(w)

        # ---------------------------------------------------------------------
        # Right column: battery stats + NTC + SN + HW / SW
        # ---------------------------------------------------------------------
        right_col = tk.Frame(main_frame, bg=self.style.colors.get('bg'))
        right_col.grid(row=0, column=1, sticky="nsew", padx=10)

        # Battery Stats
        bat_stats_frame = tk.LabelFrame(
            right_col, text="Battery Stats",
            bg=self.style.theme.colors.bg,
            fg=self.style.theme.colors.info
        )
        bat_stats_frame.pack(side="top", fill="both", pady=5)
        bat_stats_frame.grid_columnconfigure((0,1), weight=1)

        # We'll do the same approach: a container for each meter + label
        self.meter_vpack = self._create_meter_with_label(
            parent=bat_stats_frame,
            meter_label="Vpack",
            meter_size=120,
            amounttotal=60,
            textleft="-- V",   # numeric reading inside
            style="warning"
        )
        self.meter_vpack.grid(row=0, column=0, padx=5, pady=5)

        self.meter_vmin = self._create_meter_with_label(
            parent=bat_stats_frame,
            meter_label="Vmin",
            meter_size=120,
            amounttotal=5,
            textleft="-- V",
            style="info"
        )
        self.meter_vmin.grid(row=0, column=1, padx=5, pady=5)

        self.meter_vmax = self._create_meter_with_label(
            parent=bat_stats_frame,
            meter_label="Vmax",
            meter_size=120,
            amounttotal=5,
            textleft="-- V",
            style="info"
        )
        self.meter_vmax.grid(row=1, column=0, padx=5, pady=5)

        self.meter_vbatt = self._create_meter_with_label(
            parent=bat_stats_frame,
            meter_label="Vbatt",
            meter_size=120,
            amounttotal=60,
            textleft="-- V",
            style="warning"
        )
        self.meter_vbatt.grid(row=1, column=1, padx=5, pady=5)

        # NTC Temperatures
        ntc_frame = tk.LabelFrame(
            right_col, text="NTC Temperatures",
            bg=self.style.theme.colors.bg, fg=self.style.theme.colors.info
        )
        ntc_frame.pack(side="top", fill="both", pady=5)
        ntc_frame.grid_columnconfigure((0,1,2), weight=1)

        self.meter_ntc1 = self._create_meter_with_label(
            parent=ntc_frame,
            meter_label="NTC1",
            meter_size=90,
            amounttotal=100,
            textleft="--°C",
            style="success"
        )
        self.meter_ntc1.grid(row=0, column=0, padx=5, pady=5)

        self.meter_ntc2 = self._create_meter_with_label(
            parent=ntc_frame,
            meter_label="NTC2",
            meter_size=90,
            amounttotal=100,
            textleft="--°C",
            style="success"
        )
        self.meter_ntc2.grid(row=0, column=1, padx=5, pady=5)

        self.meter_ntc3 = self._create_meter_with_label(
            parent=ntc_frame,
            meter_label="NTC3",
            meter_size=90,
            amounttotal=100,
            textleft="--°C",
            style="success"
        )
        self.meter_ntc3.grid(row=0, column=2, padx=5, pady=5)

        # BMS Serial Number
        sn_frame = tk.LabelFrame(
            right_col, text="BMS Serial Number",
            bg=self.style.theme.colors.bg,
            fg=self.style.theme.colors.info
        )
        sn_frame.pack(side="top", fill="x", pady=5)
        self.sn_label = tk.Label(sn_frame, text="SN: --", bg=self.style.colors.get('bg'), fg="white")
        self.sn_label.pack(anchor="w", padx=5, pady=2)
        self.resizable_widgets.append(self.sn_label)

        # HW / SW
        version_frame = tk.LabelFrame(
            right_col, text="HW / SW Versions",
            bg=self.style.theme.colors.bg,
            fg=self.style.theme.colors.info
        )
        version_frame.pack(side="top", fill="x", pady=5)
        self.hw_label = tk.Label(version_frame, text="HW: --", bg=self.style.colors.get('bg'), fg="white")
        self.hw_label.pack(anchor="w", padx=5, pady=2)
        self.sw_label = tk.Label(version_frame, text="SW: --", bg=self.style.colors.get('bg'), fg="white")
        self.sw_label.pack(anchor="w", padx=5, pady=2)
        self.resizable_widgets.extend([self.hw_label, self.sw_label])

        # Start CAN listener
        self.can_listener = BMSPcanListener(
            channel=PCAN_USBBUS1,
            baudrate=PCAN_BAUD_250K,
            on_update=self.on_bms_data
        )
        self.can_listener.start()

        # Window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Debounced resizing
        self.bind("<Configure>", self._on_configure)
        self._resize_id = None

    def _create_meter_with_label(self, parent, meter_label, meter_size, amounttotal,
                                 textleft, style="info"):
        """
        Helper to create a container with a Meter (only numeric inside)
        + a separate Label below it to show the 'meter_label' outside the circle.
        """
        container = tk.Frame(parent, bg=self.style.colors.get('bg'))

        # The actual Meter
        meter = Meter(
            container,
            metersize=meter_size,
            amountused=0,
            amounttotal=amounttotal,
            textleft=textleft,
            textfont="-size 10 -weight bold",
            # No subtext => label is outside the meter
            subtext=None,
            bootstyle=style,
            stripethickness=4,
        )
        meter.pack(side="top")

        # The label below
        label = tk.Label(
            container,
            text=meter_label,
            bg=self.style.colors.get('bg'),
            fg="white"
        )
        label.pack(side="top")

        # Let the caller place container in grid
        # Also add to resizable so we can scale fonts
        self.resizable_widgets.append(meter)
        self.resizable_widgets.append(label)
        return container

    def on_bms_data(self, data):
        """
        Called whenever new BMS data arrives: update the meter values and alarm states, etc.
        """
        # Cell voltages: 13 meters
        for i, val in enumerate(data["voltages"]):
            if val is not None:
                used = min(val, 5.0)
                self.cell_meters[i].configure(amountused=used, textright=f"{val:.2f}V")
            else:
                self.cell_meters[i].configure(amountused=0, textright="-- V")

        # Battery stats
        if data["pack_sum"] is not None:
            used = min(data["pack_sum"], 60)
            self.meter_vpack.winfo_children()[0].configure(amountused=used, textleft=f"{data['pack_sum']:.2f}V")
        if data["vmin"] is not None:
            used = min(data["vmin"], 5)
            self.meter_vmin.winfo_children()[0].configure(amountused=used, textleft=f"{data['vmin']:.2f}V")
        if data["vmax"] is not None:
            used = min(data["vmax"], 5)
            self.meter_vmax.winfo_children()[0].configure(amountused=used, textleft=f"{data['vmax']:.2f}V")
        if data["vbatt"] is not None:
            used = min(data["vbatt"], 60)
            self.meter_vbatt.winfo_children()[0].configure(amountused=used, textleft=f"{data['vbatt']:.2f}V")

        # NTC
        ntc1, ntc2, ntc3 = data["ntc"]
        if ntc1 is not None:
            self.meter_ntc1.winfo_children()[0].configure(amountused=min(ntc1, 100),
                                                          textleft=f"{ntc1:.1f}°C")
        if ntc2 is not None:
            self.meter_ntc2.winfo_children()[0].configure(amountused=min(ntc2, 100),
                                                          textleft=f"{ntc2:.1f}°C")
        if ntc3 is not None:
            self.meter_ntc3.winfo_children()[0].configure(amountused=min(ntc3, 100),
                                                          textleft=f"{ntc3:.1f}°C")

        # Alarms
        def update_alarm(label_widget, triggered):
            base_text = label_widget.cget("text").split(":")[0]
            if triggered:
                label_widget.config(text=f"{base_text}: True", fg="#FF5555")
            else:
                label_widget.config(text=f"{base_text}: False", fg="white")

        alarms = data["alarms"]
        update_alarm(self.alarm_vmin_label, alarms["vmin"])
        update_alarm(self.alarm_vmax_label, alarms["vmax"])
        update_alarm(self.alarm_tmin_label, alarms["tmin"])
        update_alarm(self.alarm_tmax_label, alarms["tmax"])
        update_alarm(self.alarm_vbatt_label, alarms["vbatt"])
        update_alarm(self.alarm_sn_label, alarms["sn_error"])

        # SN, HW, SW
        if data["serial_number"] is not None:
            self.sn_label.config(text=f"SN: {data['serial_number']}")
        if data["hw_version"] is not None:
            self.hw_label.config(text=f"HW: {data['hw_version']}")
        if data["sw_version"] is not None:
            self.sw_label.config(text=f"SW: {data['sw_version']}")

    def on_closing(self):
        # Stop the CAN thread
        self.can_listener.stop()
        self.destroy()

    def _on_configure(self, event):
        """Debounce the resizing so we only scale fonts 200ms after the last event."""
        if hasattr(self, "_resize_id") and self._resize_id is not None:
            self.after_cancel(self._resize_id)
        self._resize_id = self.after(200, self._resize_widgets)

    def _resize_widgets(self):
        """
        Dynamically adjusts fonts, with separate sizes for the meter’s numeric text 
        vs. the label text, so that each is scaled but remain separate. 
        """
        w = self.winfo_width()
        h = self.winfo_height()

        scale_factor = min(w / 1200, h / 800)
        base_size = 14
        new_size = int(base_size * scale_factor)
        if new_size < 8:
            new_size = 8
        if new_size > 16:
            new_size = 16

        # main numeric text in the Meter
        meter_font_str = f"-size {new_size} -weight bold"

        # make label or subtext smaller
        label_size = max(4, new_size - 4)
        label_font_str = f"-size {label_size}"

        # or for normal tk.Label
        normal_font_tuple = ("TkDefaultFont", new_size)

        from ttkbootstrap.widgets import Meter
        for widget in self.resizable_widgets:
            if isinstance(widget, Meter):
                try:
                    # We only have a single text in the circle (textleft or textright).
                    # subtext is None, so we can skip subtextfont or set them the same.
                    widget.configure(
                        textfont=meter_font_str
                    )
                except Exception as e:
                    print(f"Meter font resize error: {e}")

            elif isinstance(widget, tk.Label):
                try:
                    # If it's a label we used for "Cell X" or "Vpack," we can use label_font_str
                    widget.configure(font=(None, label_size))
                except Exception as e:
                    print(f"Label font resize error: {e}")
            else:
                # fallback for normal widgets (like the alarm labels or title)
                try:
                    widget.configure(font=normal_font_tuple)
                except Exception as e:
                    print(f"Widget font resize error: {e}")

if __name__ == "__main__":
    app = BMSApp()
    app.mainloop()
