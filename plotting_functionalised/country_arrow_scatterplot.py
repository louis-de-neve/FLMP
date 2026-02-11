import pandas as pd
import numpy as np
import math
import matplotlib.patches as mpatches


def country_arrowplot(ax, country_df_2010, country_df_2021, region_map, regions, beef_cons_2010):
    ax.set_xlim(1e-8, 1)
    ax.set_ylim(5e-11, 2e-5)
    ax.set_yscale("log")
    ax.set_xscale("log")




    def t1(z): return (ax.transData + ax.transAxes.inverted()).transform(z)
    def t2(z): return (ax.transAxes + ax.transData.inverted()).transform(z)

    for country in country_df_2021["ISO"].unique():
        try:
            row_2010 = country_df_2010[country_df_2010["ISO"]==country].iloc[0]
            row_2021 = country_df_2021[country_df_2021["ISO"]==country].iloc[0]
        except IndexError:
            continue

        x = row_2010["Production_kg"]/beef_cons_2010
        y = row_2010["E_per_kg"]
        x2 = row_2021["Production_kg"]/beef_cons_2010
        y2 = row_2021["E_per_kg"]
        dx = x2 - x
        dy = y2 - y
        color = region_map.loc[region_map["alpha-3"]==country]["Color"].values[0]
        if type(color)==float:
            color = "#ffffff00"
        line = ax.plot([x,x2],[y,y2], color)


        x_axes, y_axes = t1((x,y))
        x2_axes, y2_axes = t1((x2,y2))
        dx_axes = x2_axes - x_axes
        dy_axes = y2_axes - y_axes
        l = np.sqrt(dx_axes**2 + dy_axes**2)
        
        text_coords = t1((x,y))
        text_coords = text_coords - np.array([0.02 * dx_axes/l, 0.02 * dy_axes/l])
        text_coords = t2(text_coords)

        arrow_height = 0.015
        if arrow_height+0.005 > l:
            arrow_height = l - 0.005

        patch = mpatches.FancyArrow(x_axes,y_axes,dx_axes,dy_axes, width=0.001, ec=color, fc=color,
                                    linewidth=1, transform=ax.transAxes, length_includes_head=True,
                                    head_width=0.015, head_length=arrow_height)
        ax.add_patch(patch)

        angle = math.atan2(dy_axes, dx_axes)*(180/np.pi)+90
        if angle > 90 and angle < 270:
            angle = angle - 180

        line[0].set_color("#00000000")
        ax.text(*text_coords, s=row_2010["ISO"], fontsize=6, ha="center", va="center", color=color, rotation=angle)


    ax.set_title("Change in Beef impact between 2010 and 2021")
    ax.set_ylabel("Impact, Annual Extinctions per kg")
    ax.set_xlabel("Share of Global Beef Production")
    for _, row in regions.iterrows():
        ax.plot([], [], color=row["Color"], label=row["region"])
    ax.legend(title=f"Region", fontsize=6)



    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    total_grid_color = "#2F7FF8"
    for i in range(int(np.log10(x1*y1))-2, int(np.log10(x2*y2))+2):
        i = 10 ** (i)
        x = np.logspace(np.log10(x1)-1, np.log10(x2)+1, 50)
        y = i/x
        ax.plot(x, y, color=total_grid_color, alpha=0.4, linewidth=0.8, zorder=1)
    for j in range(int(np.log10(x1*y1))-2, int(np.log10(x2*y2))+2):
        for i in np.linspace(1*(10**j), 9*(10**j), 9):
            x = np.logspace(np.log10(x1)-1, np.log10(x2)+1, 50)
            y = i/x
            ax.plot(x, y, ls="dashed", color=total_grid_color, alpha=0.2, linewidth=0.8, zorder=1)
    ax3 = ax.twiny()
    ax3.set_xscale('log')
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    ax3.set_xlim(x1*y2, x2*y2)
    ax3.set_xlabel("Annual Extinctions per kg", color=total_grid_color)
    ax3.tick_params(axis='x', colors=total_grid_color)
        

