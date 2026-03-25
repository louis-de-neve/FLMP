"""
This code is a translation/re-written python script of the original R code of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7

Please cite ;-)
(c) Florian Schwarzmueller, December 2021
Re-written in Python, October 2025 by Louis De Neve
"""

from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from numba import jit
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
np.seterr(divide="ignore")

def eliminate_dates(reporting_dates:pd.DataFrame, function_dataframe:pd.DataFrame) -> pd.DataFrame:
    # removes countries that were not correctly reported
    
    reporting_dates_start = reporting_dates[["Country_Code", "Start_Year"]].dropna()
    reporting_dates_end = reporting_dates[["Country_Code", "End_Year"]].dropna()

    for country, year in reporting_dates_start.values:
        function_dataframe.loc[(function_dataframe["Reporter_Country_Code"] == country) & (function_dataframe["Year"] < year), "Value"] = 0
    for country, year in reporting_dates_end.values:
        function_dataframe.loc[(function_dataframe["Reporter_Country_Code"] == country) & (function_dataframe["Year"] > year), "Value"] = 0

    return function_dataframe

@jit(nopython=True)
def calculate_mrio_matrices(Z, p):
    """JIT-compiled version of matrix calculations"""
    summation_vector = np.ones(len(p))
    x = p + Z @ summation_vector
    
    one_over_x = np.where(x != 0, 1.0/x, 0.0)
    A = Z @ np.diag(one_over_x)
    
    I = np.eye(len(p))
    R = np.linalg.pinv(I - A) @ np.diag(p) # note pseudo-inverse rather than inverse (inverse creates some extra)
    
    ac = x - Z.sum(axis=0)
    c = ac * one_over_x
    R_bar = np.diag(c) @ R
    
    return R_bar


def mrio_model(year, p_data, prod_data, countries, country_dict):

    

    data_subset = p_data[(p_data["Year"] == year)]
    production_data_subset = prod_data[(prod_data["Year"] == year)]

    production_data_subset.loc[production_data_subset["Value"].isna(), "Value"] = 0

    

    Z = np.zeros((len(countries), len(countries)))

    for _, row in data_subset.iterrows():
        i = country_dict[row["Consumer_Country_Code"]]
        j = country_dict[row["Producer_Country_Code"]]
        Z[i, j] = row["Value_Sum"] # denoted Z in Kastner 2011

    Z[np.isnan(Z)] = 0

    p = np.zeros((len(countries),)) 
    for _, row in production_data_subset.iterrows():
        i = country_dict[row["Area_Code"]]
        p[i] = row["Value"] # denoted p in Kastner 2011

    sum_vector = np.ones(len(countries))
    imports = Z @ sum_vector
    exports = sum_vector @ Z
    production_minimum = exports - imports
    production_minimum[production_minimum < 0] = 0
    p = np.where(p<production_minimum, production_minimum, p)
    return Z, p
    R_bar = calculate_mrio_matrices(Z, p)
   
    return R_bar

def calculate_conversion_factors(conversion_opt, content_factors, item_map):
        """Calculate conversion factors from processed to primary items"""

        # Calculate conversion factors
        if conversion_opt not in content_factors.columns:
                raise ValueError(f"Primary Conversion option ({conversion_opt}) not available")
                
        joined = item_map.merge(
            content_factors[["Item_Code", conversion_opt]], 
            left_on="FAO_code", 
            right_on="Item_Code", 
            how="left")

        joined = joined.merge(
            content_factors[["Item_Code", conversion_opt]], 
            left_on="primary_item", 
            right_on="Item_Code", 
            how="left",
            suffixes=("_processed", "_primary"))

        joined["Conversion_factor"] = joined[f"{conversion_opt}_processed"] / joined[f"{conversion_opt}_primary"]
        joined = joined.sort_values("FAO_code")
        joined.loc[~np.isfinite(joined["Conversion_factor"]), "Conversion_factor"] = 0
        result = joined.dropna(subset=["Conversion_factor"])
        conversion_factors = result[["FAO_code", "FAO_name", "primary_item", "FAO_name_primary", "Conversion_factor"]]
        return conversion_factors


def calculate_trade_matrix(
        conversion_opt="dry_matter",
        prefer_import="import", 
        year=2013,
        historic="Historic",
        results_dir=Path("./results")):
    """Calculate Trade Matrix module for MRIO pipeline"""

    print("    Loading trade data...")
    cache_file_primary = "primary_data_cache.pkl"
    cache_file_production = "production_all_cache.pkl"

    if os.path.exists(cache_file_primary) and os.path.exists(cache_file_production):
        with open(cache_file_primary, 'rb') as f:
            primary_data = pickle.load(f)
        with open(cache_file_production, 'rb') as f:
            production_all = pickle.load(f)
        print("    Loaded cached data...")
    
    else:
    # File paths
        item_map_filename = "input_data/primary_item_map_feed.csv" 
        trade_filename = "input_data/Trade_DetailedTradeMatrix_E_All_Data_(Normalized).csv" # FAOSTAT import
        reporting_filename = "input_data/Reporting_Dates.xls"
        content_filename = "input_data/content_factors_per_100g.xlsx"
        production_filename = "input_data/Production_Crops_Livestock_E_All_Data_(Normalized).csv"
        sugar_processing_filename = f"input_data/FoodBalanceSheets{historic}_E_All_Data_(Normalized).csv"


        # Load Files
        item_map = pd.read_csv(item_map_filename, encoding="Latin-1")
        raw_trade_data = pd.read_csv(trade_filename, encoding="Latin-1")
        reporting_date = pd.read_excel(reporting_filename)
        content_factors = pd.read_excel(content_filename, skiprows=1)
        sugar_processing = pd.read_csv(sugar_processing_filename, encoding="Latin-1")                                
        production = pd.read_csv(production_filename, low_memory=False)


        # Rename columns
        item_map.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        raw_trade_data.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        reporting_date.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        content_factors.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        sugar_processing.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        production.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)

        # fix missing data from indian cattle - data from FAO: https://www.fao.org/faostat/en/#data/SCL
        indian_cattle_prod = [998071.03, 989522.18, 980561.33, 971291.48, 960991.17, 931645.26, 913009.07, 899727.75, 901236.5, 915639.94, 915639.94, 915639.94, 915639.94, 915639.94]
        production.loc[(production["Item_Code"]==867)&(production["Area_Code"]==100)&(production["Element_Code"]==5510)&(production["Year"]>=2010), "Value"] = indian_cattle_prod

        # Select year
        # raw_trade_data = raw_trade_data[raw_trade_data["Year"] == year]
        # sugar_processing = sugar_processing[sugar_processing["Year"] == year]
        # production = production[production["Year"] == year]
        raw_trade_data = raw_trade_data[(raw_trade_data["Year"] >= 2010)&(raw_trade_data["Year"]<=2021)]
        sugar_processing = sugar_processing[(sugar_processing["Year"] >= 2010)&(sugar_processing["Year"]<=2021)]
        production = production[(production["Year"] >= 2010)&(production["Year"]<=2021)]

        # Tweaks for slightly different files
        production_all = production[["Area_Code", "Area", "Item_Code", "Item", "Element_Code", "Element", "Year_Code", "Year", "Unit", "Value"]]

        item_map[item_map["FAO_code"]==156] = [156, "Sugar cane", 2545, "Sugar agregate"]
        item_map[item_map["FAO_code"]==157] = [157, "Sugar beet", 2545, "Sugar agregate"]
        # production_crops.drop(columns=["Note"], inplace=True)
        # production_offals = sugar_processing[(sugar_processing["Element_Code"] == 5511) & (sugar_processing["Item_Code"] == 2736)]
        # production_offals['Element_Code'] = 5510
        # production_offals['Value'] = production_offals['Value']*1000
        
        print("    Preprocessing trade data...")

        # Combine and filter
        # production_all = pd.concat([production_all, production_offals], ignore_index=True)
        production_all = production_all[(production_all["Area_Code"]<300) & (production_all["Element_Code"]==5510)]

        # harmonise import and export data

        data_import = raw_trade_data[raw_trade_data["Element_Code"] == 5610][["Reporter_Country_Code", "Partner_Country_Code", "Element_Code", "Item_Code", "Year", "Value"]]
        data_export = raw_trade_data[raw_trade_data["Element_Code"] == 5910][["Partner_Country_Code", "Reporter_Country_Code", "Element_Code", "Item_Code", "Year", "Value"]]


        data_import = eliminate_dates(reporting_date, data_import)
        data_export = eliminate_dates(reporting_date, data_export)

        data_import.loc[data_import["Reporter_Country_Code"] == data_import["Partner_Country_Code"], "Value"] = 0
        data_export.loc[data_export["Reporter_Country_Code"] == data_export["Partner_Country_Code"], "Value"] = 0
        data_import = data_import[data_import["Value"] != 0]
        data_export = data_export[data_export["Value"] != 0]

        data_import.rename(columns={"Reporter_Country_Code": "Consumer_Country_Code", "Partner_Country_Code": "Producer_Country_Code"}, inplace=True)
        data_export.rename(columns={"Reporter_Country_Code": "Producer_Country_Code", "Partner_Country_Code": "Consumer_Country_Code"}, inplace=True)

        if prefer_import == "import":
            trade_data = pd.concat([data_import, data_export], ignore_index=True)
            trade_data = trade_data.drop_duplicates(subset=["Consumer_Country_Code", "Producer_Country_Code", "Year", "Item_Code"],
                                                    keep="first")
        elif prefer_import == "export":
            trade_data = pd.concat([data_export, data_import], ignore_index=True)
            trade_data = trade_data.drop_duplicates(subset=["Consumer_Country_Code", "Producer_Country_Code", "Year", "Item_Code"],
                                                    keep="first")
        else:
            raise ValueError("prefer_import must be either 'import' or 'export'")

        trade_data = trade_data.sort_values(["Consumer_Country_Code", "Producer_Country_Code"])

        conversion_factors = calculate_conversion_factors(conversion_opt, content_factors, item_map)


        trade_data = trade_data.merge(
            conversion_factors,
            left_on="Item_Code",
            right_on="FAO_code",
            how="left")
        trade_data.drop(columns=["FAO_code"], inplace=True)

        trade_data["primary_Value"] = trade_data["Value"] * trade_data["Conversion_factor"]

        primary_data = trade_data.groupby(["Consumer_Country_Code", "Producer_Country_Code", "Year", "primary_item"])["primary_Value"].sum().reset_index()
        primary_data.columns = ["Consumer_Country_Code", "Producer_Country_Code", "Year", "primary_item", "Value_Sum"]
                
        primary_data = primary_data[
            (primary_data["primary_item"] != 0) & 
            (primary_data["primary_item"].notna()) &
            (primary_data["Value_Sum"].notna())]


    
    # Add sugar production to main production data
    
        with open(cache_file_primary, 'wb') as f:
            pickle.dump(primary_data, f)
        with open(cache_file_production, 'wb') as f:
            pickle.dump(production_all, f)
        print("    Cached data saved...")


    unique_combinations = primary_data[["Year", "primary_item"]].drop_duplicates()
    print(unique_combinations)
    
    

    mrio_output = []
    for ic in unique_combinations["primary_item"].unique():
        p_data = primary_data[primary_data["primary_item"] == ic]
        prod_data = production_all[production_all["Item_Code"] == ic]
        producers = prod_data["Area_Code"].unique()
        importers = p_data["Consumer_Country_Code"].unique()
        exporters = p_data["Producer_Country_Code"].unique()
        traders = np.union1d(importers, exporters)
        countries = np.union1d(producers, traders)
        country_dict = {code: idx for idx, code in enumerate(countries)}
        Zs = []
        ps = []

        yrs = unique_combinations[unique_combinations["primary_item"] == ic]["Year"].unique()
        for yr in yrs:
            Z, p = mrio_model(yr, p_data, prod_data, countries, country_dict)
            if Z.shape != (0,):
                Zs.append(Z)
                ps.append(p)
        Zs = np.array(Zs)
        Ps = np.array(ps)


        iqr = np.nanpercentile(np.where(np.isclose(Zs,0), np.nan, Zs), 75, axis=0) - np.nanpercentile(np.where(np.isclose(Zs,0), np.nan, Zs), 25, axis=0)
        q3 = np.nanpercentile(np.where(np.isclose(Zs,0), np.nan, Zs), 75, axis=0)
        p_iqr = np.nanpercentile(np.where(np.isclose(Ps,0), np.nan, Ps), 75, axis=0) - np.nanpercentile(np.where(np.isclose(Ps,0), np.nan, Ps), 25, axis=0)
        p_q3 = np.nanpercentile(np.where(np.isclose(Ps,0), np.nan, Ps), 75, axis=0)
        Zs = np.where(Zs>q3+1.5*iqr, 0, Zs) # remove outliers
        Ps = np.where(Ps>p_q3+1.5*p_iqr, 0, Ps) # remove outliers

        std = np.nanstd(np.where(np.isclose(Zs,0), np.nan, Zs), axis=0)
        mean = np.nanmean(np.where(np.isclose(Zs,0), np.nan, Zs), axis=0)
        p_std = np.nanstd(np.where(np.isclose(Ps,0), np.nan, Ps), axis=0)
        p_mean = np.nanmean(np.where(np.isclose(Ps,0), np.nan, Ps), axis=0)

        mean[np.isnan(mean)] = 0
        p_mean[np.isnan(p_mean)] = 0

        std[np.isnan(std)] = 0
        std[std<0] = 0
        p_std[np.isnan(p_std)] = 0
        p_std[p_std<0] = 0

        Z = mean
        p = p_mean

        truth = calculate_mrio_matrices(Z, p)

        R_std = monte_carlo(Z, p, std, p_std)
        R_err = R_std/truth
        Rmax = np.max(truth)
        R_err[np.isnan(R_err)] = 0
        R_err = np.abs(R_err)
        thresh = 100
        truth[truth<thresh] = thresh
        R_err[truth==thresh] = 0

        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        axs[0].imshow(truth, cmap="viridis", norm="log", vmin=thresh, vmax=Rmax, interpolation="none")
        axs[1].imshow(R_err, cmap="viridis", vmin=0, vmax=2, interpolation="none")
        axs[0].set_title("R_bar (Final MRIO Matrix)")
        cbar0 = plt.colorbar(axs[0].images[0], ax=axs[0])
        cbar0.set_label("Value")
        
        axs[1].set_title("Relative Error in R_bar")
        cbar1 = plt.colorbar(axs[1].images[0], ax=axs[1])
        cbar1.set_label("Relative Error")
        plt.show()


def monte_carlo(Z, p, Z_std, p_std, iterations=1000):
    """Monte Carlo simulation to estimate uncertainty in R_bar"""
    results = []
    np.random.seed(0)
    for _ in range(iterations):
        Z_noise = np.random.normal(0, Z_std) # err% noise
        Z_noise[Z_noise<-2*Z_std] = -2*Z_std[Z_noise<-2*Z_std] # limit on pertubation
        Z_noise[Z_noise>2*Z_std] = 2*Z_std[Z_noise>2*Z_std] # limit on pertubation
        Z_perturbed = Z+Z_noise
        Z_perturbed[Z_perturbed<0] = 0

        p_noise = np.random.normal(0, p_std) 
        p_noise[p_noise<-2*p_std] = -2*p_std[p_noise<-2*p_std] # limit on pertubation
        p_noise[p_noise>2*p_std] = 2*p_std[p_noise>2*p_std] # limit on pertubation
        p_perturbed = p+p_noise# err% noise
        p_perturbed[p_perturbed<0] = 0

        R_perturbed = calculate_mrio_matrices(Z_perturbed, p_perturbed)
        results.append(R_perturbed)

    results = np.array(results)
    R_mean = np.mean(results, axis=0)
    R_stdev = np.std(results, axis=0)
    # R_s = R_stdev[~np.isnan(R_stdev)]
    # R_m = R_mean[~np.isnan(R_stdev)]
    # R_s = R_s[R_m!=0]
    # R_m = R_m[R_m!=0]
    # print(np.average(R_s/R_m, weights=R_m))
    return R_stdev
        


if __name__ == "__main__":
    import os
    os.chdir("../")
    # Example usage
    import warnings
    import pickle
    import os
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        calculate_trade_matrix(
        conversion_opt="dry_matter",
        prefer_import="import",
        year=2010,
        historic="",
        results_dir=Path("./results")
    )