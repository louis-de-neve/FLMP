"""
Created on Wed Mar 15 16:41:04 2023

@author: Thomas Ball
@editor: Louis De Neve - edited to be vectorised and integrated into MRIO pipeline Nov 2025
"""

from pathlib import Path
import pandas as pd
import numpy as np
import os
import sys

from provenance._get_biodiversity_vals import fetch_biodiversity_vals_path

# tonnes C -> kg CO2e: x1000 (t->kg) x 44/12 (molar mass ratio)
KG_CO2E_PER_TONNE_C = 1000.0 * 44.0 / 12.0

def fetch_coc_vals_path(year, datPath, use_2020=True):
    # the coc values are computed on the mapspam crop distributions, so the vintages
    # available here mirror the mapspam years and follow the same use_2020 switch.
    coc_years = [2010, 2020] if use_2020 else [2010]
    coc_yr = min(coc_years, key=lambda y: abs(y - year))  # ties -> 2010
    return os.path.join(datPath, "coc_outputs", f"processed_coc_data_walker_mapspam{coc_yr}.csv"), coc_yr

def get_wwf_pbd(datPath):
    file_name = "Planet-Based Diets - Data and Viewer.xlsx"
    sheet_name = "DATA - Product Level"
    file_path = f"{datPath}/{file_name}"
    if os.path.exists(file_path):
        
        with warnings.catch_warnings(): 
            warnings.simplefilter("ignore")
            df = pd.read_excel(file_path, sheet_name = sheet_name)
        return df
    else:
        sys.exit(f"""Couldn't find {file_name} in {datPath}""")
        return pd.DataFrame()
    
    
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

def get_impacts(wdf, year, coi, filename, results_dir=Path("./results"), use_2020=True,
                 bd_band_name="all", coc_band_name="agri_potential_carbon"):
    # setup
    country_savefile_path = results_dir / str(year) / coi
    datPath = "./input_data"

    
    # trim input data to significant values
    wdf = wdf[np.logical_not(wdf.Item.isna())]
    # wdf = wdf[wdf.Value >= 0.015]

    # name upstream columns at the impacts boundary
    wdf = wdf.rename(columns={"provenance": "provenance_tonnes",
                              "provenance_err": "provenance_tonnes_err"})

    # load additional data and merge into wdf
    commodity_crosswalk = pd.read_csv(f"{datPath}/commodity_crosswalk.csv", index_col = 0)
    wwf = get_wwf_pbd(datPath)
    Sm_wwf_items = pd.read_csv(f"{datPath}/schwarzmueller_wwf.csv",index_col = 0)
    wdf = (wdf
        .merge(Sm_wwf_items[["Item_Code_FAO", "WWF_cat"]], left_on="Item_Code", right_on="Item_Code_FAO", how="left")
        .drop(columns=["Item_Code_FAO"]))

    # load yield data
    fao_prod = pd.read_csv(f"{datPath}/Production_Crops_Livestock_E_All_Data_(Normalized).csv", encoding = "latin-1", low_memory=False)
    fao_prod = fao_prod[fao_prod.Year == year]
    yield_dat = fao_prod[fao_prod["Element Code"] == 5412]
    yield_dat = yield_dat.rename(columns={"Area Code":"Area_Code", "Item Code":"Item_Code"})
    yield_dat = yield_dat[["Area_Code", "Item_Code", "Value"]]
    
    
    # Fall back to global yields
    global_yields = yield_dat[yield_dat["Area_Code"] == 5000].copy()
    global_yields = global_yields.rename(columns={"Value":"Global_Yield"})
    wdf = wdf.merge(global_yields[["Global_Yield", "Item_Code"]], how="left", on="Item_Code")
    yield_dat = yield_dat.rename(columns={"Value":"yield_kg_per_m2"})
    wdf = wdf.merge(yield_dat, how="left", left_on=["Producer_Country_Code", "Item_Code"], right_on=["Area_Code", "Item_Code"])
    wdf = wdf.drop(columns=["Area_Code"])
    wdf.loc[wdf.yield_kg_per_m2.isna(), "yield_kg_per_m2"] = wdf.loc[wdf.yield_kg_per_m2.isna(), "Global_Yield"]
    wdf = wdf.drop(columns=["Global_Yield"])


    # FAOSTAT element 5412 is reported in kg/ha; convert to kg/m2
    wdf["yield_kg_per_m2"] = wdf["yield_kg_per_m2"] / 10000


    # load other impacts and fall back on global values
    # SWWU_avg dropped: it is a per-country AWARE factor, not a per-kg intensity.
    # to restore water, weight WU_avg (litres/kg) by it.
    wwf_arable_land = wwf[["Country_ISO", "Product", "Arable_avg", "GHG_avg", "Pasture_avg"]].copy()
    wwf_global_values = (wwf[wwf["Country_ISO"]=="all-r"][["Product", "Arable_avg", "GHG_avg", "Pasture_avg"]]
        .rename(columns={"Arable_avg":"Global_Arable_avg", "GHG_avg":"Global_GHG_avg", "Pasture_avg":"Global_Pasture_avg"}))
    wdf = (wdf
        .merge(wwf_arable_land, how="left", left_on=["Country_ISO", "WWF_cat"], right_on=["Country_ISO", "Product"])
        .drop(columns=["Product"])
        .merge(wwf_global_values, how="left", left_on=["WWF_cat"], right_on=["Product"])
        .drop(columns=["Product"]))
    wdf.loc[wdf.Pasture_avg.isna(), "Pasture_avg"] = wdf.loc[wdf.Pasture_avg.isna(), "Global_Pasture_avg"]
    wdf.loc[wdf.Arable_avg.isna(), "Arable_avg"] = wdf.loc[wdf.Arable_avg.isna(), "Global_Arable_avg"]
    wdf.loc[wdf.GHG_avg.isna(), "GHG_avg"] = wdf.loc[wdf.GHG_avg.isna(), "Global_GHG_avg"]
    wdf = wdf.drop(columns=["Global_Arable_avg", "Global_GHG_avg", "Global_Pasture_avg"])


    # Pasture calcs (only runs if not feed calc)
    if filename[:4] != "feed":
        rums = [867, 882, 947, 951, 977, 982, 1017, 1020, 1097]
        tb_pasture_vals = pd.read_csv(f"{results_dir}/{year}/.mrio/Pasture_calc.csv")[["Item_Code", "fp_m2_kg", "fp_m2_kg_perc", "Country_ISO"]]
        global_median_tb = {v: tb_pasture_vals[tb_pasture_vals["Item_Code"]==v]["fp_m2_kg"].median() for v in rums}
        global_median_tb_df = pd.DataFrame.from_dict(global_median_tb, orient='index', columns=['global_median_fp_m2_kg'])

        # Pasture_calc.csv keeps its own fp_* names; rename at the boundary
        tb_pasture_vals = tb_pasture_vals.rename(columns={"fp_m2_kg_perc": "pasture_area_relerr_frac"})

        wdf = wdf.merge(tb_pasture_vals, how="left", on=["Country_ISO", "Item_Code"])
        wdf = wdf.merge(global_median_tb_df, how="left", left_on=["Item_Code"], right_index=True)
        # wdf["Pasture_avg"] = wdf[["Pasture_avg","fp_m2_kg", "global_median_fp_m2_kg"]].max(axis=1)
        wdf["Pasture_avg"] = wdf["fp_m2_kg"]
        wdf = wdf.drop(columns=["fp_m2_kg", "global_median_fp_m2_kg"])

    # set non-applicable values to zero
    wdf.loc[wdf.Animal_Product == "Primary", "Arable_avg"] = 0
    wdf.loc[wdf.Animal_Product != "Primary", "Pasture_avg"] = 0


    # land use calculations with arable_avg as redundant fallback
    wdf["WWF_derived_yield"] = 1/(wdf.Arable_avg) # Arable_avg is m2/kg, so its reciprocal is kg/m2
    wdf.loc[wdf.yield_kg_per_m2.isna(), "yield_kg_per_m2"] = wdf.loc[wdf.yield_kg_per_m2.isna(), "WWF_derived_yield"]
    wdf = wdf.drop(columns=["WWF_derived_yield", "Arable_avg"])
    wdf["arable_area_m2_calc"] = (wdf.provenance_tonnes * 1000) / wdf.yield_kg_per_m2


    # calculate impacts (WWF values are per kg, so x kg gives the row total)
    impact_columns = {
        "GHG_avg": "ghg_prod_kgco2e_calc",
        "Pasture_avg": "pasture_area_m2_calc",
    }
    for impact, out_col in impact_columns.items():
        wdf[out_col] = wdf[impact] * (wdf.provenance_tonnes * 1000)
    wdf = wdf.drop(columns=list(impact_columns))


    # error propogation
    if filename[:4] != "feed":
        wdf.pasture_area_relerr_frac = wdf.pasture_area_relerr_frac.fillna(0)
        wdf["relerr"] = (np.sqrt((wdf.provenance_tonnes_err / wdf.provenance_tonnes)**2+(wdf.pasture_area_relerr_frac**2)))
    else:
        wdf["relerr"] = wdf.provenance_tonnes_err / wdf.provenance_tonnes
    for col in ["arable_area_m2_calc", *impact_columns.values()]:
        wdf[f"{col}_err"] = wdf[col] * wdf["relerr"]
    wdf = wdf.drop(columns=["relerr"])

    # biodiversity opportunity cost
    # bd_path = f"{datPath}/LIFE_results_SPAM_2020.csv"
    # bd_opp_cost = bd_opp_cost[bd_opp_cost.band_name=="all"]

    # bd_path = os.path.join(datPath, "mapspam_outputs", "outputs", str(spam_yr), f"processed_results_{spam_yr}.csv")#
    bd_path, spam_yr = fetch_biodiversity_vals_path(year, datPath, use_2020)

    bd_opp_cost = pd.read_csv(bd_path)

    bd_opp_cost = bd_opp_cost[bd_opp_cost.band_name==bd_band_name]
    # sign flip must stay: deltaE_mean is negative for nearly every row and the
    # `> 0` filters below select on it. sp_count not applied, so values are per sp.
    bd_opp_cost.deltaE_mean *= -1
    # bd_opp_cost.deltaE_mean_sem *= bd_opp_cost.sp_count
    

    oc_crop = bd_opp_cost[(bd_opp_cost.deltaE_mean > 0)].copy()
    oc_crop_pixels = oc_crop.pixel_count.sum()
    oc_crop["weighted_deltaE"] = oc_crop.deltaE_mean * oc_crop.pixel_count
    oc_crop = np.exp(np.log(oc_crop.weighted_deltaE).mean())/oc_crop_pixels

    oc_crop_err = bd_opp_cost[(bd_opp_cost.deltaE_mean_sem > 0)].copy()
    oc_crop_err_pixels = oc_crop_err.pixel_count.sum()
    oc_crop_err["weighted_deltaE_sem"] = oc_crop_err.deltaE_mean_sem * oc_crop_err.pixel_count
    oc_crop_err = np.exp(np.log(oc_crop_err.weighted_deltaE_sem).mean())/oc_crop_err_pixels
    


    # reshape bd_opp_cost for merging
    bd_opp_cost = bd_opp_cost[["ISO3", "item_name", "deltaE_mean", "deltaE_mean_sem"]]
    bd_opp_cost = bd_opp_cost.rename(columns={"ISO3":"Country_ISO", "item_name":"spam_name", "deltaE_mean":"life_extinctions_per_sp_per_km2", "deltaE_mean_sem": "life_extinctions_per_sp_per_km2_err"})

    # calculate global averages for fallback 1
    global_bd_opp_cost = pd.DataFrame()
    for v in bd_opp_cost.spam_name.dropna().unique():
        subset = bd_opp_cost[(bd_opp_cost.spam_name == v)&(bd_opp_cost.life_extinctions_per_sp_per_km2>0)]["life_extinctions_per_sp_per_km2"].dropna().values
        mean = np.exp(np.log(subset).mean())
        subset2 = bd_opp_cost[(bd_opp_cost.spam_name == v)&(bd_opp_cost.life_extinctions_per_sp_per_km2>0)]["life_extinctions_per_sp_per_km2_err"].dropna().values
        err = np.exp(np.log(subset2).mean())
        global_bd_opp_cost.loc[v, "life_extinctions_per_sp_per_km2_fallback"] = mean
        global_bd_opp_cost.loc[v, "life_extinctions_per_sp_per_km2_err_fallback"] = err

    # get spam_name to merge with life data
    wdf = wdf.merge(commodity_crosswalk[["Item_Code", f"spam_{spam_yr}"]], on="Item_Code", how="left")
    wdf = wdf.rename(columns={f"spam_{spam_yr}":"spam_name"})


    # merge in life data
    wdf = wdf.merge(bd_opp_cost, how="left", on=["Country_ISO", "spam_name"])

    # fallback 1 (global item averages)
    wdf = wdf.merge(global_bd_opp_cost, how="left", left_on=["spam_name"], right_index=True)
    wdf.loc[(wdf.life_extinctions_per_sp_per_km2.isna())|(wdf.life_extinctions_per_sp_per_km2==0), "life_extinctions_per_sp_per_km2"] = wdf.loc[(wdf.life_extinctions_per_sp_per_km2.isna())|(wdf.life_extinctions_per_sp_per_km2==0), "life_extinctions_per_sp_per_km2_fallback"]
    wdf.loc[(wdf.life_extinctions_per_sp_per_km2_err.isna())|(wdf.life_extinctions_per_sp_per_km2_err==0), "life_extinctions_per_sp_per_km2_err"] = wdf.loc[(wdf.life_extinctions_per_sp_per_km2_err.isna())|(wdf.life_extinctions_per_sp_per_km2_err==0), "life_extinctions_per_sp_per_km2_err_fallback"]



    # fallback 2 (global type averages)
    wdf.loc[(wdf.life_extinctions_per_sp_per_km2.isna())|(wdf.life_extinctions_per_sp_per_km2==0), "life_extinctions_per_sp_per_km2"] = oc_crop
    wdf.loc[(wdf.life_extinctions_per_sp_per_km2_err.isna())|(wdf.life_extinctions_per_sp_per_km2_err==0), "life_extinctions_per_sp_per_km2_err"] = oc_crop_err
    wdf = wdf.drop(columns=["life_extinctions_per_sp_per_km2_fallback", "life_extinctions_per_sp_per_km2_err_fallback"])

    # convert opp cost from km2 to m2
    wdf["life_extinctions_per_sp_per_m2"] = np.abs(wdf["life_extinctions_per_sp_per_km2"] / 1000000)


    # area the impact is charged against: pasture for primary, arable otherwise
    wdf.loc[wdf.Animal_Product=="Primary", "impacted_area_m2"] = wdf.loc[wdf.Animal_Product=="Primary", "pasture_area_m2_calc"]
    wdf.loc[wdf.Animal_Product=="Primary", "impacted_area_m2_err"] = wdf.loc[wdf.Animal_Product=="Primary", "pasture_area_m2_calc_err"]
    wdf.loc[wdf.Animal_Product!="Primary", "impacted_area_m2"] = wdf.loc[wdf.Animal_Product!="Primary", "arable_area_m2_calc"]
    wdf.loc[wdf.Animal_Product!="Primary", "impacted_area_m2_err"] = wdf.loc[wdf.Animal_Product!="Primary", "arable_area_m2_calc_err"]

    wdf["life_extinctions_per_sp_calc"] = wdf["impacted_area_m2"] * wdf["life_extinctions_per_sp_per_m2"]
    wdf["relerr"] = np.sqrt((wdf.life_extinctions_per_sp_per_km2_err/wdf.life_extinctions_per_sp_per_km2)**2 + (wdf.impacted_area_m2_err/wdf.impacted_area_m2)**2)
    wdf["life_extinctions_per_sp_calc_err"] = wdf["life_extinctions_per_sp_calc"] * wdf["relerr"]
    wdf.drop(columns=["relerr"], inplace=True)

    # carbon opportunity cost (COC)
    coc_path, coc_yr = fetch_coc_vals_path(year, datPath, use_2020)
    coc_opp_cost = pd.read_csv(coc_path)
    available_coc_bands = coc_opp_cost.band_name.unique().tolist()
    coc_opp_cost = coc_opp_cost[coc_opp_cost.band_name==coc_band_name]
    if len(coc_opp_cost) == 0:
        # without this the empty selection propagates as NaN and silently lands as
        # zero carbon opportunity cost in the aggregated outputs
        sys.exit(f"""No rows for coc band '{coc_band_name}' in {coc_path}; """
                 f"""available bands: {available_coc_bands}""")

    # source is tonnes C per km2; convert up front so the fallbacks below are
    # computed on the same basis as the merged values
    coc_opp_cost = coc_opp_cost.copy()
    coc_opp_cost["data_mean"] *= KG_CO2E_PER_TONNE_C
    coc_opp_cost["data_mean_sem"] *= KG_CO2E_PER_TONNE_C

    oc_crop_coc = coc_opp_cost[(coc_opp_cost.data_mean > 0)].copy()
    oc_crop_coc_pixels = oc_crop_coc.pixel_count.sum()
    oc_crop_coc["weighted_data_mean"] = oc_crop_coc.data_mean * oc_crop_coc.pixel_count
    oc_crop_coc = np.exp(np.log(oc_crop_coc.weighted_data_mean).mean())/oc_crop_coc_pixels

    oc_crop_coc_err = coc_opp_cost[(coc_opp_cost.data_mean_sem > 0)].copy()
    oc_crop_coc_err_pixels = oc_crop_coc_err.pixel_count.sum()
    oc_crop_coc_err["weighted_data_mean_sem"] = oc_crop_coc_err.data_mean_sem * oc_crop_coc_err.pixel_count
    oc_crop_coc_err = np.exp(np.log(oc_crop_coc_err.weighted_data_mean_sem).mean())/oc_crop_coc_err_pixels

    # reshape coc_opp_cost for merging
    coc_opp_cost = coc_opp_cost[["ISO3", "item_name", "data_mean", "data_mean_sem"]]
    coc_opp_cost = coc_opp_cost.rename(columns={"ISO3":"Country_ISO", "item_name":"spam_name", "data_mean":"carbon_kgco2e_per_km2", "data_mean_sem": "carbon_kgco2e_per_km2_err"})

    # calculate global averages for fallback 1
    global_coc_opp_cost = pd.DataFrame()
    for v in coc_opp_cost.spam_name.dropna().unique():
        subset = coc_opp_cost[(coc_opp_cost.spam_name == v)&(coc_opp_cost.carbon_kgco2e_per_km2>0)]["carbon_kgco2e_per_km2"].dropna().values
        mean = np.exp(np.log(subset).mean())
        subset2 = coc_opp_cost[(coc_opp_cost.spam_name == v)&(coc_opp_cost.carbon_kgco2e_per_km2>0)]["carbon_kgco2e_per_km2_err"].dropna().values
        err = np.exp(np.log(subset2).mean())
        global_coc_opp_cost.loc[v, "carbon_kgco2e_per_km2_fallback"] = mean
        global_coc_opp_cost.loc[v, "carbon_kgco2e_per_km2_err_fallback"] = err

    # merge in coc data
    wdf = wdf.merge(coc_opp_cost, how="left", on=["Country_ISO", "spam_name"])

    # fallback 1 (global item averages)
    wdf = wdf.merge(global_coc_opp_cost, how="left", left_on=["spam_name"], right_index=True)
    wdf.loc[(wdf.carbon_kgco2e_per_km2.isna())|(wdf.carbon_kgco2e_per_km2==0), "carbon_kgco2e_per_km2"] = wdf.loc[(wdf.carbon_kgco2e_per_km2.isna())|(wdf.carbon_kgco2e_per_km2==0), "carbon_kgco2e_per_km2_fallback"]
    wdf.loc[(wdf.carbon_kgco2e_per_km2_err.isna())|(wdf.carbon_kgco2e_per_km2_err==0), "carbon_kgco2e_per_km2_err"] = wdf.loc[(wdf.carbon_kgco2e_per_km2_err.isna())|(wdf.carbon_kgco2e_per_km2_err==0), "carbon_kgco2e_per_km2_err_fallback"]

    # fallback 2 (global type averages)
    wdf.loc[(wdf.carbon_kgco2e_per_km2.isna())|(wdf.carbon_kgco2e_per_km2==0), "carbon_kgco2e_per_km2"] = oc_crop_coc
    wdf.loc[(wdf.carbon_kgco2e_per_km2_err.isna())|(wdf.carbon_kgco2e_per_km2_err==0), "carbon_kgco2e_per_km2_err"] = oc_crop_coc_err
    wdf = wdf.drop(columns=["carbon_kgco2e_per_km2_fallback", "carbon_kgco2e_per_km2_err_fallback"])

    # convert coc from km2 to m2
    wdf["carbon_kgco2e_per_m2"] = wdf["carbon_kgco2e_per_km2"] / 1000000

    wdf["ghg_coc_kgco2e_calc"] = wdf["impacted_area_m2"] * wdf["carbon_kgco2e_per_m2"]
    wdf["relerr"] = np.sqrt((wdf.carbon_kgco2e_per_km2_err/wdf.carbon_kgco2e_per_km2)**2 + (wdf.impacted_area_m2_err/wdf.impacted_area_m2)**2)
    wdf["ghg_coc_kgco2e_calc_err"] = wdf["ghg_coc_kgco2e_calc"] * wdf["relerr"]

    wdf.drop(columns=["impacted_area_m2", "impacted_area_m2_err", "relerr"], inplace=True)

    wdf.to_csv(f"{country_savefile_path}/{filename}")
    return wdf

if __name__ == "__main__":
    YEARS = [2019]
    COUNTRIES = ["GBR"]
    import os
    os.chdir("../")
    for year in YEARS:
        for country in COUNTRIES:
            print(f"Processing {country} for year {year}...")
            hc = pd.read_csv(f"results/{year}/{country}/human_consumed.csv")
            get_impacts(hc, year, country, "human_consumed_impacts_wErr.csv")

