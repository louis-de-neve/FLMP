import pandas as pd
from pathlib import Path

pasture_items = [867, 882, 947, 951, 977, 982, 1017, 1020, 1097]
pasture_item_strings = ["Cow_Meat", "Cow_Milk", "Buffalo_Meat", "Buffalo_Milk", "Sheep_Meat", "Sheep_Milk", "Goat_Meat", "Goat_Milk", "Horse_Meat"]
feed_items = [1035, 1058, 1062, 1069, 1073, 1080, 1091, 1108, 1127, 1141, 1166]
feed_item_strings = ["Pig_Meat", "Chicken_Meat", "Hen_Eggs", "Duck_Meat", "Goose_Meat", "Turkey_Meat", "Other_Eggs", "Donkey_Meat", "Camel_Meat", "Rabbit_Meat", "Other_Meat"]
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    area_codes = pd.read_excel(f"input_data/nocsDataExport_20251021-164754.xlsx", engine="openpyxl")

for i, item in enumerate(feed_items):
    
    by_year: dict[str, pd.Series] = {}
    for year in range(2010, 2021):
        feed_file = Path(f"results/{year}/.mrio/TradeMatrixFeed_import_dry_matter.csv")

        df = pd.read_csv(feed_file)
        # Filter for pasture items and remove NaN values
        filtered_df = df[df['Animal_Product_Code']==item].dropna()

        df = filtered_df[["Consumer_Country_Code", "Animal_Product_Code", "Value"]].copy()
        by_year[str(year)] = df.groupby(["Consumer_Country_Code"])["Value"].sum()
        by_year[str(year)] = 1000*by_year[str(year)] # convert from tonnes to kg
    out = pd.DataFrame(by_year)
    ac = area_codes[["ISO3", "FAOSTAT"]].rename(columns={"ISO3":"Country_ISO", "FAOSTAT":"Consumer_Country_Code"})
    out = out.merge(ac, on="Consumer_Country_Code", how="left")
    out = out.drop(columns=["Consumer_Country_Code"]).set_index("Country_ISO")
    out = out.sort_index()
    output_path = f"feed_use/feed_use_kg_{feed_item_strings[i]}.csv"
    out.to_csv(output_path)
        
    