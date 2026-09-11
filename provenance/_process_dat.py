"""
Created on Mon Jul 25 16:55:34 2022

@author: Thomas Ball
@editor: Louis De Neve - edited to be vectorised and integrated into MRIO pipeline Nov 2025
"""

import pandas as pd
import numpy as np
import os
import warnings
import time
from pathlib import Path

def main(year, coi_iso, bh, bf, results_dir=Path("./results"), amortization_years=30):

    datPath = "./input_data"
    scenPath = results_dir / str(year) / coi_iso

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        country_code_data = pd.read_excel(f"{datPath}/nocsDataExport_20251021-164754.xlsx")
    coi = country_code_data.loc[country_code_data["ISO3"]==coi_iso]["FAOSTAT"].values[0]

    grouping = "group_name_v7"
    
    # coi = 229

    commodity_crosswalk = pd.read_csv(f"{datPath}/commodity_crosswalk.csv")
    
    # bh = pd.read_csv(f"{scenPath}/human_consumed_impacts_wErr.csv", index_col = 0)
    # bf = pd.read_csv(f"{scenPath}/feed_impacts_wErr.csv", index_col = 0)
    # print(bf)
    bh = bh.copy()
    bf = bf.copy()
    bf["life_extinctions_per_sp_calc"] = bf["life_extinctions_per_sp_calc"].mask(bf["life_extinctions_per_sp_calc"].lt(0),0)
    bf["ghg_coc_kgco2e_calc"] = bf["ghg_coc_kgco2e_calc"].mask(bf["ghg_coc_kgco2e_calc"].lt(0),0)

    bh = bh[np.logical_not(np.isinf(bh.arable_area_m2_calc))]
    bh["ItemT_Name"] = bh["Item"]
    bh["ItemT_Code"] = bh["Item_Code"]
    bh["pasture_area_m2_calc"] = bh.pasture_area_m2_calc.fillna(0)
    bh["life_extinctions_relerr_frac"] = bh["life_extinctions_per_sp_calc_err"] / bh["life_extinctions_per_sp_calc"]

    bf = bf[np.logical_not(np.isinf(bf.arable_area_m2_calc))]
    bf["ItemT_Code"] = bf["Animal_Product_Code"]
    bf["ItemT_Name"] = bf["Animal_Product"]
    bf["pasture_area_m2_calc"] = 0
    bf["life_extinctions_relerr_frac"] = bf["life_extinctions_per_sp_calc_err"] / bf["life_extinctions_per_sp_calc"]
    bf = bf[~np.isinf(bf.life_extinctions_relerr_frac)]
    xdf = pd.concat([bh,bf])


    lookup = xdf[["ItemT_Code", "ItemT_Name"]].drop_duplicates()


    xdfs_uk = xdf[xdf.Producer_Country_Code == coi]
    xdfs_os = xdf[~(xdf.Producer_Country_Code == coi)]
    xdfs_uk = xdfs_uk[["pasture_area_m2_calc", "arable_area_m2_calc", "ItemT_Name", "ItemT_Code", "provenance_tonnes"]]
    xdfs_os = xdfs_os[["pasture_area_m2_calc", "arable_area_m2_calc", "ItemT_Name", "ItemT_Code", "provenance_tonnes"]]
    
    
    xdfs_uk = xdfs_uk.groupby("ItemT_Name").sum()
    xdfs_os = xdfs_os.groupby("ItemT_Name").sum()


    df_uk = pd.DataFrame()
    missing_items = []
    for item in xdfs_uk.index.tolist():
        x = xdfs_uk.loc[item]
        try:
            item_code = lookup[lookup.ItemT_Name == item].ItemT_Code.values[0]
            df_uk.loc[item, "Group"] = commodity_crosswalk[commodity_crosswalk.Item_Code == item_code][grouping].values[0]
            df_uk.loc[item, "throughput_tonnes"] = x.provenance_tonnes
            df_uk.loc[item, "pasture_area_m2_calc"] = x.pasture_area_m2_calc
            df_uk.loc[item, "arable_area_m2_calc"] = x.arable_area_m2_calc
            df_uk.loc[item, "ghg_prod_food_kgco2e_calc"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].ghg_prod_kgco2e_calc.sum()
            df_uk.loc[item, "ghg_prod_feed_kgco2e_calc"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)].ghg_prod_kgco2e_calc.sum()
            df_uk.loc[item, "ghg_prod_total_kgco2e_calc"] =  df_uk.loc[item, "ghg_prod_feed_kgco2e_calc"] + df_uk.loc[item, "ghg_prod_food_kgco2e_calc"]
            df_uk.loc[item, "life_extinctions_per_sp_food_calc"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)]["life_extinctions_per_sp_calc"].sum()
            df_uk.loc[item, "life_extinctions_per_sp_feed_calc"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)]["life_extinctions_per_sp_calc"].sum()
            df_uk.loc[item, "life_extinctions_per_sp_total_calc"] = df_uk.loc[item, "life_extinctions_per_sp_feed_calc"] + df_uk.loc[item, "life_extinctions_per_sp_food_calc"]
            df_uk.loc[item, "ghg_coc_food_kgco2e_calc"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)]["ghg_coc_kgco2e_calc"].sum()
            df_uk.loc[item, "ghg_coc_feed_kgco2e_calc"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)]["ghg_coc_kgco2e_calc"].sum()
            df_uk.loc[item, "ghg_coc_total_kgco2e_calc"] = df_uk.loc[item, "ghg_coc_feed_kgco2e_calc"] + df_uk.loc[item, "ghg_coc_food_kgco2e_calc"]

            # bd opp food err
            df_uk.loc[item, "life_extinctions_per_sp_food_calc_err"] = bh[(bh.Item==item)&(bh.Producer_Country_Code==coi)].life_extinctions_per_sp_calc_err.sum()

            df_uk.loc[item, "life_extinctions_per_sp_feed_calc_err"] = bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code==coi)].life_extinctions_per_sp_calc_err.sum()

            # bd opp total error
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fe_err = df_uk.loc[item, "life_extinctions_per_sp_feed_calc_err"]/df_uk.loc[item, "life_extinctions_per_sp_feed_calc"]
                fo_err = df_uk.loc[item, "life_extinctions_per_sp_food_calc_err"]/df_uk.loc[item, "life_extinctions_per_sp_food_calc"]

            df_uk.loc[item, "life_extinctions_per_sp_total_calc_err"] = df_uk.loc[item, "life_extinctions_per_sp_feed_calc_err"] + df_uk.loc[item, "life_extinctions_per_sp_food_calc_err"]

            # coc opp food/feed/total err
            df_uk.loc[item, "ghg_coc_food_kgco2e_calc_err"] = bh[(bh.Item==item)&(bh.Producer_Country_Code==coi)].ghg_coc_kgco2e_calc_err.sum()
            df_uk.loc[item, "ghg_coc_feed_kgco2e_calc_err"] = bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code==coi)].ghg_coc_kgco2e_calc_err.sum()
            df_uk.loc[item, "ghg_coc_total_kgco2e_calc_err"] = df_uk.loc[item, "ghg_coc_feed_kgco2e_calc_err"] + df_uk.loc[item, "ghg_coc_food_kgco2e_calc_err"]

            df_uk.loc[item, "consumed_tonnes"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].provenance_tonnes.sum()
            df_uk.loc[item, "consumed_tonnes_err"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].provenance_tonnes_err.sum()

        except IndexError:
            item_code = lookup[lookup.ItemT_Name == item].ItemT_Code.values[0]
            missing_items.append((item, item_code))

    df_os = pd.DataFrame()
    for item in xdfs_os.index.tolist():
        x = xdfs_os.loc[item]
        try:
            item_code = lookup[lookup.ItemT_Name == item].ItemT_Code.values[0]
            df_os.loc[item, "Group"] = commodity_crosswalk[commodity_crosswalk.Item_Code == item_code][grouping].values[0]
            df_os.loc[item, "throughput_tonnes"] = x.provenance_tonnes
            df_os.loc[item, "pasture_area_m2_calc"] = x.pasture_area_m2_calc
            df_os.loc[item, "arable_area_m2_calc"] = x.arable_area_m2_calc
            df_os.loc[item, "ghg_prod_food_kgco2e_calc"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)].ghg_prod_kgco2e_calc.sum()
            df_os.loc[item, "ghg_prod_feed_kgco2e_calc"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)].ghg_prod_kgco2e_calc.sum()
            df_os.loc[item, "ghg_prod_total_kgco2e_calc"] =  df_os.loc[item, "ghg_prod_feed_kgco2e_calc"] + df_os.loc[item, "ghg_prod_food_kgco2e_calc"]
            df_os.loc[item, "life_extinctions_per_sp_food_calc"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)]["life_extinctions_per_sp_calc"].sum()
            df_os.loc[item, "life_extinctions_per_sp_feed_calc"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)]["life_extinctions_per_sp_calc"].sum()
            df_os.loc[item, "life_extinctions_per_sp_total_calc"] = df_os.loc[item, "life_extinctions_per_sp_feed_calc"] + df_os.loc[item, "life_extinctions_per_sp_food_calc"]
            df_os.loc[item, "ghg_coc_food_kgco2e_calc"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)]["ghg_coc_kgco2e_calc"].sum()
            df_os.loc[item, "ghg_coc_feed_kgco2e_calc"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)]["ghg_coc_kgco2e_calc"].sum()
            df_os.loc[item, "ghg_coc_total_kgco2e_calc"] = df_os.loc[item, "ghg_coc_feed_kgco2e_calc"] + df_os.loc[item, "ghg_coc_food_kgco2e_calc"]
            # if item not in df_uk.index:
            df_os.loc[item, "consumed_tonnes"] = bh[(bh.Item == item)&(bh.Producer_Country_Code !=coi)].provenance_tonnes.sum()
            df_os.loc[item, "consumed_tonnes_err"] = np.sqrt(np.nansum(bh[(bh.Item == item)&(bh.Producer_Country_Code !=coi)].provenance_tonnes_err ** 2))

            # bd opp food err
            df_os.loc[item, "life_extinctions_per_sp_food_calc_err"] = bh[(bh.Item==item)&(bh.Producer_Country_Code!=coi)].life_extinctions_per_sp_calc_err.sum()

            # bd opp feed err
            df_os.loc[item, "life_extinctions_per_sp_feed_calc_err"] = bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code!=coi)].life_extinctions_per_sp_calc_err.sum()
            # bd opp total error
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fe_err = df_os.loc[item, "life_extinctions_per_sp_feed_calc_err"]/df_os.loc[item, "life_extinctions_per_sp_feed_calc"]
                fo_err = df_os.loc[item, "life_extinctions_per_sp_food_calc_err"]/df_os.loc[item, "life_extinctions_per_sp_food_calc"]

            df_os.loc[item, "life_extinctions_per_sp_total_calc_err"] = df_os.loc[item, "life_extinctions_per_sp_feed_calc_err"] + df_os.loc[item, "life_extinctions_per_sp_food_calc_err"]

            # coc opp food/feed/total err
            df_os.loc[item, "ghg_coc_food_kgco2e_calc_err"] = bh[(bh.Item==item)&(bh.Producer_Country_Code!=coi)].ghg_coc_kgco2e_calc_err.sum()
            df_os.loc[item, "ghg_coc_feed_kgco2e_calc_err"] = bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code!=coi)].ghg_coc_kgco2e_calc_err.sum()
            df_os.loc[item, "ghg_coc_total_kgco2e_calc_err"] = df_os.loc[item, "ghg_coc_feed_kgco2e_calc_err"] + df_os.loc[item, "ghg_coc_food_kgco2e_calc_err"]

        except IndexError:
            item_code = lookup[lookup.ItemT_Name == item].ItemT_Code.values[0]
            missing_items.append((item, item_code))
            



    kdf = pd.concat([df_uk,df_os])
    # print(kdf.index.tolist())
    # print(kdf.loc["Oil palm fruit"])

    kdf = kdf.groupby([kdf.index, "Group"]).sum().reset_index()

    # print(df_uk, df_os)


    df_uk.to_csv(f"{scenPath}/df_{coi_iso.lower()}.csv")
    df_os.to_csv(f"{scenPath}/df_os.csv")
    xdf.to_csv(f"{scenPath}/impacts_full.csv") # rename to impacts_aggregated
    
    if "Item" not in kdf.columns:
        
        kdf.columns = [_ if _ != "level_0" else "Item" for _ in kdf.columns]
    
    for item in kdf.Item.unique():
        kdf.loc[kdf.Item==item, "primary_tonnes"] = xdf[(xdf.Item==item)&(xdf.ItemT_Name.isin([item, "Primary"]))].provenance_tonnes.sum()
        
    kdf.to_csv(f"{scenPath}/impacts_aggregated.csv")
    agg_impact_path = results_dir / "impacts" / str(year) / f"impacts_aggregated_{coi_iso}.csv"
    os.makedirs(agg_impact_path.parent, exist_ok=True)
    kdf.to_csv(agg_impact_path, index=False)

    food_commodity_impacts = kdf[["Item", "primary_tonnes", "ghg_prod_total_kgco2e_calc", "life_extinctions_per_sp_total_calc", "life_extinctions_per_sp_total_calc_err", "ghg_coc_total_kgco2e_calc", "ghg_coc_total_kgco2e_calc_err"]].copy()
    food_commodity_impacts["ghg_prod_kgco2e_per_kg"] = food_commodity_impacts.ghg_prod_total_kgco2e_calc / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["life_extinctions_per_sp_per_kg"] = food_commodity_impacts.life_extinctions_per_sp_total_calc / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["life_extinctions_per_sp_per_kg_err"] = food_commodity_impacts.life_extinctions_per_sp_total_calc_err / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["ghg_coc_kgco2e_per_kg_per_year"] = (food_commodity_impacts.ghg_coc_total_kgco2e_calc / amortization_years) / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["ghg_coc_kgco2e_per_kg_per_year_err"] = (food_commodity_impacts.ghg_coc_total_kgco2e_calc_err / amortization_years) / (food_commodity_impacts.primary_tonnes * 1000)

    food_commodity_impacts = food_commodity_impacts.drop(columns=["ghg_prod_total_kgco2e_calc", "life_extinctions_per_sp_total_calc", "life_extinctions_per_sp_total_calc_err", "ghg_coc_total_kgco2e_calc", "ghg_coc_total_kgco2e_calc_err"])
    last_row = food_commodity_impacts.iloc[-1].copy()
    last_row.iloc[1:] = 0
    last_row.iloc[0] = "Zero"
    food_commodity_impacts = pd.concat([food_commodity_impacts, last_row.to_frame().T], ignore_index=True)

    old_to_new = pd.read_csv(f"{datPath}/composition_old_vs_new.csv")
    old_to_new = old_to_new.merge(food_commodity_impacts, left_on="New", right_on="Item", how="left")
    old_to_new.drop(columns=["Item", "New"], inplace=True)
    old_to_new.rename(columns={"Old":"Item"}, inplace=True)
    old_to_new.to_csv(f"{scenPath}/food_commodity_impacts.csv", index=False)

    return missing_items


def main_global(year, coi_iso, bh, bf, results_dir=Path("./results"), amortization_years=30):

    datPath = "./input_data"
    scenPath = results_dir / str(year) / coi_iso
    grouping = "group_name_v7"
    
    # coi = 229

    commodity_crosswalk = pd.read_csv(f"{datPath}/commodity_crosswalk.csv")
    
    # bh = pd.read_csv(f"{scenPath}/human_consumed_impacts_wErr.csv", index_col = 0)
    # bf = pd.read_csv(f"{scenPath}/feed_impacts_wErr.csv", index_col = 0)
    # print(bf)
    bh = bh.copy()
    bf = bf.copy()
    bf["life_extinctions_per_sp_calc"] = bf["life_extinctions_per_sp_calc"].mask(bf["life_extinctions_per_sp_calc"].lt(0),0)
    bf["ghg_coc_kgco2e_calc"] = bf["ghg_coc_kgco2e_calc"].mask(bf["ghg_coc_kgco2e_calc"].lt(0),0)

    bh = bh[np.logical_not(np.isinf(bh.arable_area_m2_calc))]
    bh["ItemT_Name"] = bh["Item"]
    bh["ItemT_Code"] = bh["Item_Code"]
    bh["pasture_area_m2_calc"] = bh.pasture_area_m2_calc.fillna(0)
    bh["life_extinctions_relerr_frac"] = bh["life_extinctions_per_sp_calc_err"] / bh["life_extinctions_per_sp_calc"]

    bf = bf[np.logical_not(np.isinf(bf.arable_area_m2_calc))]
    bf["ItemT_Code"] = bf["Animal_Product_Code"]
    bf["ItemT_Name"] = bf["Animal_Product"]
    bf["pasture_area_m2_calc"] = 0
    bf["life_extinctions_relerr_frac"] = bf["life_extinctions_per_sp_calc_err"] / bf["life_extinctions_per_sp_calc"]
    bf = bf[~np.isinf(bf.life_extinctions_relerr_frac)]
    xdf = pd.concat([bh,bf])


    lookup = xdf[["ItemT_Code", "ItemT_Name"]].drop_duplicates()


    xdfs_uk = xdf.copy()
    xdfs_uk = xdfs_uk[["pasture_area_m2_calc", "arable_area_m2_calc", "ItemT_Name", "ItemT_Code", "provenance_tonnes"]]
    
    
    xdfs_uk = xdfs_uk.groupby("ItemT_Name").sum()


    df_uk = pd.DataFrame()
    missing_items = []
    for item in xdfs_uk.index.tolist():
        x = xdfs_uk.loc[item]
        try:
            item_code = lookup[lookup.ItemT_Name == item].ItemT_Code.values[0]
            df_uk.loc[item, "Group"] = commodity_crosswalk[commodity_crosswalk.Item_Code == item_code][grouping].values[0]
            df_uk.loc[item, "throughput_tonnes"] = x.provenance_tonnes
            df_uk.loc[item, "pasture_area_m2_calc"] = x.pasture_area_m2_calc
            df_uk.loc[item, "arable_area_m2_calc"] = x.arable_area_m2_calc
            df_uk.loc[item, "ghg_prod_food_kgco2e_calc"] = bh[(bh.Item == item)].ghg_prod_kgco2e_calc.sum()
            df_uk.loc[item, "ghg_prod_feed_kgco2e_calc"] = bf[(bf.Animal_Product == item)].ghg_prod_kgco2e_calc.sum()
            df_uk.loc[item, "ghg_prod_total_kgco2e_calc"] =  df_uk.loc[item, "ghg_prod_feed_kgco2e_calc"] + df_uk.loc[item, "ghg_prod_food_kgco2e_calc"]
            df_uk.loc[item, "life_extinctions_per_sp_food_calc"] = bh[(bh.Item == item)]["life_extinctions_per_sp_calc"].sum()
            df_uk.loc[item, "life_extinctions_per_sp_feed_calc"] = bf[(bf.Animal_Product == item)]["life_extinctions_per_sp_calc"].sum()
            df_uk.loc[item, "life_extinctions_per_sp_total_calc"] = df_uk.loc[item, "life_extinctions_per_sp_feed_calc"] + df_uk.loc[item, "life_extinctions_per_sp_food_calc"]
            df_uk.loc[item, "ghg_coc_food_kgco2e_calc"] = bh[(bh.Item == item)]["ghg_coc_kgco2e_calc"].sum()
            df_uk.loc[item, "ghg_coc_feed_kgco2e_calc"] = bf[(bf.Animal_Product == item)]["ghg_coc_kgco2e_calc"].sum()
            df_uk.loc[item, "ghg_coc_total_kgco2e_calc"] = df_uk.loc[item, "ghg_coc_feed_kgco2e_calc"] + df_uk.loc[item, "ghg_coc_food_kgco2e_calc"]

            # bd opp food err
            df_uk.loc[item, "life_extinctions_per_sp_food_calc_err"] = bh[(bh.Item==item)].life_extinctions_per_sp_calc_err.sum()

            df_uk.loc[item, "life_extinctions_per_sp_feed_calc_err"] = bf[(bf.Animal_Product==item)].life_extinctions_per_sp_calc_err.sum()

            # bd opp total error
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fe_err = df_uk.loc[item, "life_extinctions_per_sp_feed_calc_err"]/df_uk.loc[item, "life_extinctions_per_sp_feed_calc"]
                fo_err = df_uk.loc[item, "life_extinctions_per_sp_food_calc_err"]/df_uk.loc[item, "life_extinctions_per_sp_food_calc"]

            df_uk.loc[item, "life_extinctions_per_sp_total_calc_err"] = df_uk.loc[item, "life_extinctions_per_sp_feed_calc_err"] + df_uk.loc[item, "life_extinctions_per_sp_food_calc_err"]

            # coc opp food/feed/total err
            df_uk.loc[item, "ghg_coc_food_kgco2e_calc_err"] = bh[(bh.Item==item)].ghg_coc_kgco2e_calc_err.sum()
            df_uk.loc[item, "ghg_coc_feed_kgco2e_calc_err"] = bf[(bf.Animal_Product==item)].ghg_coc_kgco2e_calc_err.sum()
            df_uk.loc[item, "ghg_coc_total_kgco2e_calc_err"] = df_uk.loc[item, "ghg_coc_feed_kgco2e_calc_err"] + df_uk.loc[item, "ghg_coc_food_kgco2e_calc_err"]

            df_uk.loc[item, "consumed_tonnes"] = bh[(bh.Item == item)].provenance_tonnes.sum()
            df_uk.loc[item, "consumed_tonnes_err"] = bh[(bh.Item == item)].provenance_tonnes_err.sum()

        except IndexError:
            item_code = lookup[lookup.ItemT_Name == item].ItemT_Code.values[0]
            missing_items.append((item, item_code))
    
   

    kdf = df_uk.copy()
    # print(kdf.index.tolist())
    # print(kdf.loc["Oil palm fruit"])

    kdf = kdf.groupby([kdf.index, "Group"]).sum().reset_index()

    # print(df_uk, df_os)


    df_uk.to_csv(f"{scenPath}/df_{coi_iso.lower()}.csv")
    xdf.to_csv(f"{scenPath}/impacts_full.csv") # rename to impacts_aggregated
    
    if "Item" not in kdf.columns:
        
        kdf.columns = [_ if _ != "level_0" else "Item" for _ in kdf.columns]
    
    for item in kdf.Item.unique():
        kdf.loc[kdf.Item==item, "primary_tonnes"] = xdf[(xdf.Item==item)&(xdf.ItemT_Name.isin([item, "Primary"]))].provenance_tonnes.sum()
        
    kdf.to_csv(f"{scenPath}/impacts_aggregated.csv")
    agg_impact_path = results_dir / "impacts" / str(year) / f"impacts_aggregated_{coi_iso}.csv"
    os.makedirs(agg_impact_path.parent, exist_ok=True)
    kdf.to_csv(agg_impact_path, index=False)

    food_commodity_impacts = kdf[["Item", "primary_tonnes", "ghg_prod_total_kgco2e_calc", "life_extinctions_per_sp_total_calc", "life_extinctions_per_sp_total_calc_err", "ghg_coc_total_kgco2e_calc", "ghg_coc_total_kgco2e_calc_err"]].copy()
    food_commodity_impacts["ghg_prod_kgco2e_per_kg"] = food_commodity_impacts.ghg_prod_total_kgco2e_calc / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["life_extinctions_per_sp_per_kg"] = food_commodity_impacts.life_extinctions_per_sp_total_calc / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["life_extinctions_per_sp_per_kg_err"] = food_commodity_impacts.life_extinctions_per_sp_total_calc_err / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["ghg_coc_kgco2e_per_kg_per_year"] = (food_commodity_impacts.ghg_coc_total_kgco2e_calc / amortization_years) / (food_commodity_impacts.primary_tonnes * 1000)
    food_commodity_impacts["ghg_coc_kgco2e_per_kg_per_year_err"] = (food_commodity_impacts.ghg_coc_total_kgco2e_calc_err / amortization_years) / (food_commodity_impacts.primary_tonnes * 1000)

    food_commodity_impacts = food_commodity_impacts.drop(columns=["ghg_prod_total_kgco2e_calc", "life_extinctions_per_sp_total_calc", "life_extinctions_per_sp_total_calc_err", "ghg_coc_total_kgco2e_calc", "ghg_coc_total_kgco2e_calc_err"])
    last_row = food_commodity_impacts.iloc[-1].copy()
    last_row.iloc[1:] = 0
    last_row.iloc[0] = "Zero"
    food_commodity_impacts = pd.concat([food_commodity_impacts, last_row.to_frame().T], ignore_index=True)

    old_to_new = pd.read_csv(f"{datPath}/composition_old_vs_new.csv")
    old_to_new = old_to_new.merge(food_commodity_impacts, left_on="New", right_on="Item", how="left")
    old_to_new.drop(columns=["Item", "New"], inplace=True)
    old_to_new.rename(columns={"Old":"Item"}, inplace=True)
    old_to_new.to_csv(f"{scenPath}/food_commodity_impacts.csv", index=False)

    return missing_items


if __name__ == "__main__":
    

    datPath = "dat"
    # scenPath = os.path.join(odPath, "Work\\Work for others\\Catherine CLR\\food_results\\gbr")

