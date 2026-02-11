import math
import matplotlib.patches as mpatches
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerPatch
import numpy as np
from mosaics import mosaic_plotting, label_formatting, Group, Commodity
from bar_change import bar_plot
from cons_impact_scatter import cons_impact_plot
from load_commodity import load_commodity
from calculate_impacts import calculate_impacts
from country_arrow_scatterplot import country_arrowplot
from vectorplotting import country_vectorplot, commodity_vectorplot, feedpasture_vectorplot


world_population_2010 = 6948574560
world_population_2021 = 7927332080
pops = [world_population_2010, world_population_2021]

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
    ax4 = fig.add_axes((fwidth + xpad+left_margin/2, ypad + shift34, fwidth - 2*xpad, fheight - 2*ypad - offset3/2))

    axs = np.array([[ax1, ax2], [ax3, ax4]])
    return fig, axs

def single_axes_setup():
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_axes((0.15, 0.1, 0.8, 0.8))
    return fig, ax

def three_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(15, 5))

    fwidth = 1/3
    fheight = 1
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03

    offset3 = 0.06
    shift34 = 0.03


    ax1 = fig.add_axes((xpad+left_margin, ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax3 = fig.add_axes((fwidth*2 + xpad+left_margin/2, ypad, fwidth - 2*xpad, fheight - 2*ypad))

    axs = np.array([ax1, ax2, ax3])
    return fig, axs

def get_region_map():
    regions = pd.DataFrame({'Asia' : "#df9903eb",
                'Europe' : "#2b56e2aa",
                'Americas' : "#36ad36c6",
                'Africa' : "#ff0000aa",
                'Oceania': "#f700ffaa",
                }.items(), columns=["region", "Color"])

    region_map = pd.read_csv("../input_data/regions.csv")[["alpha-3", "region"]]
    region_map = region_map.merge(regions, on="region", how="left")
    return regions, region_map

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
    bar_plot(fig, axs[1,0], groups, (-1., 3.), relative=False)
    cons_impact_plot(axs[1,1], groups)
    plt.suptitle(c)
    plt.savefig(f'../outputs/mosaics/{c}.png', dpi=600)

def world_setup():

    fig, axs = six_axes_setup()
    # Data import
    df_2010 = pd.read_csv(f'../results/{2010}/world_aggregate_impacts.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/world_aggregate_impacts.csv')

    for col in ["bd_opp_total", "Cons", "bd_opp_total_err", "Pasture_m2", "Arable_m2"]:
        df_2010[col] = df_2010[col] / world_population_2010
        df_2021[col] = df_2021[col] / world_population_2021

    groups = mosaic_plotting(axs[0,0], axs[0,1], df_2010, df_2021)
    bar_plot(fig, axs[1,0], groups, (-0.7, 0.92))
    cons_impact_plot(axs[1,1], groups)

    feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021 = load_commodity("Meat of cattle with the bone; fresh or chilled")
    beef_cons_2010 = pasture_df_2010["provenance"].sum()*1000
    country_df_2010, country_df_2021 = calculate_impacts(feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021)
    regions, region_map = get_region_map()

    country_arrowplot(axs[2,0], country_df_2010, country_df_2021, region_map, regions, beef_cons_2010)
    # country_vectorplot(axs[2,1], country_df_2010, country_df_2021, region_map)
    commodity_vectorplot(axs[2,1], groups, pops)
    plt.savefig('../outputs/Global_group_mosaics_vectors.png', dpi=600)

def single_plot_setup():
    fig, ax = single_axes_setup()
    
    df_2010 = pd.read_csv(f'../results/{2010}/world_aggregate_impacts.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/world_aggregate_impacts.csv')

    for col in ["bd_opp_total", "Cons", "bd_opp_total_err", "Pasture_m2", "Arable_m2"]:
        df_2010[col] = df_2010[col] / world_population_2010
        df_2021[col] = df_2021[col] / world_population_2021

    groups = mosaic_plotting(None, None, df_2010, df_2021)
    commodity_vectorplot(ax, groups, pops)

    

    plt.savefig('../outputs/commodity_vector_plot.png', dpi=600)
   
def feed_pasture_vector_setup():
    fig, axs = three_axes_setup()
    feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021 = load_commodity("Meat of cattle with the bone; fresh or chilled")
    beef_cons_2010 = pasture_df_2010["provenance"].sum()*1000
    country_df_2010, country_df_2021 = calculate_impacts(feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021)
    regions, region_map = get_region_map()

    feedpasture_vectorplot(axs[0], axs[1], country_df_2010, country_df_2021, region_map)
    country_vectorplot(axs[2], country_df_2010, country_df_2021, region_map)
    axs[0].set_title("Pasture impact changes")
    axs[1].set_title("Feed impact changes")
    axs[2].set_title("Total impact changes")
    plt.savefig('../outputs/feed_pasture_vectors.png', dpi=600)

country_setup()