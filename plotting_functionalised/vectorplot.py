import numpy as np
import math
import matplotlib.patches as mpatches
import warnings

def vectorplot_setup(ax):
    ax.set_title("Change in impact per kg between 2010 and 2021")
    ax.set_xlabel(r"Change in Biodiversity Opportunity Cost per m$^2$")
    ax.set_ylabel(r"Change in Land use per kg")

    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    xstep = 0.1 if x_max - x_min <= 0.5 else 0.25
    ystep = 0.1 if y_max - y_min <= 0.5 else 0.25
    if x_max-x_min > 2:
        xstep, ystep = 0.5,0.5
    xtick_locs = np.arange(x_min, x_max+xstep, xstep)
    ytick_locs = np.arange(y_min, y_max+ystep, ystep)
    xtick_labels = [f"{int(tick * 100)}%" for tick in xtick_locs]
    ytick_labels = [f"{int(tick * 100)}%" for tick in ytick_locs]

    ax.set_xticks(xtick_locs, xtick_labels)
    ax.set_yticks(ytick_locs, ytick_labels)
    ax.grid(zorder=0)
    ax.axhline(0, color="black", linewidth=0.8, zorder=1)
    ax.axvline(0, color="black", linewidth=0.8, zorder=1)
    xs = np.linspace(-1, 1, 100)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ys = -xs/(1+xs)
    ys[0] = 2
    ax.plot(xs, ys, ls="dashed", color="grey", linewidth=0.8, zorder=2, label="Iso-impact line")
    ax.fill_between(xs, ys, -1, color="#d0f0d0", zorder=0, label="Impact decrease")
    ax.fill_between(xs, ys, 1, color="#f0d0d0", zorder=0, label="Impact increase")
    leg = ax.legend(fontsize=6, loc="upper right")
    ax.add_artist(leg)

def plot_vector(ax, x_change, y_change, width, color, label, text_offset=0.04):
    patch = mpatches.FancyArrow(0,0,x_change,y_change, ec=color, fc=color, length_includes_head=True,
                                    width=width, head_width=3*width, head_length=3*width, zorder=3+width, lw=0)

    l = np.sqrt(x_change**2 + y_change**2)
    x_offset = text_offset * x_change/l
    y_offset = text_offset * y_change/l
    text_x = x_change + x_offset
    text_y = y_change + y_offset

    angle = math.atan2(y_change, x_change)*(180/np.pi)+90
    if angle > 90 and angle < 270:
        angle = angle - 180

    ax.add_patch(patch)
    ax.text(text_x, text_y, s=label, fontsize=6, ha="center", va="center", color="#000000", rotation=angle, zorder=4)

    