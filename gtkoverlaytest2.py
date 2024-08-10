import subprocess
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk # type: ignore
from gi.repository import GLib # type: ignore
import time


def on_window_delete_event(widget, event):
    Gtk.main_quit()

class TimeLabel(Gtk.Label):
    def __init__(self, shell_com: str = "python3 main2.py", windowobj=None):
        self.command = shell_com
        self._windowobjthingy = windowobj
        self._win_was_moved = False
        self._last_output = "Connecting..."
        Gtk.Label.__init__(self, label = "hbeattext")
        self.process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.set_blocking(self.process.stdout.fileno(), False)
        GLib.timeout_add(300, self.updateEvent_Label)
        self.updateEvent_Label()

    def updateEvent_Label(self):
        timeStr = self.get_proc_line()
        print(self._win_was_moved, self._last_output)
        if not self._win_was_moved:
            if not self._last_output == "Connecting...":
                self._windowobjthingy.move(self._windowobjthingy.get_position()[0],0)
                self._win_was_moved = True
        self.set_markup(f"<span foreground='red' font_desc='Px IBM PS2thin2 22'>{timeStr}</span>")
        return GLib.SOURCE_CONTINUE

    def getTime(self):
        return time.strftime("%c")
    
    def get_proc_line(self):
            output = self.process.stdout.readline().decode().strip()
            print(output)
            # print(output)
            if self.process.poll() is not None:
                Gtk.main_quit()
            if output:
                # print("procpol", self.process.poll())
                self._last_output = output; return output
            return self._last_output
    











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

# Create a label with red color
# label = Gtk.Label()
# label.set_markup('<span foreground="red" font_desc="Arial 36">Hello, World!</span>')
# window.add(label)
labelthing = TimeLabel(windowobj=window)# , shell_com="ping -c 4 1.1.1.1")
# def gtk_style():
#     css = b"""
# * {outline-color:black;outline-width:10px;outline-style:solid}
#         """

#     style_provider = Gtk.CssProvider()
#     style_provider.load_from_data(css)

#     Gtk.StyleContext.add_provider_for_screen(
#         Gdk.Screen.get_default(),
#         style_provider,
#         Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
#     )

# gtk_style()
# labelthing.set_justify(Gtk.Justification.LEFT)
window.add(labelthing)
window.show_all()
Gtk.main()

