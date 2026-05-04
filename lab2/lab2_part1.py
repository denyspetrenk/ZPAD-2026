import urllib.request
import os
import hashlib
import glob
from datetime import datetime
import pandas as pd

DATA_DIR = "vhi_data"
SKIP_DOWNLOAD = False

REGIONS = {
    1: "Cherkasy", 2: "Chernihiv", 3: "Chernivtsi", 4: "Crimea", 5: "Dnipropetrovsk",
    6: "Donetsk", 7: "Ivano-Frankivsk", 8: "Kharkiv", 9: "Kherson", 10: "Khmelnytskyy",
    11: "Kyiv", 12: "Kyiv_City", 13: "Kirovohrad", 14: "Luhansk", 15: "Lviv",
    16: "Mykolayiv", 17: "Odesa", 18: "Poltava", 19: "Rivne", 20: "Sevastopol",
    21: "Sumy", 22: "Ternopil", 23: "Transcarpathia", 24: "Vinnytsya", 25: "Volyn",
    26: "Zaporizhzhya", 27: "Zhytomyr"
}

ukr_mapping = {
    "Vinnytsya": 1, "Volyn": 2, "Dnipropetrovsk": 3, "Donetsk": 4,
    "Zhytomyr": 5, "Transcarpathia": 6, "Zaporizhzhya": 7,
    "Ivano-Frankivsk": 8, "Kyiv": 9, "Kirovohrad": 10,
    "Luhansk": 11, "Lviv": 12, "Mykolayiv": 13, "Odesa": 14,
    "Poltava": 15, "Rivne": 16, "Sumy": 17, "Ternopil": 18,
    "Kharkiv": 19, "Kherson": 20, "Khmelnytskyy": 21,
    "Cherkasy": 22, "Chernivtsi": 23, "Chernihiv": 24,
    "Crimea": 25, "Kyiv_City": 26, "Sevastopol": 27
}

def download_vhi_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    for prov_id, prov_name in REGIONS.items():
        url = f"https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={prov_id}&year1=1981&year2=2024&type=Mean"
        
        try:
            with urllib.request.urlopen(url) as response:
                new_data = response.read()
            
            new_hash = hashlib.md5(new_data).hexdigest()
            old_files = glob.glob(os.path.join(DATA_DIR, f"vhi_id_{prov_id}_*.csv"))
            needs_update = True
            
            if old_files:
                with open(old_files[-1], "rb") as f:
                    old_hash = hashlib.md5(f.read()).hexdigest()
                if new_hash == old_hash:
                    needs_update = False
            
            if needs_update:

                for old_file in old_files:
                    os.remove(old_file)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(DATA_DIR, f"vhi_id_{prov_id}_{timestamp}.csv")
                print(f' + Оновлення файлу {os.path.join(DATA_DIR, f"vhi_id_{prov_id}_{timestamp}.csv")}...')
                
                with open(filename + ".tmp", "wb") as f:
                    f.write(new_data)
                os.rename(filename + ".tmp", filename)
            else:
                print(f' - Файл {os.path.join(DATA_DIR, f"vhi_id_{prov_id}_*.csv")} актуальний, оновлення не потрібне!')

        except Exception as e:
            print(f"Error downloading {prov_name}: {e}")

def process_vhi_data():
    all_dfs = []
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    for file in files:
        prov_id = int(os.path.basename(file).split('_')[2])
        prov_name = REGIONS[prov_id]
        
        df = pd.read_csv(
            file, 
            header=1, 
            usecols=[0, 1, 2, 3, 4, 5, 6], 
            names=['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI']
        )
        
        df['Year'] = df['Year'].astype(str).str.replace(r'<[^>]*>', '', regex=True)
        df['VHI'] = df['VHI'].astype(str).str.replace(r'<[^>]*>', '', regex=True)
        
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['VHI'] = pd.to_numeric(df['VHI'], errors='coerce')

        df = df.dropna(subset=['Year', 'VHI'])
        
        df['Year'] = df['Year'].astype(int)
        df['Week'] = df['Week'].astype(int)
        
        df['Region_Name'] = prov_name
        df['Region_ID'] = ukr_mapping[prov_name] 
        
        df = df[['Region_ID', 'Region_Name', 'Year', 'Week', 'VCI', 'TCI', 'VHI']]
        all_dfs.append(df)
        
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()
    
def get_vhi_series_by_year(df, region_id, year):
    return df[(df['Region_ID'] == region_id) & (df['Year'] == year)][['Week', 'VHI']]

def get_vhi_for_regions_and_years(df, region_ids, start_year, end_year):
    return df[(df['Region_ID'].isin(region_ids)) & (df['Year'] >= start_year) & (df['Year'] <= end_year)][['Region_ID', 'Region_Name', 'Year', 'Week', 'VHI']]

def get_vhi_statistics(df, region_ids, start_year, end_year):
    filtered_df = df[(df['Region_ID'].isin(region_ids)) & (df['Year'] >= start_year) & (df['Year'] <= end_year)]
    if filtered_df.empty:
        return "No data found"
    return filtered_df['VHI'].agg(['min', 'max', 'mean', 'median'])


if not SKIP_DOWNLOAD:

    download_vhi_data()

df_clean = process_vhi_data()

if not df_clean.empty:
    df_clean = df_clean.sort_values(by=['Region_ID', 'Year', 'Week']).reset_index(drop=True)

    stats_kyiv = get_vhi_statistics(df_clean, [9], 2019, 2024)
    vhi_vinnytsia_2020 = get_vhi_series_by_year(df_clean, 1, 2020)
    vhi_multi = get_vhi_for_regions_and_years(df_clean, [1, 2], 2010, 2015)

    print("--- Stats Kyiv (2019-2024) ---")
    print(stats_kyiv)
    
    print("\n--- Vinnytsia 2020 ---")
    print(vhi_vinnytsia_2020.head())
    
    print("\n--- Multi Region (2010-2015) ---")
    print(vhi_multi.head())