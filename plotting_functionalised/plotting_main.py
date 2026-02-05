import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.legend_handler import HandlerPatch
import numpy as np
from mosaics import mosaic_plotting, label_formatting, Group, Commodity
from bar_change import bar_plot
from cons_impact_scatter import cons_impact_plot

def six_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(10, 15))

    fwidth = 0.5
    fheight = 1/3
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03

    offset3 = 0.06
    shift34 = 0.03

    ax1 = fig.add_axes((xpad+left_margin, 2*fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, 2*fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))

    ax3 = fig.add_axes((xpad+left_margin, fheight + ypad + offset3 + shift34, fwidth - 2*xpad, fheight - 2*ypad - offset3))
    ax4 = fig.add_axes((fwidth + xpad+left_margin/2, fheight + ypad + shift34, fwidth - 2*xpad, fheight - 2*ypad))

    ax5 = fig.add_axes((xpad+left_margin, ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax6 = fig.add_axes((fwidth + xpad+left_margin/2, ypad, fwidth - 2*xpad, fheight - 2*ypad))

    axs = np.array([[ax1, ax2], [ax3, ax4], [ax5, ax6]])
    return fig, axs

def four_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(10, 10))

    fwidth = 0.5
    fheight = 0.5
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03

    offset3 = 0.06
    shift34 = 0.03


    ax1 = fig.add_axes((xpad+left_margin, fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))

    ax3 = fig.add_axes((xpad+left_margin, ypad + offset3 + shift34, fwidth - 2*xpad, fheight - 2*ypad - offset3))
    ax4 = fig.add_axes((fwidth + xpad+left_margin/2, ypad + shift34, fwidth - 2*xpad, fheight - 2*ypad))

    axs = np.array([[ax1, ax2], [ax3, ax4]])
    return fig, axs


def world_setup():

    fig, axs = six_axes_setup()
    # Data import
    df_2010 = pd.read_csv(f'../results/{2010}/world_aggregate_impacts.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/world_aggregate_impacts.csv')

    for col in ["bd_opp_total", "Cons", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 6948574560
        df_2021[col] = df_2021[col] / 7927332080

    groups = mosaic_plotting(axs[0,0], axs[0,1], df_2010, df_2021)
    bar_plot(fig, axs[1,0], groups, (-0.7, 0.92))
    cons_impact_plot(axs[1,1], groups)
    plt.savefig('../outputs/Global_group_mosaics.png', dpi=600)


def country_setup():
    c="CHN"
    fig, axs = four_axes_setup()
    # Data import
    df_2010 = pd.read_csv(f'../results/{2010}/{c}/impacts_aggregated.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/impacts_aggregated.csv')

    for col in ["bd_opp_total", "Cons", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 1.43e9
        df_2021[col] = df_2021[col] / 1.35e9

    groups = mosaic_plotting(axs[0,0], axs[0,1], df_2010, df_2021)
    bar_plot(fig, axs[1,0], groups, (-1., 3.))
    cons_impact_plot(axs[1,1], groups)
    plt.suptitle(c)
    plt.savefig(f'../outputs/mosaics/{c}.png', dpi=600)

country_setup()

exit()






regions = pd.DataFrame({'Asia' : "#df9903eb",
                'Europe' : "#2b56e2aa",
                'Americas' : "#36ad36c6",
                'Africa' : "#ff0000aa",
                'Oceania': "#f700ffaa",
                }.items(), columns=["region", "Color"])

region_map = pd.read_csv("../input_data/regions.csv")[["alpha-3", "region"]]
region_map = region_map.merge(regions, on="region", how="left")

# Plots 5 and 6
ax = axs[2, 0]
ax2 = axs[2, 1]

cdat = pd.read_excel("../input_data/nocsDataExport_20251021-164754.xlsx")
COUNTRIES = [_.upper() for _ in cdat["ISO3"].unique().tolist() if isinstance(_, str)]

feed_df_2010 = pd.DataFrame()
feed_df_2021 = pd.DataFrame()
pasture_df_2010 = pd.DataFrame()
pasture_df_2021 = pd.DataFrame()

for country in COUNTRIES:
    try:
        cdf_2010 = pd.read_csv(f'../results/{2010}/{country}/impacts_full.csv')
    except FileNotFoundError:
        continue
    try:
        cdf_2021 = pd.read_csv(f'../results/{2021}/{country}/impacts_full.csv')
    except FileNotFoundError:
        continue

    cdf_2010 = cdf_2010[["Producer_Country_Code", "Consumer_Country_Code", "Item", "ItemT_Name", "bd_opp_cost_calc", "provenance", "bd_opp_cost_m2", "Pasture_avg_calc", "FAO_land_calc_m2", "Country_ISO"]]
    cdf_2021 = cdf_2021[["Producer_Country_Code", "Consumer_Country_Code", "Item", "ItemT_Name", "bd_opp_cost_calc", "provenance", "bd_opp_cost_m2", "Pasture_avg_calc", "FAO_land_calc_m2", "Country_ISO"]]
    feed_2010 = cdf_2010[(cdf_2010["ItemT_Name"]=="Meat of cattle with the bone; fresh or chilled")&(cdf_2010["FAO_land_calc_m2"]!=0)].copy()
    feed_2021 = cdf_2021[(cdf_2021["ItemT_Name"]=="Meat of cattle with the bone; fresh or chilled")&(cdf_2021["FAO_land_calc_m2"]!=0)].copy()
    past_2010 = cdf_2010[(cdf_2010["ItemT_Name"]=="Meat of cattle with the bone; fresh or chilled")&(cdf_2010["FAO_land_calc_m2"]==0)].copy()
    past_2021 = cdf_2021[(cdf_2021["ItemT_Name"]=="Meat of cattle with the bone; fresh or chilled")&(cdf_2021["FAO_land_calc_m2"]==0)].copy()

    feed_df_2010 = pd.concat([feed_df_2010, feed_2010], ignore_index=True)
    feed_df_2021 = pd.concat([feed_df_2021, feed_2021], ignore_index=True)
    pasture_df_2010 = pd.concat([pasture_df_2010, past_2010], ignore_index=True)
    pasture_df_2021 = pd.concat([pasture_df_2021, past_2021], ignore_index=True)

Country_df_2010 = pd.DataFrame()
Country_df_2021 = pd.DataFrame()


for country in pasture_df_2010["Producer_Country_Code"].unique():
    country_feed_2010 = feed_df_2010[feed_df_2010["Consumer_Country_Code"]==country]
    country_pasture_2010 = pasture_df_2010[pasture_df_2010["Producer_Country_Code"]==country]
    iso = country_pasture_2010["Country_ISO"].iloc[0]

    E = country_feed_2010["bd_opp_cost_calc"].sum() + country_pasture_2010["bd_opp_cost_calc"].sum()
    Production = country_pasture_2010["provenance"].sum()*1000
    E_per_kg = E / Production

    Pasture_m2_per_kg = country_pasture_2010["Pasture_avg_calc"].sum() / Production
    Pasture_E_per_m2 = country_pasture_2010["bd_opp_cost_calc"].sum() / country_pasture_2010["Pasture_avg_calc"].sum()

    Feed_m2_per_kg = country_feed_2010["FAO_land_calc_m2"].sum() / Production
    Feed_E_per_m2 = country_feed_2010["bd_opp_cost_calc"].sum() / country_feed_2010["FAO_land_calc_m2"].sum()

    cdf_2010 = pd.DataFrame({"ISO":[iso],
                            "E":[E],
                            "E_per_kg":[E_per_kg],
                            "Production_kg":[Production],
                            "Pasture_m2_per_kg":[Pasture_m2_per_kg],
                            "Pasture_E_per_m2":[Pasture_E_per_m2],
                            "Feed_m2_per_kg":[Feed_m2_per_kg],
                            "Feed_E_per_m2":[Feed_E_per_m2]
                            })

    Country_df_2010 = pd.concat([Country_df_2010, cdf_2010], ignore_index=True)

for country in pasture_df_2021["Producer_Country_Code"].unique():
    country_feed_2021 = feed_df_2021[feed_df_2021["Consumer_Country_Code"]==country]
    country_pasture_2021 = pasture_df_2021[pasture_df_2021["Producer_Country_Code"]==country]
    iso = country_pasture_2021["Country_ISO"].iloc[0]

    E = country_feed_2021["bd_opp_cost_calc"].sum() + country_pasture_2021["bd_opp_cost_calc"].sum()
    Production = country_pasture_2021["provenance"].sum()*1000
    E_per_kg = E / Production

    Pasture_m2_per_kg = country_pasture_2021["Pasture_avg_calc"].sum() / Production
    Pasture_E_per_m2 = country_pasture_2021["bd_opp_cost_calc"].sum() / country_pasture_2021["Pasture_avg_calc"].sum()

    Feed_m2_per_kg = country_feed_2021["FAO_land_calc_m2"].sum() / Production
    Feed_E_per_m2 = country_feed_2021["bd_opp_cost_calc"].sum() / country_feed_2021["FAO_land_calc_m2"].sum()

    cdf_2021 = pd.DataFrame({"ISO":[iso],
                            "E":[E],
                            "E_per_kg":[E_per_kg],
                            "Production_kg":[Production],
                            "Pasture_m2_per_kg":[Pasture_m2_per_kg],
                            "Pasture_E_per_m2":[Pasture_E_per_m2],
                            "Feed_m2_per_kg":[Feed_m2_per_kg],
                            "Feed_E_per_m2":[Feed_E_per_m2]
                            })

    Country_df_2021 = pd.concat([Country_df_2021, cdf_2021], ignore_index=True)


ax.set_xlim(1e-8, 1)
ax.set_ylim(5e-11, 2e-5)
ax.set_yscale("log")
ax.set_xscale("log")

ax2.set_xlim(-0.75, 0.75)
ax2.set_ylim(-0.75, 0.75)


prod_max = Country_df_2010["Production_kg"].max()
impact_max = Country_df_2010["E"].max()
temp = []
for country in Country_df_2021["ISO"].unique():
    try:
        row_2010 = Country_df_2010[Country_df_2010["ISO"]==country].iloc[0]
        row_2021 = Country_df_2021[Country_df_2021["ISO"]==country].iloc[0]
    except IndexError:
        continue
    if country == "USA" or country == "NAM":
        print(f"{row_2010["Production_kg"]:,}")

    x = row_2010["Production_kg"]/beef_cons_2010
    y = row_2010["E_per_kg"]
    x2 = row_2021["Production_kg"]/beef_cons_2010
    y2 = row_2021["E_per_kg"]
    dx = x2 - x
    dy = y2 - y
    color = region_map.loc[region_map["alpha-3"]==country]["Color"].values[0]
    if type(color)==float:
        print(country)
        color = "#ffffff00"
    line = ax.plot([x,x2],[y,y2], color)
    # color = line[0].get_color()
  

    def t1(z): return (ax.transData + ax.transAxes.inverted()).transform(z)
    def t2(z): return (ax.transAxes + ax.transData.inverted()).transform(z)

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



    area_2010 = (row_2010["Pasture_m2_per_kg"] + row_2010["Feed_m2_per_kg"]) * row_2010["Production_kg"]
    area_2021 = (row_2021["Pasture_m2_per_kg"] + row_2021["Feed_m2_per_kg"]) * row_2021["Production_kg"]
    bd_cost1 = row_2010["E"] / area_2010
    eff1 = area_2010 / row_2010["Production_kg"]
    bd_cost2 = row_2021["E"] / area_2021
    eff2 = area_2021 / row_2021["Production_kg"]

    y_change = (eff2 - eff1) / eff1
    x_change = (bd_cost2 - bd_cost1) / bd_cost1


    width = (np.log10(row_2010["Production_kg"]) / np.log10(prod_max) - 0.6) * 0.05
    color = color[:-2]
    # temp.append(alpha)
    # alpha = min(1.0, alpha)
    # color = f"{color[:-2]}{int(alpha*255):02x}"

    patch = mpatches.FancyArrow(0,0,x_change,y_change, ec=color, fc=color, length_includes_head=True,
                                width=width, head_width=3*width, head_length=3*width, zorder=3+width, lw=0)

    l = np.sqrt(x_change**2 + y_change**2)
    x_offset = 0.04 * x_change/l
    y_offset = 0.04 * y_change/l
    text_x = x_change + x_offset
    text_y = y_change + y_offset

    angle = math.atan2(y_change, x_change)*(180/np.pi)+90
    if angle > 90 and angle < 270:
        angle = angle - 180

    if country == "USA":
        print(width)
   
    if row_2010["E"] > impact_max/30:
        ax2.add_patch(patch)
        ax2.text(text_x, text_y, s=row_2010["ISO"], fontsize=6, ha="center", va="center", color="#000000", rotation=angle, zorder=4)
        temp.append((row_2010["ISO"], row_2010["Production_kg"], width))


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
    

ax2.set_title("Change in Beef impact per kg between 2010 and 2021")
ax2.set_xlabel(r"Change in Biodiversity Opportunity Cost per m$^2$")
ax2.set_ylabel(r"Change in Land use per kg")




tick_locs = [-0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75]
tick_labels = ["-75%", "-50%", "-25%", "0%", "+25%", "+50%", "+75%"]
ax2.set_xticks(tick_locs, tick_labels)
ax2.set_yticks(tick_locs, tick_labels)
ax2.grid(zorder=0)
ax2.axhline(0, color="black", linewidth=0.8, zorder=1)
ax2.axvline(0, color="black", linewidth=0.8, zorder=1)
xs = np.linspace(-1, 1, 100)
ys = -xs/(1+xs)
ys[0] = 2
ax2.plot(xs, ys, ls="dashed", color="grey", linewidth=0.8, zorder=2, label="Iso-impact line")
ax2.fill_between(xs, ys, -1, color="#d0f0d0", zorder=0, label="Impact decrease")
ax2.fill_between(xs, ys, 1, color="#f0d0d0", zorder=0, label="Impact increase")
leg = ax2.legend(fontsize=6, loc="upper right")
ax2.add_artist(leg)

for i, wt in enumerate([(1e7, "10 kt"), (1e8, "100 kt"), (1e9, "1 Mt"), (1e10, "10 Mt")]):
    j, text = wt
    width = (np.log10(j) / np.log10(prod_max) - 0.6) * 0.05
    patch = mpatches.FancyArrow(0.62,-0.55-0.053*i,0.11,0, width=width, ec="black", fc="black",
                                length_includes_head=True, head_width=3*width, head_length=3*width, lw=0)
    ax2.add_patch(patch)
    ax2.text(0.6, -0.55-0.053*i, text, va="center", ha="right", fontsize=6)
ax2.text(0.63, -0.495, "Production", va="bottom", ha="center", fontsize=7)


plt.savefig('../outputs/Global_group_mosaics_vectors.png', dpi=600)














# handles, labels = [], []
# for i, text in [(1e8, "100 kt"), (1e9, "1 Mt"), (1e10, "10 Mt")]:
#     width = (np.log10(i) / np.log10(prod_max) - 0.65) * 0.05
#     patch = mpatches.FancyArrow(2,2,0,0, width=width, label=width, ec="black", fc="black",
#                                 length_includes_head=True, head_width=3*width, head_length=3*width,)
#     p = ax2.add_patch(patch)
#     handles.append(p)
#     labels.append(text)
# class ArrowLegendHandler(HandlerPatch):
#     def create_artists(self, legend, orig_handle,
#                        xdescent, ydescent,
#                        width, height, fontsize, trans):
#         a = orig_handle.axes.transData  # type: ignore
#         def delta_transform(dx, dy):
#             top = np.asarray((trans.inverted()+a).transform([dx[0], dy[0]]))
#             bottom = np.asarray((trans.inverted()+a).transform([dx[1], dy[1]])) 
#             delta = bottom-top
#             return delta
#         thick = delta_transform([0,orig_handle._width], [0,0])[0] # type: ignore
#         head_thick = delta_transform([0,3*orig_handle._width], [0,0])[0] # type: ignore
#         print(thick, orig_handle._width, head_thick) # type: ignore
#         head_length = delta_transform([0,0], [0,3*orig_handle._width])[1] # type: ignore

#         p = mpatches.FancyArrow(0, 0.5*height, width, 0, width=thick, lw=0, length_includes_head=True,
#                                 head_width=3*thick, head_length=head_length, ec="#00000000", fc="black")
#         return [p]
# ax2.legend(handles, labels, title="Production", loc="lower right", frameon=False, markerfirst=False,
#            fontsize=6, handlelength=3.5, labelspacing=1,  title_fontsize=7,
#            handler_map={mpatches.FancyArrow : ArrowLegendHandler()})