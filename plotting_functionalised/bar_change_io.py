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
    if label == "Other Fruit and vegetables":
        label = "Other Fruit\nand Vegetables"
    if label == "Soya beans":
        label = "Soya Beans                  \n\n\n"
    if label == "Chicken":
        label = "\n\n\n\n\n\nChicken              "
    if "Cow" in label:
        label = "Cow Milk"
    return label

def bar_plot_io(fig,ax:Axes, groups:list[Group], ylim:tuple[float, float], relative=True, ytick_spacing=0.2, secondary_groups=[None])->None:

    left = 0
    pad = 0.008

    groups = sorted(groups, key=lambda group: group.n)
    count = sum([len(g.commodities) for g in groups])
    width = 1/count - pad + pad/count
    t1 = 0
    t2 = 0
    labels = []
    handles = []
    class commods:
        def __init__(self, width, height, err, name, color, imported_height, imp_err):
            self.width = width
            self.height = height
            self.err = err
            self.name = name
            self.color = color
            self.imported_height = imported_height
            self.imp_err = imp_err

    commod_list = []
    g_names = [g.name for g in secondary_groups]
    for g in groups:
        commodities = sorted(g.commodities, key=lambda c: c.m)
        seconday_group_index = g_names.index(g.name)
        secondary_group = secondary_groups[seconday_group_index]
        seconday_commodities_names = [c.name for c in secondary_group.commodities]
        for c in commodities:
            height = (c.raw_vals[1] - c.raw_vals[0])/c.raw_vals[0]
            err = np.sqrt((c.errors[1]/c.raw_vals[1])**2 + (c.errors[0]/c.raw_vals[0])**2) * abs(height)
            if relative:
                width = c.yvals[0]*g.xvals[0]
                pad=0
            imported_height = 0
            imp_err = 0
            if c.name in seconday_commodities_names:
                print(height)
                c2 = secondary_group.commodities[seconday_commodities_names.index(c.name)]
                total_change = c.raw_vals[1] - c.raw_vals[0]
                imported_change = c2.raw_vals[1] - c2.raw_vals[0]
                domestic_change = total_change - imported_change
                height = domestic_change/c.raw_vals[0]
                imported_height = imported_change/c.raw_vals[0]  

                imp_err = np.sqrt((c2.errors[1]/c2.raw_vals[1])**2 + (c2.errors[0]/c2.raw_vals[0])**2) * abs(imported_height)
                err = np.sqrt(((c.errors[1]-c2.errors[1])/(c.raw_vals[1]-c2.raw_vals[1]))**2 + ((c.errors[0]-c2.errors[0])/(c.raw_vals[0]-c2.raw_vals[0]))**2) * abs(height)

                print(round(height, 3), round(imported_height, 3))


            com = commods(width, height, err, c.name, c.color, imported_height, imp_err)
            commod_list.append(com)




        t1 += g.dataframe(0)["bd_opp_total"].sum()
        t2 += g.dataframe(1)["bd_opp_total"].sum()

    commod_list = sorted(commod_list, key=lambda c:c.width, reverse=True)
    for c in commod_list:
        rect = mpatches.Rectangle((left, 0), c.width, c.height, color=c.color, zorder=1, linewidth=0)
        ax.add_patch(rect)
        if c.height>=0 and c.imported_height>+0:
            y = c.height
        elif c.height>=0 and c.imported_height<0:
            y = 0
        elif c.height<0 and c.imported_height>=0:
            y = 0
        else:
            y = c.height

        rect2 = mpatches.Rectangle((left, y), c.width, c.imported_height, color=c.color, zorder=1.5, linewidth=0)
        ax.add_patch(rect2)
        rect2 = mpatches.Rectangle((left, y), c.width, c.imported_height, color="black", alpha=0.5, zorder=1.5, fill=False, linewidth=0, hatch="xxx", hatch_linewidth=1)
        ax.add_patch(rect2)
        if y == 0:
            ax.errorbar(left + c.width/2, c.imported_height, yerr=c.imp_err, color="black", capsize=2, fmt="none", linewidth=0.8, zorder=3)
            ax.errorbar(left + c.width/2, c.height, yerr=c.err, color="black", capsize=2, fmt="none", linewidth=0.8, zorder=3)
        else:
            ax.errorbar(left + c.width/2, c.height+c.imported_height, yerr=c.err+c.imp_err, color="black", capsize=2, fmt="none", linewidth=0.8, zorder=3)
        
        va = "center" if "Chicken" in tag_formatting(c.name) else "bottom"

        text_pos = 0
        if c.imported_height>0:
            text_pos += c.imported_height + c.imp_err
        if c.height>0:
            text_pos += c.height + c.err

        ax.text(left+c.width/2, text_pos+ylim[1]/50, tag_formatting(c.name), fontsize=6, ha="center", va=va, zorder=4)

        left += c.width+pad

        
        #hline = ax.hlines(g_avg, xmin=g_start, xmax=g_end, color=g.color, linewidth=0.8,
        #                  label=tag_formatting(g.name), linestyle=[(3, (3, 3))], gapcolor='white', zorder=2)
        #labels.append(tag_formatting(g.name))
        #handles.append(hline)

    total_average = (t2-t1)/t1
    hline = ax.hlines(total_average, xmin=0, xmax=1, color="#888888", linewidth=0.8, linestyle=[(3, (3, 3))], gapcolor='white', zorder=0.5, label="Total Average")
    labels.append(f"Total: {'{}{}%'.format("+" if total_average > 0 else "", int(total_average*100))}")
    handles.append(hline)
    ax.set_xticks(np.linspace(0, 1, 11), [f"{int(i*100)}%" for i in np.linspace(0, 1, 11)], color="black")

    rect1 = mpatches.Rectangle((-1, 0), 0, 0, color="#D55E00", zorder=1.5, linewidth=0)
    rect2 = mpatches.Rectangle((-1, 0), 0, 0, color="#D55E00", zorder=1.5, linewidth=0)
    rect3 = mpatches.Rectangle((-1, 0), 0, 0, color="black", alpha=0.5, zorder=1.6, fill=False, linewidth=0, hatch="xxxx", hatch_linewidth=5)
    ax.legend([(rect2, rect3), rect1, hline], ["Imported products", "Domestic products", "Average Impact Change"], title="Impact Source", handlelength=2)
    # rect2 = mpatches.Rectangle((left, y), c.width, c.imported_height, color="black", alpha=0.5, zorder=1.5, fill=False, linewidth=0, hatch="x", hatch_linewidth=3)
    # ax.add_patch(rect2)

    ax.hlines(0, xmin=0, xmax=1, color="black", linewidth=0.8)
    ax.set_xlim(0,left)
    ax.set_ylim(*ylim)
    ax.set_yticks(np.arange(round(ylim[0], 1), round(ylim[1], 1) + 0.05, ytick_spacing))
    ax.set_yticklabels(["{}{}%".format("+" if y > 0 else "", int(y*100)) for y in np.arange(round(ylim[0], 1), round(ylim[1], 1) + 0.05, ytick_spacing)])
    ax.set_ylabel("2010-2020 difference in Mean Species\nExtinction Risk over next 100 years")
    ax.set_xlabel("2010 Impact Share")

    ax.set_title("Biodiversity footprint change of\ntop 10 commodities from 2010 to 2021")
    # ax.legend(handles, labels, title="Impact weighted averages", title_fontsize=8,
    #     fontsize=6, ncol=2,
    #     handlelength=2,handler_map={tuple: HandlerTuple(ndivide=None)})
