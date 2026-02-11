import numpy as np
import matplotlib.patches as mpatches
from vectorplot import vectorplot_setup, plot_vector
from mosaics import Group
from bar_change import tag_formatting

def country_vectorplot(ax2, country_df_2010, country_df_2021, region_map):
    ax2.set_xlim(-0.75, 0.75)
    ax2.set_ylim(-0.75, 0.75)
    vectorplot_setup(ax2)

    prod_max = country_df_2010["Production_kg"].max()
    impact_max = country_df_2010["E"].max()


    for country in country_df_2021["ISO"].unique():
        try:
            row_2010 = country_df_2010[country_df_2010["ISO"]==country].iloc[0]
            row_2021 = country_df_2021[country_df_2021["ISO"]==country].iloc[0]
        except IndexError:
            continue

        area_2010 = (row_2010["Pasture_m2_per_kg"] + row_2010["Feed_m2_per_kg"]) * row_2010["Production_kg"]
        area_2021 = (row_2021["Pasture_m2_per_kg"] + row_2021["Feed_m2_per_kg"]) * row_2021["Production_kg"]
        bd_cost1 = row_2010["E"] / area_2010
        eff1 = area_2010 / row_2010["Production_kg"]
        bd_cost2 = row_2021["E"] / area_2021
        eff2 = area_2021 / row_2021["Production_kg"]

        y_change = (eff2 - eff1) / eff1
        x_change = (bd_cost2 - bd_cost1) / bd_cost1
        width = (np.log10(row_2010["Production_kg"]) / np.log10(prod_max) - 0.6) * 0.05


        color = region_map.loc[region_map["alpha-3"]==country]["Color"].values[0]
        if type(color)==float:
            color = "#ffffff00"
        color = color[:-2]


        if row_2010["E"] > impact_max/30:
            plot_vector(ax2, x_change, y_change, width, color, row_2010["ISO"])



    for i, wt in enumerate([(1e7, "10 kt"), (1e8, "100 kt"), (1e9, "1 Mt"), (1e10, "10 Mt")]):
        j, text = wt
        width = (np.log10(j) / np.log10(prod_max) - 0.6) * 0.05
        patch = mpatches.FancyArrow(0.62,-0.55-0.053*i,0.11,0, width=width, ec="black", fc="black",
                                    length_includes_head=True, head_width=3*width, head_length=3*width, lw=0)
        ax2.add_patch(patch)
        ax2.text(0.6, -0.55-0.053*i, text, va="center", ha="right", fontsize=6)
    ax2.text(0.63, -0.495, "Production", va="bottom", ha="center", fontsize=7)
   
   
def commodity_vectorplot(ax, groups:list[Group], pops:list[int]):
    ax.set_xlim(-0.5, 0.25)
    ax.set_ylim(-0.5, 0.25)

    impact_max = max([commodity.raw_vals[0] for group in groups for commodity in group.commodities]) * pops[0]
    def width_calc(x):
        return ((np.log10(x) / np.log10(impact_max))-0.01) * 0.012


    for group in groups:
        for commodity in group.commodities:
            eff1 = commodity.area[0] / commodity.cons[0]  if commodity.cons[0] != 0 else 0
            eff2 = commodity.area[1] / commodity.cons[1]  if commodity.cons[1] != 0 else 0
            bd_cost1 = commodity.raw_vals[0] / commodity.area[0]  if commodity.area[0] != 0 else 0
            bd_cost2 = commodity.raw_vals[1] / commodity.area[1]  if commodity.area[1] != 0 else 0

            y_change = (eff2 - eff1) / eff1 if eff1 != 0 else 0
            x_change = (bd_cost2 - bd_cost1) / bd_cost1 if bd_cost1 != 0 else 0
            width = width_calc(commodity.raw_vals[0]*pops[0])
            color = commodity.color
            label = tag_formatting(commodity.name)

            if width > width_calc(46.9):
                plot_vector(ax, x_change, y_change, width, color, label, text_offset=0.02)


    vectorplot_setup(ax)

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    for i, wt in enumerate([(46.9*20, "20%"), (469, "10%"), (46.9*5, "5%"), (46.9, "1%")]):
        j, text = wt
        width = width_calc(j)
        patch = mpatches.FancyArrow(xmax-0.13,ymin+0.15-0.04*i,0.11,0, width=width, ec="black", fc="black",
                                    length_includes_head=True, head_width=3*width, head_length=3*width, lw=0)
        ax.add_patch(patch)
        ax.text(xmax-0.15, ymin+0.15-0.04*i, text, va="center", ha="right", fontsize=6)
    ax.text(xmax-0.10, ymin+0.18, "Impact share", va="bottom", ha="center", fontsize=7)


def feedpasture_vectorplot(ax, ax2, country_df_2010, country_df_2021, region_map):
    ax2.set_xlim(-1, 1)
    ax2.set_ylim(-1, 1)
    vectorplot_setup(ax2)
    ax.set_xlim(-0.75, 0.75)
    ax.set_ylim(-0.75, 0.75)
    vectorplot_setup(ax)


    prod_max = country_df_2010["Production_kg"].max()
    impact_max = country_df_2010["Pasture_E"].max()


    for country in country_df_2021["ISO"].unique():
        try:
            row_2010 = country_df_2010[country_df_2010["ISO"]==country].iloc[0]
            row_2021 = country_df_2021[country_df_2021["ISO"]==country].iloc[0]
        except IndexError:
            continue

        area_2010 = (row_2010["Pasture_m2_per_kg"]) * row_2010["Production_kg"]
        area_2021 = (row_2021["Pasture_m2_per_kg"]) * row_2021["Production_kg"]
        bd_cost1 = row_2010["Pasture_E"] / area_2010
        eff1 = area_2010 / row_2010["Production_kg"]
        bd_cost2 = row_2021["Pasture_E"] / area_2021
        eff2 = area_2021 / row_2021["Production_kg"]

        y_change = (eff2 - eff1) / eff1
        x_change = (bd_cost2 - bd_cost1) / bd_cost1
        width = (np.log10(row_2010["Production_kg"]) / np.log10(prod_max) - 0.6) * 0.05


        color = region_map.loc[region_map["alpha-3"]==country]["Color"].values[0]
        if type(color)==float:
            color = "#ffffff00"
        color = color[:-2]


        if row_2010["E"] > impact_max/30:
            plot_vector(ax, x_change, y_change, width, color, row_2010["ISO"])
    for i, wt in enumerate([(1e7, "10 kt"), (1e8, "100 kt"), (1e9, "1 Mt"), (1e10, "10 Mt")]):
        j, text = wt
        width = (np.log10(j) / np.log10(prod_max) - 0.6) * 0.05
        patch = mpatches.FancyArrow(0.62,-0.55-0.053*i,0.11,0, width=width, ec="black", fc="black",
                                    length_includes_head=True, head_width=3*width, head_length=3*width, lw=0)
        ax.add_patch(patch)
        ax.text(0.6, -0.55-0.053*i, text, va="center", ha="right", fontsize=6)
    ax.text(0.63, -0.495, "Production", va="bottom", ha="center", fontsize=7)
   


    for country in country_df_2021["ISO"].unique():
        try:
            row_2010 = country_df_2010[country_df_2010["ISO"]==country].iloc[0]
            row_2021 = country_df_2021[country_df_2021["ISO"]==country].iloc[0]
        except IndexError:
            continue

        area_2010 = (row_2010["Feed_m2_per_kg"]) * row_2010["Production_kg"]
        area_2021 = (row_2021["Feed_m2_per_kg"]) * row_2021["Production_kg"]
        bd_cost1 = row_2010["Feed_E"] / area_2010
        eff1 = area_2010 / row_2010["Production_kg"]
        bd_cost2 = row_2021["Feed_E"] / area_2021
        eff2 = area_2021 / row_2021["Production_kg"]

        y_change = (eff2 - eff1) / eff1
        x_change = (bd_cost2 - bd_cost1) / bd_cost1
        width = (np.log10(row_2010["Production_kg"]) / np.log10(prod_max) - 0.6) * 0.05


        color = region_map.loc[region_map["alpha-3"]==country]["Color"].values[0]
        if type(color)==float:
            color = "#ffffff00"
        color = color[:-2]


        if row_2010["E"] > impact_max/30:
            plot_vector(ax2, x_change, y_change, width, color, row_2010["ISO"])
