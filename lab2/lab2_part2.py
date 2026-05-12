import os
import time
import zipfile
import requests
import pandas as pd

# Налаштування URL та файлів
DATA_URL = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
ZIP_FILE = "dataset.zip"
TXT_FILE = "household_power_consumption.txt"

# Завантаження та розпакування даних, якщо їх ще немає
if not os.path.exists(TXT_FILE):
    print("Завантаження архіву...")
    response = requests.get(DATA_URL)
    with open(ZIP_FILE, 'wb') as f:
        f.write(response.content)
    
    print("Розпакування архіву...")
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall()

print("Зчитування даних...")
df = pd.read_csv(TXT_FILE, sep=';', na_values=['?'], low_memory=False)

# Очищення та підготовка даних
df_clean = df.dropna().copy()
df_clean['Datetime'] = pd.to_datetime(df_clean['Date'] + ' ' + df_clean['Time'], format='%d/%m/%Y %H:%M:%S')
print(f"Дані очищено! Кількість рядків: {len(df_clean)}")

# Завдання А: Потужність > 5 кВт
def filter_high_power(data):
    return data[data['Global_active_power'] > 5.0]

# Завдання Б: Сила струму 19-20 А, Група 2 > Група 3
def filter_current_and_appliances(data):
    cond = (data['Global_intensity'].between(19.0, 20.0)) & \
           (data['Sub_metering_2'] > data['Sub_metering_3'])
    return data[cond]

# Завдання В: Випадкові 500 000 записів та середнє для 3-х груп
def random_sample_means(data):
    sample = data.sample(n=500000, replace=False, random_state=42)
    return sample[['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']].mean()

# Завдання Г: Після 18:00, Потужність > 6, Група 2 найбільша. Вибірка кожних 3-х і 4-х.
def complex_evening_filter(data):
    cond1 = (data['Datetime'].dt.hour >= 18) & (data['Global_active_power'] > 6.0)
    res = data[cond1]
    
    cond2 = (res['Sub_metering_2'] > res['Sub_metering_1']) & \
            (res['Sub_metering_2'] > res['Sub_metering_3'])
    res = res[cond2]
    
    half_index = len(res) // 2
    
    # Беремо кожен 3-й з першої половини та кожен 4-й з другої
    return pd.concat([res.iloc[:half_index:3], res.iloc[half_index::4]])

print("\n--- Профілювання часу виконання ---")

start = time.time()
res_a = filter_high_power(df_clean)
print(f"Завдання А: {len(res_a)} записів. Час: {time.time() - start:.4f} сек")

start = time.time()
res_b = filter_current_and_appliances(df_clean)
print(f"Завдання Б: {len(res_b)} записів. Час: {time.time() - start:.4f} сек")

start = time.time()
res_c = random_sample_means(df_clean)
print(f"Завдання В: Середні значення:\n{res_c.to_string()}\nЧас: {time.time() - start:.4f} сек")

start = time.time()
res_d = complex_evening_filter(df_clean)
print(f"Завдання Г: {len(res_d)} записів. Час: {time.time() - start:.4f} сек")

print("\n--- Додаткові операції ---")

# Нормування та стандартизація на копії вибірки А
df_demo = res_a[['Global_active_power', 'Global_intensity']].copy()

# Min-Max Scaling
min_val, max_val = df_demo['Global_active_power'].min(), df_demo['Global_active_power'].max()
df_demo['GAP_Normalized'] = (df_demo['Global_active_power'] - min_val) / (max_val - min_val)

# Z-score Standardization
mean_val, std_val = df_demo['Global_intensity'].mean(), df_demo['Global_intensity'].std()
df_demo['Intensity_Standardized'] = (df_demo['Global_intensity'] - mean_val) / std_val

print("Результати нормування та стандартизації (перші 5 рядків):")
print(df_demo.head())

# Кореляція
pearson_corr = df_clean['Global_active_power'].corr(df_clean['Global_intensity'], method='pearson')
spearman_corr = df_clean['Global_active_power'].corr(df_clean['Global_intensity'], method='spearman')

print(f"\nКореляція Пірсона: {pearson_corr:.4f}")
print(f"Кореляція Спірмена: {spearman_corr:.4f}")

# One Hot Encoding (перші 10 000 рядків)
df_clean['DayOfWeek'] = df_clean['Datetime'].dt.day_name()
df_ohe = pd.get_dummies(df_clean.head(10000), columns=['DayOfWeek'], dtype=int)

ohe_columns = [col for col in df_ohe.columns if 'DayOfWeek' in col]
print("\nНові колонки після One Hot Encoding:")
print(df_ohe[ohe_columns].head())