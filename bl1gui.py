import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import SELECT_MODE_SINGLE

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from battlab import BattLabOne


def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

class App:
    def __init__(self):
        self.bl1 = BattLabOne()
        self.data = [0] * 100
        self.samples = None
        self.to_ms = 100

        self.fig, self.axes = plt.subplots()
        self.axes.set_xlim(0, 100)
        self.axes.set_ylim(0, 2.5)
        self.x = [i for i in range(100)]
        self.line, = self.axes.plot([], [])
        _, _, fw, fh = self.fig.bbox.bounds

        # v_layout = [sg.Text("Voltage (V): ")]
        # for v in self.bl1.VOLTAGES:
        #     v_layout.append(sg.Radio(text=str(v), group_id="voltages", key="voltage_{}".format(v)))

        self.layout = [
            [sg.Text("Voltage (V): "), sg.Listbox(values=self.bl1.VOLTAGES,
                                                  default_values = [1.2],
                                                  key="voltage",
                                                  size=(8, 2),
                                                  select_mode=SELECT_MODE_SINGLE)],
            [sg.Text("Current Range: "),
             sg.Radio(text="High", group_id="crange", default=True, key="crange-high"),
             sg.Radio(text="Low", group_id="crange", key="crange-low")],
            [sg.Button('Sample'), sg.Button("Stop", disabled=True)],
            [sg.HorizontalSeparator(color="#000000")],
            [sg.Canvas(size=(fw, fh), key="canvas")],
        ]

    def dispatch_event(self, event, values):
        self.DISPATCH[event](self, values)

    def sample(self, values):
        self.bl1.current_range = self.bl1.CurrentRange.HIGH
        self.bl1.voltage = 1.2 # values["voltage"][0]
        self.samples = self.bl1.sample()
        self.to_ms = 0

        self.window["Sample"].update(disabled=True)
        self.window["Stop"].update(disabled=False)

        plt.title("")
        plt.draw()
        self.axes.set_xlim(0, 100)
        self.axes.set_ylim(0, 2.5)
        self.data = [0] * 100
        self.animation.resume()

    def stop(self, values):
        self.samples = None
        self.to_ms = 100
        self.bl1.reset()
        del self.data[0:100]
        results = ("{} samples\navg: {:.3f} max: {:.3f} " +
                   "min: {:.3f}").format(len(self.data),
                                         sum(self.data) / len(self.data),
                                         max(self.data),
                                         min(self.data))

        self.window["Sample"].update(disabled=False)
        self.window["Stop"].update(disabled=True)

        self.animation.pause()

        self.axes.set_xlim(0, len(self.data))
        self.line.set_xdata([i for i in range(len(self.data))])
        self.axes.set_ylim(ymin=min(self.data), ymax=max(self.data))
        self.line.set_ydata(self.data)

        plt.title(results)
        plt.draw()

    def timeout(self, values):
        if self.samples:
            self.data.append(next(self.samples))

    def setup_plot(self, canvas):
        self.fig_blit = draw_figure(canvas, self.fig)

        def animate(i):
            self.line.set_xdata(self.x)
            self.line.set_ydata(self.data[-100:])
            return self.line,

        self.animation = animation.FuncAnimation(self.fig, animate, interval=20,
                                           blit=True)
    def set_window(self, window):
        self.setup_plot(window["canvas"].TKCanvas)
        self.window = window

    DISPATCH = {
        "Sample": sample,
        "Stop": stop,
        "__TIMEOUT__": timeout
    }

def main():
    sg.theme('Default 1')

    app = App()
    window = sg.Window("BattLab-One", app.layout, finalize=True,
                       force_toplevel=True, font=("Arial", 12))
    app.set_window(window)

    while True:
        event, values = window.read(timeout=app.to_ms)

        if event == sg.WIN_CLOSED:
            break

        app.dispatch_event(event, values)

    app.bl1.voltage = 0

    window.close()


if __name__ == "__main__":
    main()
