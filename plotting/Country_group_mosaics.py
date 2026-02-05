import math
import pandas as pd
import matplotlib.transforms as transforms
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

ISO = "CHN"

# Figure setup
fig = plt.figure(figsize=(10, 10))

fwidth = 0.5
fheight = 0.5
fpad = 0.1
xpad = fpad * fwidth
ypad = fpad * fheight
left_margin = 0.03

offset3 = 0.07
shift34 = 0.013

ax1 = fig.add_axes((xpad+left_margin, fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))
ax2 = fig.add_axes((fwidth + xpad+left_margin/2, fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))

ax3 = fig.add_axes((xpad+left_margin,  ypad + offset3 + shift34, fwidth - 2*xpad, fheight - 2*ypad - offset3))
ax4 = fig.add_axes((fwidth + xpad+left_margin/2, ypad + shift34, fwidth - 2*xpad, fheight - 2*ypad))
axs = np.array([[ax1, ax2], [ax3, ax4]])


# reference data & functions
colors = pd.DataFrame({'Grains, roots, starchy carbohydrates' : "#E69F00",
                'Legumes, beans, nuts' : "#F0E442",
                'Fruit and vegetables' : "#009E73",
                'Stimulants and spices' : "#56B4E9",
                'Ruminant meat' : "#D55E00", 
                'Dairy and eggs' : "#0072B2",
                'Poultry and pig meat' : "#CC79A7", 
                'Sugar crops' : "#93F840"
                }.items(), columns=["Group", "Color"])

colors2 = pd.DataFrame({'Grains, roots, starchy carbohydrates' : "#ffd066",
                'Legumes, beans, nuts' : "#f7f1a1",
                'Fruit and vegetables' : "#00ffba",
                'Stimulants and spices' : "#a5d7f3",
                'Ruminant meat' : "#ffaa66", 
                'Dairy and eggs' : "#33b6ff",
                'Poultry and pig meat' : "#e3b5ce", 
                'Sugar crops' : "#c7fb9d"
                }.items(), columns=["Group", "Color2"])

order = pd.DataFrame({'Grains, roots, starchy carbohydrates' : 3,
                'Legumes, beans, nuts' : 5,
                'Fruit and vegetables' : 4,
                'Stimulants and spices' : 6,
                'Ruminant meat' : 0, 
                'Dairy and eggs' : 2,
                'Poultry and pig meat' : 1, 
                'Sugar crops' : 7
                }.items(), columns=["Group", "Order"])

def label_formatting(label):
    if "Other" in label:
        label = "Other"
    if ";" in label:
        label = label.split(";")[0]
    if "with the bone" in label:
        label = label.replace("with the bone", "")
    if "Cashew" in label:
        label = "Cashews"
    if "Oil palm" in label:
        label = "Palm oil"
    return label


# Data import
df_2010 = pd.read_csv(f'../results/{2010}/{ISO}/impacts_aggregated.csv')
df_2021 = pd.read_csv(f'../results/{2021}/{ISO}/impacts_aggregated.csv')

# df_2010 = pd.read_csv(f'../results/{2010}/world_aggregate_impacts.csv')
# df_2021 = pd.read_csv(f'../results/{2021}/world_aggregate_impacts.csv')

for col in ["bd_opp_total", "Cons", "bd_opp_total_err"]:
    df_2010[col] = df_2010[col] / 6948574560 # TODO replace with country pop
    df_2021[col] = df_2021[col] / 7927332080 # TODO replace with country pop

print(df_2010["bd_opp_total"].sum())
print(df_2021["bd_opp_total"].sum())

print(df_2010["Cons"].sum())
print(df_2021["Cons"].sum())


# Axes manipulation for scale
total_2010 = df_2010["bd_opp_total"].sum()
total_2021 = df_2021["bd_opp_total"].sum()

if total_2010 > total_2021:
    axis_to_change = axs[0,1]
else:
    axis_to_change = axs[0,0]
larger_total = max(total_2010, total_2021)
smaller_total = min(total_2010, total_2021)
new_length_ratio = np.sqrt(smaller_total / larger_total)
delta = (1 - new_length_ratio)/2

current_pos = axis_to_change.get_position()
current_dim = (current_pos.x1 - current_pos.x0, current_pos.y1 - current_pos.y0)
delta_dim = (current_dim[0]*delta, current_dim[1]*delta)
new_pos = transforms.Bbox([[current_pos.x0 + delta_dim[0], current_pos.y0 + 2*delta_dim[1]], [current_pos.x1 - delta_dim[0], current_pos.y1]])
axis_to_change.set_position(new_pos)


# initialisation for plotting
default_pad = 0.005
other_condition = 10
plot_order = []
color_order = []

# Top two axes: mosaics by group + item for 2010 and 2021
for i, df in enumerate([df_2010, df_2021]):
    if df["bd_opp_total"].sum() == larger_total:
        pad = default_pad* new_length_ratio
    else:
        pad = default_pad
    xpad = pad
    df = df[["Item", "Group", "bd_opp_total", "Cons"]]
    df2 = df[["Group", "bd_opp_total", "Cons"]].copy()
    df_grouped = df2.groupby("Group").sum().reset_index()
    df_grouped = df_grouped.merge(colors, on="Group", how="left")
    df_grouped = df_grouped.merge(colors2, on="Group", how="left")
    df_grouped = df_grouped.merge(order, on="Group", how="left")
    df_grouped = df_grouped.sort_values("Order")

    total_bd_opp = df_grouped["bd_opp_total"].sum()
    df_grouped["bd_opp_perc"] = df_grouped["bd_opp_total"] / total_bd_opp
    
    left = 0
    for _, row in df_grouped.iterrows():
        group_df = df[df["Group"] == row["Group"]].copy()
        group_df = group_df.sort_values("bd_opp_total", ascending=False)
        group_df["group_bd_opp_perc"] = group_df["bd_opp_total"] / group_df["bd_opp_total"].sum()


        other_categories = group_df[group_df["Item"].str.contains("Other")]["Item"].tolist()
        others = group_df[(group_df["group_bd_opp_perc"] < other_condition*pad)|(group_df["Item"].isin(other_categories))]
        if len(others) > 1:
            others_sum = others["group_bd_opp_perc"].sum()
            group_df = group_df[(group_df["group_bd_opp_perc"] >= other_condition*pad) & (~group_df["Item"].isin(other_categories))]
            others_row = pd.DataFrame({"Item": [f"Others_{row["Group"]}"], "Group": [row["Group"]], "bd_opp_total": [0], "Cons": [0], "group_bd_opp_perc": [others_sum]})
            group_df = pd.concat([group_df, others_row], ignore_index=True)

        cmap = LinearSegmentedColormap.from_list("custom_cmap", [row["Color"], row["Color2"]])
        up = 0

        for j, item_row in group_df.iterrows():
            if item_row["group_bd_opp_perc"]-2*pad > 0:
                rect = mpatches.Rectangle((left+xpad, up+pad), row["bd_opp_perc"]-2*xpad, item_row["group_bd_opp_perc"]-2*pad, color=cmap(up))
                axs[0,i].add_patch(rect)
                if i == 0:
                    plot_order.append(item_row["Item"])
                    color_order.append(cmap(up))


            text_color = "white" if row["Group"] == "Dairy and eggs" else "black"
            if (row["bd_opp_perc"] > 0.1) and (item_row["group_bd_opp_perc"] > 0.05):
                label = label_formatting(item_row["Item"])
                axs[0,i].text(left + row["bd_opp_perc"]/2, up + item_row["group_bd_opp_perc"]/2, label, ha="center", va="center", fontsize=6, color=text_color)

            elif (row["bd_opp_perc"] > 0.04) and (item_row["group_bd_opp_perc"] > 0.1):
                label = label_formatting(item_row["Item"])
                axs[0,i].text(left + row["bd_opp_perc"]/2, up + item_row["group_bd_opp_perc"]/2, label, ha="center", va="center", fontsize=6, rotation=90, color=text_color)
            
            up += item_row["group_bd_opp_perc"]
        left += row["bd_opp_perc"]
    

    axs[0, i].set_xlim(0,1)
    axs[0, i].set_ylim(0,1)
    axs[0, i].set_xticks([])
    axs[0, i].set_yticks([])
    axs[0, i].axis('off')
axs[0,0].set_title("2010", fontsize=14)
axs[0,1].set_title("2021", fontsize=14)
plot_order.append("Sugar beet")
color_order.append("#c7fb9d")


# Middle two axes: Waterfall charts for bd change and consumption change

ax = axs[1,0]
df = df_2010.copy()
df = df.merge(df_2021[["Item", "bd_opp_total",  "bd_opp_total_err"]], on="Item", suffixes=("_2010", "_2021"))
df["bd_opp_change"] = df["bd_opp_total_2021"] - df["bd_opp_total_2010"]
df["bd_opp_perc_err"] = np.sqrt((df["bd_opp_total_err_2021"]/df["bd_opp_total_2021"])**2 + (df["bd_opp_total_err_2010"]/df["bd_opp_total_2010"])**2)

non_other_df = df[df["Item"].isin(plot_order)].copy()
other_df = df[~df["Item"].isin(plot_order)].copy()
other_df = other_df.copy().groupby("Group").sum().reset_index()
other_df["bd_opp_perc_err"] = (other_df["bd_opp_total_err_2021"]+other_df["bd_opp_total_err_2010"]) / (other_df["bd_opp_total_2010"]+other_df["bd_opp_total_2021"])
other_df["Item"] = other_df["Group"].apply(lambda x: f"Others_{x}")

non_other_df = non_other_df[["Item", "bd_opp_total_2010", "bd_opp_change", "bd_opp_perc_err"]]
other_df = other_df[["Item", "bd_opp_total_2010", "bd_opp_change", "bd_opp_perc_err"]]
df = pd.concat([non_other_df, other_df], ignore_index=True)
df = df[df["Item"].isin(plot_order)]
df = df.sort_values("Item", key=lambda x: x.map({item: i for i, item in enumerate(plot_order)}))

color_map = {item: color for item, color in zip(plot_order, color_order)}
df["Color"] = df["Item"].map(color_map)

df["bd_opp_relative_change"] = df["bd_opp_change"] / df["bd_opp_total_2010"]
df["bd_opp_relative_err"] = (df["bd_opp_perc_err"]) * np.abs(df["bd_opp_relative_change"])

left = 0
pad = 0.008
width = 1/(len(df)) - pad + pad/len(df)
for _, row in df.iterrows():
    # width = row["bd_opp_total_2010"]/df["bd_opp_total_2010"].sum()
    rect = mpatches.Rectangle((left, 0), width, row["bd_opp_relative_change"], color=row["Color"])
    ax.add_patch(rect)

    ax.errorbar(left + width/2, row["bd_opp_relative_change"], yerr=row["bd_opp_relative_err"], color="black", capsize=2, fmt="none", linewidth=0.8)

    left += width+pad

tags = []
for _, row in df.iterrows():
    if row["Item"].startswith("Others_"):
        label = row["Item"].replace("Others_", "Other ")
        if "pig meat" in label:
            label = "Other meats"
        if "Plantains" in label:
            label = "Plantains"
        if "carbohydrates" in label:
            label = "Other Grains, roots, carbs"
    else:
        label = label_formatting(row["Item"])
    tags.append(label)
ax.set_xticks(np.linspace(width/2, 1-width/2, len(df)), tags, rotation=-75, fontsize=6, ha="left", va="top")


ax.hlines(0, xmin=0, xmax=1, color="black", linewidth=0.8)
# ax.set_ylim(-0.7,0.7)
ax.set_xlim(0,1)
ticks = ax.get_yticks()
ax.set_yticks(ticks, [f"{int(tick*100)}%" for tick in ticks])
ax.set_ylim(-1.5)
# ax.set_yticks([0.6, 0.4, 0.2, 0, -0.2, -0.4, -0.6], ["+60%", "+40%", "+20%", "0%", "-20%", "-40%", "-60%"])
ax.set_ylabel("Global Biodiversity footprint change")
ax.set_title("Biodiversity footprint change from 2010 to 2021")


# plot 4
ax = axs[1,1]
df = df_2010.copy()
df = df.merge(df_2021[["Item", "Cons", "Cons_err", "bd_opp_total",  "bd_opp_total_err"]], on="Item", suffixes=("_2010", "_2021"))
df["Cons_2010"] *= 1000
df["Cons_err_2010"] *= 1000
df["Cons_2021"] *= 1000
df["Cons_err_2021"] *= 1000
non_other_df = df[df["Item"].isin(plot_order)].copy()
other_df = df[~df["Item"].isin(plot_order)].copy()
other_df = other_df.copy().groupby("Group").sum().reset_index()
other_df["Item"] = other_df["Group"].apply(lambda x: f"Others_{x}")
df = pd.concat([non_other_df, other_df], ignore_index=True)
df = df[df["Item"]!="Sugar beet"]
color_map = {item: color for item, color in zip(plot_order, color_order)}

df["Color"] = df["Item"].map(color_map)

beef_cons_2010 = df[df["Item"]=="Meat of cattle with the bone; fresh or chilled"]["Cons_2010"].values[0] * 6948574560 # TODO replace with country pop
for _, row in df.iterrows():
    x = row["Cons_2010"]
    y = row["bd_opp_total_2010"]/row["Cons_2010"]
    x2 = row["Cons_2021"]
    y2 = row["bd_opp_total_2021"]/row["Cons_2021"]
    dx = x2 - x
    dy = y2 - y

    if type(row["Color"]) != float:
        ax.plot([x,x2],[y,y2], color=row["Color"])
        
        angle = math.atan2(np.log10(y)-np.log10(y2), np.log10(x)-np.log10(x2))*(180/np.pi)+90+120


        ax.plot(x2, y2, color=row["Color"], marker=(3,1,angle))
    # ax.annotate("", xytext=(x, y), xy=(x2, y2),
    #         arrowprops=dict(arrowstyle="->"))
ax.set_yscale("log")
ax.set_xscale("log")
# ax.set_xlim(df["Cons_2010"].min()*0.8, df["Cons_2021"].max()*1.4)
# ax.set_ylim((df["bd_opp_total_2010"]/df["Cons_2010"]).min()*0.8, (df["bd_opp_total_2021"]/df["Cons_2021"]).max()*1.2)


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

ax3.set_xlim(x1*y2, x2*y2)
ax3.set_xlabel("Annual Extinctions per kg", color=total_grid_color)
ax3.tick_params(axis='x', colors=total_grid_color)
    
print(x1, x2, y1, y2)
ax.set_xlim(x1, x2)
ax.set_ylim(y1, y2)
ax.set_ylabel("Impact per kg")
ax.set_xlabel("Annual consumption per capita, kg")
ax.set_title(f"Change in {ISO} commodity consumption and impact\nbetween 2010 and 2021")

fig.suptitle(ISO, fontsize=14)
plt.savefig(f'../outputs/mosaics/{ISO}_group_mosaics.png', dpi=1200)