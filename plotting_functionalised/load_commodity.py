import pandas as pd
import pickle as pkl
import os
def load_commodity(commodity:str="Meat of cattle with the bone; fresh or chilled", use_cache:bool=True):

    if use_cache and os.path.exists(f'../results/2010/feed_{commodity}.pkl'):
        feed_df_2010 = pkl.load(open(f'../results/2010/feed_{commodity}.pkl', 'rb'))
        feed_df_2021 = pkl.load(open(f'../results/2021/feed_{commodity}.pkl', 'rb'))
        pasture_df_2010 = pkl.load(open(f'../results/2010/pasture_{commodity}.pkl', 'rb'))
        pasture_df_2021 = pkl.load(open(f'../results/2021/pasture_{commodity}.pkl', 'rb'))
        return feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021

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
        feed_2010 = cdf_2010[(cdf_2010["ItemT_Name"]==commodity)&(cdf_2010["FAO_land_calc_m2"]!=0)].copy()
        feed_2021 = cdf_2021[(cdf_2021["ItemT_Name"]==commodity)&(cdf_2021["FAO_land_calc_m2"]!=0)].copy()
        past_2010 = cdf_2010[(cdf_2010["ItemT_Name"]==commodity)&(cdf_2010["FAO_land_calc_m2"]==0)].copy()
        past_2021 = cdf_2021[(cdf_2021["ItemT_Name"]==commodity)&(cdf_2021["FAO_land_calc_m2"]==0)].copy()

        feed_df_2010 = pd.concat([feed_df_2010, feed_2010], ignore_index=True)
        feed_df_2021 = pd.concat([feed_df_2021, feed_2021], ignore_index=True)
        pasture_df_2010 = pd.concat([pasture_df_2010, past_2010], ignore_index=True)
        pasture_df_2021 = pd.concat([pasture_df_2021, past_2021], ignore_index=True)

    pkl.dump(feed_df_2010, open(f'../results/2010/feed_{commodity}.pkl', 'wb'))
    pkl.dump(feed_df_2021, open(f'../results/2021/feed_{commodity}.pkl', 'wb'))
    pkl.dump(pasture_df_2010, open(f'../results/2010/pasture_{commodity}.pkl', 'wb'))
    pkl.dump(pasture_df_2021, open(f'../results/2021/pasture_{commodity}.pkl', 'wb'))

    return feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021