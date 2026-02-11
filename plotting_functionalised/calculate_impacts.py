import pandas as pd
import warnings 

def calculate_impacts(feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return calculate_impacts_sub(feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021)

def calculate_impacts_sub(feed_df_2010, feed_df_2021, pasture_df_2010, pasture_df_2021):

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
                                "Feed_E_per_m2":[Feed_E_per_m2],
                                "Feed_E":[country_feed_2010["bd_opp_cost_calc"].sum()],
                                "Pasture_E":[country_pasture_2010["bd_opp_cost_calc"].sum()]
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
                                "Feed_E_per_m2":[Feed_E_per_m2],
                                "Feed_E":[country_feed_2021["bd_opp_cost_calc"].sum()],
                                "Pasture_E":[country_pasture_2021["bd_opp_cost_calc"].sum()]
                                })

        Country_df_2021 = pd.concat([Country_df_2021, cdf_2021], ignore_index=True)

    return Country_df_2010, Country_df_2021
