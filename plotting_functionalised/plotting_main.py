import math
import matplotlib.patches as mpatches
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerPatch
import numpy as np
from mosaics import mosaic_plotting, label_formatting, Group, Commodity
from bar_change import bar_plot
from bar_change_io import bar_plot_io
from cons_impact_scatter import cons_impact_plot
from load_commodity import load_commodity, load_commodity_total
from calculate_impacts import calculate_impacts
from country_arrow_scatterplot import country_arrowplot
from vectorplotting import country_vectorplot, commodity_vectorplot, feedpasture_vectorplot
from figure_setups import get_axes
from Ellipse_plot import ellipse_plot

world_population_2010 = 6948574560
world_population_2021 = 7927332080
pops = [world_population_2010, world_population_2021]


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


def filter_top_commodities(groups, top_n=10):
    c_impacts = []
    for g in groups:
        for c in g.commodities:
            c_impacts.append(c.raw_vals[1])
    c_impacts = sorted(c_impacts, reverse=True)
    threshold = c_impacts[top_n-1]
    for g in groups:
        g.commodities = [c for c in g.commodities if c.raw_vals[1] >= threshold]
    return groups

def country_setup():
    c="CHN"
    fig, axs = get_axes(4)
    # Data import
    df_2010 = pd.read_csv(f'../results/{2010}/{c}/impacts_aggregated.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/impacts_aggregated.csv')
    for col in ["bd_opp_total", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 30995
        df_2021[col] = df_2021[col] / 30995

    groups = mosaic_plotting(axs[0,0], axs[0,1], df_2010, df_2021)
    groups = filter_top_commodities(groups, 10)
    bar_plot(fig, axs[1,0], groups, (-0.4, 1.2), relative=True)
    axs[1,0].set_title("Change in impact of top 10 commodities")

    df_2010 = pd.read_csv(f'../results/{2010}/{c}/impacts_aggregated.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/impacts_aggregated.csv')
    for col in ["bd_opp_total", "Cons", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 1.43e9
        df_2021[col] = df_2021[col] / 1.35e9
    for col in ["bd_opp_total", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 30995
        df_2021[col] = df_2021[col] / 30995
    groups = mosaic_plotting(None, None, df_2010, df_2021)
    groups = filter_top_commodities(groups, 10)

    com_names = []
    for g in groups:
        for c2 in g.commodities:
            com_names.append(c2.name)

    cons_impact_plot(axs[1,1], groups)
    # plt.suptitle(c)
    plt.savefig(f'../outputs/mosaics/{c}.png', dpi=600)
    print("here")
    return com_names

def world_setup():

    fig, axs = get_axes(6)
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
    country_vectorplot(axs[2,1], country_df_2010, country_df_2021, region_map)
    # commodity_vectorplot(axs[2,1], groups, pops)
    plt.savefig('../outputs/Global_group_mosaics_vectors.png', dpi=600)

def single_plot_setup():
    fig, axs = get_axes(2)
    
    # CONSUMPTION BY COUNTRY
    regions, region_map = get_region_map()
    df_2010, df_2021 = load_commodity_total(True)
    df_2010["m2_per_kg"] = df_2010["Area"]/df_2010["Cons"]
    df_2021["m2_per_kg"] = df_2021["Area"]/df_2021["Cons"]
    df_2010["E_per_m2"] = df_2010["bd_opp_total"] / (df_2010["Area"])
    df_2021["E_per_m2"] = df_2021["bd_opp_total"] / (df_2021["Area"])
    country_arrowplot(axs[0], df_2010, df_2021, region_map, regions, df_2010["Cons"].sum()*1000, (1e-7, 1), (1e-11, 1e-7), xvar="Cons_share", yvar="E_per_kg")
    country_arrowplot(axs[1], df_2010, df_2021, region_map, regions, df_2010["Cons"].sum()*1000, (1e-12, 1e-8), (1e3, 1e6), xvar="E_per_m2", yvar="m2_per_kg")
    axs[0].set_xlabel("Share of global consumption")
    axs[0].set_title("Change in consumption impact between 2010 and 2021")
    axs[1].set_xlabel("Biodiversity Opportunity Cost, Extinctions per kg")
    axs[1].set_ylabel("Land Usage, m2 per kg")
    axs[1].set_title("Change in consumption impact per kg between 2010 and 2021")
    plt.savefig('../outputs/consumption_impacts_by_country.png', dpi=600)
    


    # COMMODITY VECTOR PLOT
    # df_2010 = pd.read_csv(f'../results/{2010}/world_aggregate_impacts.csv')
    # df_2021 = pd.read_csv(f'../results/{2021}/world_aggregate_impacts.csv')
    # for col in ["bd_opp_total", "Cons", "bd_opp_total_err", "Pasture_m2", "Arable_m2"]:
    #     df_2010[col] = df_2010[col] / world_population_2010
    #     df_2021[col] = df_2021[col] / world_population_2021
    # groups = mosaic_plotting(None, None, df_2010, df_2021)
    # commodity_vectorplot(ax, groups, pops)
    # plt.savefig('../outputs/commodity_vector_plot.png', dpi=600)
   
def feed_pasture_vector_setup():
    fig, axs = get_axes(3)
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

def ellipse_setup():
    fig, axs = get_axes(1)
    regions, region_map = get_region_map()
    df_2010, df_2021 = load_commodity_total(True)
    df_2010["m2_per_kg"] = df_2010["Area"]/df_2010["Cons"]
    df_2021["m2_per_kg"] = df_2021["Area"]/df_2021["Cons"]
    df_2010["E_per_m2"] = df_2010["bd_opp_total"] / (df_2010["Area"])
    df_2021["E_per_m2"] = df_2021["bd_opp_total"] / (df_2021["Area"])
    ellipse_plot(axs[0], df_2010, df_2021, region_map, regions, df_2010["Cons"].sum()*1000, (1e-7, 1), (1e-11, 1e-7), xvar="Cons_share", yvar="E_per_kg")
    plt.savefig('../outputs/ellipses.png', dpi=600)

def country_setup_2():
    c="CHN"
    fig, axs = get_axes(1)
    # Data import
    df_2010 = pd.read_csv(f'../results/{2010}/{c}/impacts_aggregated.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/impacts_aggregated.csv')

    groups = mosaic_plotting(None, None, df_2010, df_2021)
    groups = filter_top_commodities(groups, 10)
    

    df_2010 = pd.read_csv(f'../results/{2010}/{c}/df_os.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/df_os.csv')
    df_2010["Item"] = df_2010["Unnamed: 0"]
    df_2021["Item"] = df_2021["Unnamed: 0"]

    groups2 = mosaic_plotting(None, None, df_2010, df_2021)
    bar_plot_io(fig, axs[0], groups, (-0.4, 1.2), relative=True, ytick_spacing=0.2, secondary_groups=groups2)
    

    # cons_impact_plot(axs[1], groups)
    plt.savefig(f'../outputs/mosaics/{c}2.png', dpi=600)

def country_setup_3(c_names):
    c="CHN"
    fig, axs = get_axes(2)
    # Data import
    df_2010 = pd.read_csv(f'../results/{2010}/{c}/df_chn.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/df_chn.csv')
    df_2010["Item"] = df_2010["Unnamed: 0"]
    df_2021["Item"] = df_2021["Unnamed: 0"]

    for col in ["bd_opp_total", "Cons", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 1.43e9
        df_2021[col] = df_2021[col] / 1.35e9
    for col in ["bd_opp_total", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 30995
        df_2021[col] = df_2021[col] / 30995

    groups = mosaic_plotting(None, None, df_2010, df_2021)
    for g in groups:
        g.commodities = [c for c in g.commodities if c.name in c_names]
    cons_impact_plot(axs[0], groups, (1e-2, 1e3))

    df_2010 = pd.read_csv(f'../results/{2010}/{c}/df_os.csv')
    df_2021 = pd.read_csv(f'../results/{2021}/{c}/df_os.csv')
    df_2010["Item"] = df_2010["Unnamed: 0"]
    df_2021["Item"] = df_2021["Unnamed: 0"]

    for col in ["bd_opp_total", "Cons", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 1.43e9
        df_2021[col] = df_2021[col] / 1.35e9
    for col in ["bd_opp_total", "bd_opp_total_err"]:
        df_2010[col] = df_2010[col] / 30995
        df_2021[col] = df_2021[col] / 30995

    groups = mosaic_plotting(None, None, df_2010, df_2021)
    for g in groups:
        g.commodities = [c2 for c2 in g.commodities if c2.name in c_names]
    cons_impact_plot(axs[1], groups, (1e-2, 1e3))
    


    axs[1].legend([], frameon=False)
    axs[0].set_title("Change in Domestic Impact of Top 10 Commodities")
    axs[1].set_title("Change in Imported Impact of Top 10 Commodities")
    # cons_impact_plot(axs[1], groups)
    plt.savefig(f'../outputs/mosaics/{c}3.png', dpi=600)

com_names = country_setup()

country_setup_2()
country_setup_3(com_names)


# df_2010, df_2021,_1,_2 = load_commodity("Sugar cane", True)
# print(df_2010)
# country_df_2010, country_df_2021 = calculate_impacts(_1, _2, df_2010, df_2021)
# print(country_df_2010[["ISO", "E"]][country_df_2010["ISO"]=="BRA"], country_df_2010["E"].sum())
# print(country_df_2021[["ISO", "E"]][country_df_2021["ISO"]=="BRA"], country_df_2021["E"].sum())
# # world_setup()