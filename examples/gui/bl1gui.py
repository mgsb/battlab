"""GUI application for BattLab-One using PySimpleGUI"""

import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import SELECT_MODE_SINGLE

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')

from battlab import BattLabOne


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

class App:
    def __init__(self):
        self.bl1 = BattLabOne()
        self.samples = None
        self.to_ms = 100
        self.block_size = 250
        self.data = [0.0] * self.block_size

        self.fig, self.axes = plt.subplots()
        self.x = [i for i in range(self.block_size)]
        self.line, = self.axes.plot([], [])
        _, _, fw, fh = self.fig.bbox.bounds

        self.layout = [
            [sg.Text("Voltage (V): "), sg.Listbox(values=self.bl1.VOLTAGES,
                                                  default_values = [1.2],
                                                  key="voltage",
                                                  size=(8, 2),
                                                  select_mode=SELECT_MODE_SINGLE)],
            [sg.Text("Current Range:"),
             sg.Radio(text="High", group_id="crange", default=True, key="crange-high"),
             sg.Radio(text="Low", group_id="crange", key="crange-low")],
            [sg.Button('Sample'), sg.Checkbox('Trigger', key="trigger", default=False),
             sg.Button("Stop", disabled=True)],
            [sg.HorizontalSeparator(color="#000000")],
            [sg.Canvas(size=(fw, fh), key="canvas")],
        ]

    def dispatch_event(self, event, values):
        return self.DISPATCH[event](self, values)

    def sample(self, values):
        self.to_ms = 0

        self.window["Sample"].update(disabled=True)
        self.window["Stop"].update(disabled=False)

        self.axes.set_xlim(0, self.block_size)
        self.data = [0.0] * self.block_size
        plt.title("")
        plt.draw()

        self.bl1.current_range = self.bl1.CurrentRange.HIGH \
            if values["crange-high"] else self.bl1.CurrentRange.LOW
        self.bl1.voltage = values["voltage"][0]

        self.trigger = values["trigger"]
        print("sample: ", self.trigger)
        self.samples = self.bl1.sample(self.trigger)

        self.animation.resume()

        return True

    def stop(self, *_):
        self.samples = None
        self.to_ms = 100
        self.bl1.reset()
        del self.data[0:self.block_size]
        results = ("{} samples\navg: {:.3f} max: {:.3f} " +
                   "min: {:.3f}").format(len(self.data),
                                         sum(self.data) / len(self.data),
                                         max(self.data),
                                         min(self.data))

        self.window["Sample"].update(disabled=False)
        self.window["Stop"].update(disabled=True)

        self.animation.pause()

        if self.trigger:
            self.data.reverse()
            num_zeros = len(self.data) - self.data.index(0.0)
            print(min(self.data), max(self.data))
            print(len(self.data), num_zeros)
            self.data.reverse()
            del self.data[0:num_zeros]

        self.axes.set_xlim(0, len(self.data))
        self.line.set_xdata([i for i in range(len(self.data))])
        self.axes.set_ylim(ymin=min(self.data), ymax=max(self.data))
        self.line.set_ydata(self.data)
        plt.title(results)
        plt.draw()

        return True

    def timeout(self, *_):
        if self.samples:
            try:
                self.data.append(next(self.samples))
            except StopIteration as exc:
                self.samples = None
                self.window["Stop"].click()

        return True

    def setup_plot(self, canvas):
        self.fig_blit = draw_figure(canvas, self.fig)

        def animate(*_):
            self.line.set_xdata(self.x)
            self.line.set_ydata(self.data[-self.block_size:])
            self.axes.set_ylim(min(self.data[-self.block_size:]),
                               max(self.data[-self.block_size:]) + 0.1)
            return self.line,

        self.animation = animation.FuncAnimation(self.fig, animate, interval=20,
                                                 blit=True)
    def set_window(self, window):
        self.setup_plot(window["canvas"].TKCanvas)
        self.window = window
        return True

    def shutdown(self, *_):
        self.bl1.voltage = 0
        self.bl1.reset()
        return False

    DISPATCH = {
        "Sample": sample,
        "Stop": stop,
        "__TIMEOUT__": timeout,
        None: shutdown,
    }

def main():
    sg.theme('Default 1')

    app = App()
    window = sg.Window("BattLab-One", app.layout, finalize=True,
                       force_toplevel=True) #, font=("Arial", 12))
    app.set_window(window)

    while True:
        event, values = window.read(timeout=app.to_ms)

        if not app.dispatch_event(event, values):
            break

    window.close()


if __name__ == "__main__":
    main()
