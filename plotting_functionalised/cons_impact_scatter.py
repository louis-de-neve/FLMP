import matplotlib.patches as mpatches
from matplotlib.legend_handler import HandlerTuple
import numpy as np
from mosaics import Group



def cons_impact_plot(ax, groups:list[Group])->None:

    def t1(z): return (ax.transData + ax.transAxes.inverted()).transform(z)
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_xlim(1e-1, 1e3)
    ax.set_ylim(1e-11, 1e-7)
    groups = sorted(groups, key=lambda g: g.n)
    labels = []
    handles = []
    for g in groups:
        labels.append(g.name)
        handles.append(tuple([c.line_object for c in g.commodities]))
        for c in g.commodities:
                
            x = c.cons[0]*1000
            y = c.raw_vals[0]/(c.cons[0]*1000)
            x2 = c.cons[1]*1000
            y2 = c.raw_vals[1]/(c.cons[1]*1000)
            x_axes, y_axes = t1((x,y))
            x2_axes, y2_axes = t1((x2,y2))
            dx_axes = x2_axes - x_axes
            dy_axes = y2_axes - y_axes
            l = np.sqrt(dx_axes**2 + dy_axes**2)
            
            arrow_height = 0.015
            if arrow_height+0.005 > l:
                arrow_height = l - 0.005

            patch = mpatches.FancyArrow(x_axes,y_axes,dx_axes,dy_axes, width=0.001, ec=c.color, fc=c.color,
                                        linewidth=1, transform=ax.transAxes, length_includes_head=True,
                                        head_width=0.01, head_length=arrow_height)
            ax.add_patch(patch)



    

   

    total_grid_color = "#2F7FF8"
    for i in range(-12, -4):
        i = 10 ** (i)
        x = np.logspace(-4, 3, 50)
        y = i/x
        ax.plot(x, y, color=total_grid_color, alpha=0.4, linewidth=0.8, zorder=1)

    for j in range(-12, -4):
        for i in np.linspace(1*(10**j), 9*(10**j), 9):
            x = np.logspace(-4, 3, 50)
            y = i/x
            ax.plot(x, y, ls="dashed", color=total_grid_color, alpha=0.2, linewidth=0.8, zorder=1)
    ax.set_ylabel("Impact per kg")
    ax.set_xlabel("Annual consumption per capita, kg")
    ax.set_title("Change in commodity consumption and impact\nbetween 2010 and 2021")

    ax2 = ax.twiny()
    ax2.set_xscale('log')
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    ax2.set_xlim(x1*y2, x2*y2)
    ax2.set_xlabel("Annual Extinctions per capita", color=total_grid_color)
    ax2.tick_params(axis='x', colors=total_grid_color)

    ax.legend(handles, labels,
        fontsize=6, ncols=2,
        handlelength=2.5,handler_map={tuple: HandlerTuple(ndivide=None)})