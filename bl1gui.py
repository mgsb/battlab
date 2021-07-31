import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import SELECT_MODE_SINGLE

from random import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from battlab import BattLabOne


def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def main():
    sg.theme('Default 1')

    bl1 = BattLabOne()

    fig, ax = plt.subplots()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)
    x = [i for i in range(100)]
    line, = ax.plot([], [])
    _, _, fw, fh = fig.bbox.bounds # (0, 0, 100, 75) #

    layout = [
        [sg.Text("Voltage (V): "), sg.Listbox(values=bl1.VOLTAGES,
                                              default_values = [1.2],
                                              key="voltage",
                                              size=(8, 3),
                                              select_mode=SELECT_MODE_SINGLE),
         sg.Text("Current Range: "),
         sg.Radio(text="High", group_id="crange", default=True, key="crange-high"),
         sg.Radio(text="Low", group_id="crange", key="crange-low")],
        [sg.Button('Sample'), sg.Button("Stop")],
        [sg.HorizontalSeparator(color="#000000")],
        [sg.Text("Current (mA): "), sg.Text(size=(10, 1), key="cur_sample")],
        [sg.Text("Statistics: "), sg.Text(size=(40, 1), key="stats")],
        [sg.Canvas(size=(fw, fh), key="canvas")],
    ]

    window = sg.Window("BattLab-One", layout, finalize=True,
                       force_toplevel=True, font=("Arial", 12))

    fig_photo = draw_figure(window["canvas"].TKCanvas, fig)

    def animate(i):
        y = [random() for _ in range(100)]
        line.set_xdata(x)
        line.set_ydata(y)
        return line,

    ani = animation.FuncAnimation(fig, animate, interval=20, blit=True)

    samples = None
    timeout = 100
    data = []

    while True:
        event, values = window.read(timeout=timeout)

        if event == sg.WIN_CLOSED:
            break
        elif event == sg.TIMEOUT_EVENT and samples:
            sample = next(samples)
            data.append(sample)
            window["cur_sample"].update("{:.5f}".format(sample))
        elif event == "Sample":
            bl1.current_range = bl1.CurrentRange.HIGH
            bl1.voltage = values["voltage"][0]
            timeout = 0
            samples = bl1.sample()
            data = []
        elif event == "Stop":
            bl1.reset()
            samples = None
            timeout = 100
            results = ("count: {} avg: {:.3f}, max: {:.3f}, " +
                       "min: {:.3f}").format(len(data), sum(data) / len(data),
                                             max(data),
                                             min(data))
            window["stats"].update(results)


    bl1.voltage = 0

    window.close()


if __name__ == "__main__":
    main()
