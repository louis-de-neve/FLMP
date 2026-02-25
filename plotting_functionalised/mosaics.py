import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as transforms
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from pandas import DataFrame
from matplotlib.axes import Axes


class Commodity:
    def __init__(self, name:str, m:int, color:str|tuple="#777777", line_object:Line2D|None=None)->None:
        self.name = name
        self.m = m
        self.color = color
        self.line_object = line_object
        self.yvals = [0.,0.]
        self.raw_vals = [0.,0.]
        self.errors = [0.,0.]
        self.cons = [0.,0.]
        self.area = [0.,0.]

    def set_yval(self, i:int, value:float|int)->None:
        self.yvals[i] = value

    def set_raw_vals(self, i:int, value:float|int)->None:
        self.raw_vals[i] = value

    def set_errors(self, i:int, value:float|int)->None:
        self.errors[i] = value
    
    def set_cons(self, i:int, value:float|int)->None:
        self.cons[i] = value
    
    def set_area(self, i:int, value:float|int)->None:
        self.area[i] = value

class Group:
    def __init__(self, name:str, n:int, color:str|tuple, color2:str|tuple)->None:
        self.name = name
        self.color = color
        self.color2 = color2
        self.n = n
        self.commodities = []
        self.xvals = [0.,0.]
        self.data:list[DataFrame] = []

    def add_item(self, item:Commodity)->None:
        self.commodities.append(item)

    def set_xval(self, i:int, value:float|int)->None:
        self.xvals[i] = value

    def set_data(self, i:int, df:DataFrame)->None:
        if len(self.data) > i:
            self.data[i] = df
        else:
            self.data.append(df)

    def dataframe(self, i:int)->DataFrame:
        return self.data[i] if len(self.data) > i else pd.DataFrame()


# reference data & functions
COLORS = pd.DataFrame({'Grains, roots, starchy carbohydrates' : "#E69F00",
                'Legumes, beans, nuts' : "#F0E442",
                'Fruit and vegetables' : "#009E73",
                'Stimulants and spices' : "#F7322B",
                'Ruminant meat' : "#D55E00", 
                'Dairy and eggs' : "#0072B2",
                'Poultry and pig meat' : "#CC79A7", 
                'Sugar crops' : "#93F840"
                }.items(), columns=["Group", "Color"])

COLORS2 = pd.DataFrame({'Grains, roots, starchy carbohydrates' : "#ffd066",
                'Legumes, beans, nuts' : "#f7f1a1",
                'Fruit and vegetables' : "#00ffba",
                'Stimulants and spices' : "#fb9b98",
                'Ruminant meat' : "#ffaa66", 
                'Dairy and eggs' : "#33b6ff",
                'Poultry and pig meat' : "#e3b5ce", 
                'Sugar crops' : "#c7fb9d"
                }.items(), columns=["Group", "Color2"])

ORDER = pd.DataFrame({'Grains, roots, starchy carbohydrates' : 3,
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
    if "Maize" in label:
        label = "Maize"
    if "Oil palm" in label:
        label = "Palm oil"
    return label


def modify_axes(ax1, ax2, df_2010, df_2021):
    # Axes manipulation for scale
    total_2010 = df_2010["bd_opp_total"].sum()
    total_2021 = df_2021["bd_opp_total"].sum()

    if total_2010 > total_2021:
        axis_to_change = ax2
    else:
        axis_to_change = ax1
    larger_total = max(total_2010, total_2021)
    smaller_total = min(total_2010, total_2021)
    print(larger_total, smaller_total)
    new_length_ratio = np.sqrt(smaller_total / larger_total)
    delta = (1 - new_length_ratio)/2

    current_pos = axis_to_change.get_position()
    current_dim = (current_pos.x1 - current_pos.x0, current_pos.y1 - current_pos.y0)
    delta_dim = (current_dim[0]*delta, current_dim[1]*delta)
    new_pos = transforms.Bbox([[current_pos.x0 + delta_dim[0], current_pos.y0 + 2*delta_dim[1]], [current_pos.x1 - delta_dim[0], current_pos.y1]])
    axis_to_change.set_position(new_pos)
    i_larger = 0 if total_2010 > total_2021 else 1
    axes = [ax1, ax2]
    for i in range(2):
        axes[i].set_xlim(0,1)
        axes[i].set_ylim(0,1)
        axes[i].set_xticks([])
        axes[i].set_yticks([])
        axes[i].axis('off')
    return i_larger, new_length_ratio


def define_groups_and_colors(data:DataFrame, order:DataFrame, colors:DataFrame, colors2:DataFrame)->list[Group]:
    groups = []
    df_grouped = data[["Group"]].copy()
    df_grouped = df_grouped.groupby("Group").sum().reset_index()
    df_grouped = df_grouped.merge(colors, on="Group", how="left")
    df_grouped = df_grouped.merge(colors2, on="Group", how="left")
    df_grouped = df_grouped.merge(order, on="Group", how="left")
    df_grouped = df_grouped.sort_values("Order").set_index("Order")

    n=-1
    for _, row in df_grouped.iterrows():
        n+=1
        group = Group(name=row["Group"], n=n, color=row["Color"], color2=row["Color2"])
        groups.append(group)
    return groups
        
def assign_group_data(groups:list[Group], data:DataFrame, i:int)->None:
    total_bd_opp = data["bd_opp_total"].sum()
    for group in groups:
        group_data = data[data["Group"] == group.name]
        group_bd_opp = group_data["bd_opp_total"].sum()
        group.set_xval(i, group_bd_opp / total_bd_opp)
        group.set_data(i, group_data)

def define_commodities_and_colors(ax:Axes, group:Group, classify_as_other_limit:float)->None:
    group_df = group.dataframe(0).copy()
    group_df = group_df.sort_values("bd_opp_total", ascending=False).reset_index(drop=True)
    group_df["group_bd_opp_perc"] = group_df["bd_opp_total"] / group_df["bd_opp_total"].sum()
    other_categories = group_df[(group_df["Item"].str.contains("other", case=False))|(group_df["group_bd_opp_perc"]<classify_as_other_limit)]["Item"].tolist()
    other_categories = [] if len(other_categories) == 1 else other_categories
    

    final_df = group.dataframe(1).copy()
    final_df["group_bd_opp_perc"] = final_df["bd_opp_total"] / final_df["bd_opp_total"].sum()


    intial_non_other_df = group_df[~group_df["Item"].isin(other_categories)]
    length = len(intial_non_other_df) + (1 if len(other_categories) > 0 else 0)
    cmap = LinearSegmentedColormap.from_list("custom_cmap", [group.color, group.color2], N=length)
    non_other_cats = intial_non_other_df["Item"].unique().tolist()

    m=-1
    for _, item_row in intial_non_other_df.iterrows():
        m+=1
        item_name = item_row["Item"]
        color = cmap(m)
        y0 = item_row["group_bd_opp_perc"]
        y1 = final_df[final_df["Item"] == item_name]["group_bd_opp_perc"].values[0] if item_name in final_df["Item"].values else 0
        raw0 = item_row["bd_opp_total"]
        raw1 = final_df[final_df["Item"] == item_name]["bd_opp_total"].values[0] if item_name in final_df["Item"].values else 0
        err0 = item_row["bd_opp_total_err"]
        err1 = final_df[final_df["Item"] == item_name]["bd_opp_total_err"].values[0] if item_name in final_df["Item"].values else 0
        cons0 = item_row["Cons"]
        cons1 = final_df[final_df["Item"] == item_name]["Cons"].values[0] if item_name in final_df["Item"].values else 0
        area0 = item_row["Pasture_m2"] + item_row["Arable_m2"]
        area1 = final_df[final_df["Item"] == item_name]["Pasture_m2"].values[0] + final_df[final_df["Item"] == item_name]["Arable_m2"].values[0] if item_name in final_df["Item"].values else 0
        legend_plot = ax.plot([], [], color=cmap(m), lw=5, label="_")[0]

        commodity = Commodity(name=item_name, m=m, color=color)
        commodity.set_yval(0, y0)
        commodity.set_yval(1, y1)
        commodity.set_raw_vals(0, raw0)
        commodity.set_raw_vals(1, raw1)
        commodity.set_errors(0, err0)
        commodity.set_errors(1, err1)
        commodity.set_cons(0, cons0)
        commodity.set_cons(1, cons1)
        commodity.set_area(0, area0)
        commodity.set_area(1, area1)
        commodity.line_object = legend_plot
        group.add_item(commodity)
    m+=1

    def others(df, non_other_cats):
        others_df = df[~df["Item"].isin(non_other_cats)]
        others_sum_perc = others_df["group_bd_opp_perc"].sum()
        others_sum_raw = others_df["bd_opp_total"].sum()
        others_cons = others_df["Cons"].sum()
        others_err= others_df["bd_opp_total_err"].sum()
        return others_sum_perc, others_sum_raw, others_err, others_cons
    legend_plot = ax.plot([], [], color=cmap(m), lw=5, label="_")[0]
    if len(other_categories) > 0:
        commodity = Commodity(name=f"Others_{group.name}", m=m, color=cmap(m))
        initial_others = others(group_df, non_other_cats)
        final_others = others(final_df, non_other_cats)
        commodity.set_yval(0, initial_others[0])
        commodity.set_yval(1, final_others[0])
        commodity.set_raw_vals(0, initial_others[1])
        commodity.set_raw_vals(1, final_others[1])
        commodity.set_errors(0, initial_others[2])
        commodity.set_errors(1, final_others[2])
        commodity.set_cons(0, initial_others[3])
        commodity.set_cons(1, final_others[3])
        commodity.line_object = legend_plot
        group.add_item(commodity)


def plot_mosaic(groups:list[Group], ax, i:int, i_larger:int, ratio:float)->None:
        default_pad = 0.005
        if i == i_larger:
            pad = default_pad* ratio
        else:
            pad = default_pad

        left = 0
        for group in groups:
            up = 0
            text_color = "white" if group.name == "Dairy and eggs" else "black"
            for commodity in group.commodities:
                if commodity.yvals[i] -2*pad > 0:
                    rect = mpatches.Rectangle((left+pad, up+pad), group.xvals[i]-2*pad, commodity.yvals[i]-2*pad, color=commodity.color)
                    ax.add_patch(rect)

                    label = label_formatting(commodity.name)
                    if (group.xvals[i] > 0.1) and (commodity.yvals[i] > 0.05) and (commodity.name != "Raw milk of cattle"):
                        ax.text(left + group.xvals[i]/2, up + commodity.yvals[i]/2, label, ha="center", va="center", fontsize=6, color=text_color)
                    elif (group.xvals[i] > 0.04) and (commodity.yvals[i] > 0.1):
                        ax.text(left + group.xvals[i]/2, up + commodity.yvals[i]/2, label, ha="center", va="center", fontsize=6, rotation=90, color=text_color)

                up += commodity.yvals[i]
            left += group.xvals[i]
    


def mosaic_plotting(ax1, ax2, df_2010, df_2021):

        


    groups = define_groups_and_colors(df_2010, ORDER, COLORS, COLORS2)
    assign_group_data(groups, df_2010, 0)
    assign_group_data(groups, df_2021, 1)

    if type(ax1) == type(None) or type(ax2) == type(None):
        for g in groups:
            define_commodities_and_colors(plt.gca(), g, classify_as_other_limit=0.05)
        return groups
    
    
    for g in groups:
            define_commodities_and_colors(ax2, g, classify_as_other_limit=0.05)
    i_larger, new_length_ratio = modify_axes(ax1, ax2, df_2010, df_2021)
    plot_mosaic(groups, ax1, 0, i_larger, new_length_ratio)
    plot_mosaic(groups, ax2, 1, i_larger, new_length_ratio)

    ax1.set_title("2010", fontsize=14)
    ax2.set_title("2021", fontsize=14)

    return groups

