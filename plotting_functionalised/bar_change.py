import numpy as np
import matplotlib.patches as mpatches
from matplotlib.axes import Axes
from matplotlib.legend_handler import HandlerTuple
from mosaics import label_formatting, Group

def tag_formatting(tag:str)->str:
    if tag.startswith("Others_"):
        label = tag.replace("Others_", "Other ")
        if "pig meat" in label:
            label = "Other meats"
        if "Plantains" in label:
            label = "Plantains"
        if "carbohydrates" in label:
            label = "Other Grains, roots, carbs"
    else:
        label = label_formatting(tag)
    label = label.replace("carbohydrates", "carbs")
    return label

def bar_plot(fig,ax:Axes, groups:list[Group], ylim:tuple[float, float], relative=True, ytick_spacing=0.2, secondary=False)->None:

    left = 0
    pad = 0.008

    groups = sorted(groups, key=lambda group: group.n)
    count = sum([len(g.commodities) for g in groups])
    width = 1/count - pad + pad/count
    tags = []
    tag_colors = []
    t1 = 0
    t2 = 0
    labels = []
    handles = []
    for g in groups:
        commodities = sorted(g.commodities, key=lambda c: c.m)
        g_start = left
        for c in commodities:
            height = (c.raw_vals[1] - c.raw_vals[0])/c.raw_vals[0]
            err = np.sqrt((c.errors[1]/c.raw_vals[1])**2 + (c.errors[0]/c.raw_vals[0])**2) * abs(height)
            if relative:
                width = c.yvals[0]*g.xvals[0]
                pad=0
            if not secondary:
                color = c.color
            else:
                color = f"{c.color}66"
            rect = mpatches.Rectangle((left, 0), width, height, color=c.color, zorder=1, linewidth=0)
            ax.add_patch(rect)
            ax.errorbar(left + width/2, height, yerr=err, color="black", capsize=2, fmt="none", linewidth=0.8, zorder=3)
           
            if height > 0:
                ax.text(left+width/2, height+err+ylim[1]/50, tag_formatting(c.name), rotation=-90, fontsize=6, ha="center", va="bottom", zorder=4)
            else:
                ax.text(left+width/2, height-err-ylim[1]/50, tag_formatting(c.name), rotation=-90, fontsize=6, ha="center", va="top", zorder=4)
            left += width+pad
            tags.append(tag_formatting(c.name))
            tag_colors.append(g.color)
        g_end = left-pad
        g_avg = (g.dataframe(1)["bd_opp_total"].sum() - g.dataframe(0)["bd_opp_total"].sum())/g.dataframe(0)["bd_opp_total"].sum()
        t1 += g.dataframe(0)["bd_opp_total"].sum()
        t2 += g.dataframe(1)["bd_opp_total"].sum()
        #hline = ax.hlines(g_avg, xmin=g_start, xmax=g_end, color=g.color, linewidth=0.8,
        #                  label=tag_formatting(g.name), linestyle=[(3, (3, 3))], gapcolor='white', zorder=2)
        #labels.append(tag_formatting(g.name))
        #handles.append(hline)

    total_average = (t2-t1)/t1
    hline = ax.hlines(total_average, xmin=0, xmax=1, color="#888888", linewidth=0.8, linestyle=[(3, (3, 3))], gapcolor='white', zorder=2.5, label="Total Average")
    labels.append(f"Total: {'{}{}%'.format("+" if total_average > 0 else "", int(total_average*100))}")
    handles.append(hline)
    ax.set_xticks([])#np.linspace(width/2, left-width/2, count), tags, rotation=-75, fontsize=6, ha="left", va="top")

    ax.hlines(0, xmin=0, xmax=1, color="black", linewidth=0.8)
    ax.set_xlim(0,left)
    ax.set_ylim(*ylim)
    ax.set_yticks(np.arange(round(ylim[0], 1), round(ylim[1], 1) + 0.05, ytick_spacing))
    ax.set_yticklabels(["{}{}%".format("+" if y > 0 else "", int(y*100)) for y in np.arange(round(ylim[0], 1), round(ylim[1], 1) + 0.05, ytick_spacing)])
    ax.set_ylabel("Global Biodiversity footprint change")


    import matplotlib.transforms as transforms
    offset = transforms.ScaledTranslation(-width*2, 0, fig.dpi_scale_trans)
    for i, label in enumerate(ax.xaxis.get_majorticklabels()):
        label.set_transform(label.get_transform() + offset)
        label.set_color(tag_colors[i])

    ax.set_title("Biodiversity footprint change from 2010 to 2021")
    ax.legend(handles, labels, title="Impact weighted averages", title_fontsize=8,
        fontsize=6, ncol=2,
        handlelength=2,handler_map={tuple: HandlerTuple(ndivide=None)})
