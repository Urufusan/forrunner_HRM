import asyncio
import struct
import bitstruct
import gi
import socket
import threading
import os
from bleak import BleakClient
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk # type: ignore
from gi.repository import GLib # type: ignore

HR_MEAS = "00002A37-0000-1000-8000-00805F9B34FB"
address = "38:F9:F5:40:81:D1".lower()

# Unix socket paths
SOCKET_PATH = '/tmp/ble_gtk_socket'

def _clear_socket_fd():
    try:
        os.unlink(SOCKET_PATH)
    except OSError:
        if os.path.exists(SOCKET_PATH):
            raise

class TimeLabel(Gtk.Label):
    def __init__(self, windowobj=None):
        super().__init__(label="Connecting...")
        self._windowobjthingy = windowobj
        self._win_was_moved = False
        self._last_output = "Connecting..."
        GLib.timeout_add(100, self.update_gui)

    def update_gui(self):
        # print("tick")
        if not self._win_was_moved:
            if self._last_output != "Connecting...":
                self._windowobjthingy.move(self._windowobjthingy.get_position()[0], 0)
                self._win_was_moved = True
        self.set_markup(f"<span foreground='red' font_desc='Px IBM PS2thin2 22'>{self._last_output}</span>")
        return True  # Continue calling this function

    def on_new_data(self, new_output):
        self._last_output = new_output
        self.queue_draw()
        if new_output == "!STOP!":
            Gtk.main_quit()

def ble_worker():
    async def start_ble_client():
        async with BleakClient(address) as client:
            if client.is_connected:
                print(f"Connected to {client}")
                with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
                    def hr_val_handler(sender, data):
                        (unused, rr_int, nrg_expnd, snsr_cntct_spprtd, snsr_detect, hr_fmt) = bitstruct.unpack("b3b1b1b1b1b1", data)
                        if hr_fmt:
                            hr_val, = struct.unpack_from("<H", data, 1)  # uint16
                        else:
                            hr_val, = struct.unpack_from("<B", data, 1)  # uint8

                        last_beat = "♥︎" if not hasattr(hr_val_handler, "_last_beat") or not hr_val_handler._last_beat else " "
                        hr_val_handler._last_beat = not getattr(hr_val_handler, "_last_beat", False)

                        output = f"|HR: {(hr_val if snsr_detect else ' --'):3} BPM {last_beat}|"
                        # print(output)
                        # Send data over the socket
                        s.sendto(output.encode('utf-8'), SOCKET_PATH)

                    await client.start_notify(HR_MEAS, hr_val_handler)

                    while client.is_connected:
                        await asyncio.sleep(1)
                    else:
                        s.sendto("!STOP!".encode('utf-8'), SOCKET_PATH)

    # Run the asyncio loop
    asyncio.run(start_ble_client())

def socket_listener(label):
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(SOCKET_PATH)

        while True:
            data, _ = server_socket.recvfrom(1024)  # Buffer size
            output = data.decode('utf-8')
            GLib.idle_add(label.on_new_data, output)  # Update GUI from GTK main loop

def on_window_delete_event(widget, event):
    Gtk.main_quit()

# Create a window with transparent background and no frame or titlebar
window = Gtk.Window()
window.set_decorated(False)
window.set_titlebar(None)
window.set_app_paintable(True)
window.set_position(Gtk.WindowPosition.CENTER)
window.set_default_size(1, 1)
window.set_keep_above(True)
window.set_skip_taskbar_hint(True)
window.set_skip_pager_hint(True)
window.connect("delete-event", on_window_delete_event)

# Set the window background color to transparent
screen = window.get_screen()
visual = screen.get_rgba_visual()
if visual and screen.is_composited():
    window.set_visual(visual)

labelthing = TimeLabel(windowobj=window)
window.add(labelthing)
window.show_all()

_clear_socket_fd()

# Start the BLE worker in a separate thread
ble_thread = threading.Thread(target=ble_worker, daemon=True)
ble_thread.start()

# Start the socket listener in a separate thread
socket_thread = threading.Thread(target=socket_listener, args=(labelthing,), daemon=True)
socket_thread.start()

Gtk.main()

_clear_socket_fd()