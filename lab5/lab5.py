import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
import urllib.request
from datetime import datetime

st.set_page_config(page_title="Аналіз рослинності України", layout="wide")

UKR_REGIONS = {
    1: "Вінницька", 2: "Волинська", 3: "Дніпропетровська", 4: "Донецька",
    5: "Житомирська", 6: "Закарпатська", 7: "Запорізька", 8: "Івано-Франківська",
    9: "Київська", 10: "Кіровоградська", 11: "Луганська", 12: "Львівська",
    13: "Миколаївська", 14: "Одеська", 15: "Полтавська", 16: "Рівненська",
    17: "Сумська", 18: "Тернопільська", 19: "Харківська", 20: "Херсонська",
    21: "Хмельницька", 22: "Черкаська", 23: "Чернівецька", 24: "Чернігівська",
    25: "Крим", 26: "м. Київ", 27: "м. Севастополь"
}

# + Кешування даних
@st.cache_data
def load_data():
    NOAA_REGIONS = {
        1: "Cherkasy", 2: "Chernihiv", 3: "Chernivtsi", 4: "Crimea", 5: "Dnipropetrovsk",
        6: "Donetsk", 7: "Ivano-Frankivsk", 8: "Kharkiv", 9: "Kherson", 10: "Khmelnytskyy",
        11: "Kyiv", 12: "Kyiv_City", 13: "Kirovohrad", 14: "Luhansk", 15: "Lviv",
        16: "Mykolayiv", 17: "Odesa", 18: "Poltava", 19: "Rivne", 20: "Sevastopol",
        21: "Sumy", 22: "Ternopil", 23: "Transcarpathia", 24: "Vinnytsya", 25: "Volyn",
        26: "Zaporizhzhya", 27: "Zhytomyr"
    }
    
    DATA_DIR = "vhi_data"
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    all_dfs = []
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    # АВТОМАТИЧНЕ ЗАВАНТАЖЕННЯ
    if not files:
        with st.spinner("Дані відсутні. Завантажую свіжі дані з NOAA... Це займе близько хвилини."):
            progress_bar = st.progress(0)
            total_regions = len(NOAA_REGIONS)
            
            for idx, (prov_id, prov_name) in enumerate(NOAA_REGIONS.items()):
                url = f"https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={prov_id}&year1=1981&year2=2024&type=Mean"
                try:
                    with urllib.request.urlopen(url) as response:
                        new_data = response.read()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(DATA_DIR, f"vhi_id_{prov_id}_{timestamp}.csv")
                    
                    with open(filename + ".tmp", "wb") as f:
                        f.write(new_data)
                    os.rename(filename + ".tmp", filename)
                except Exception as e:
                    st.error(f"Помилка завантаження для {prov_name}: {e}")
                
                # Смуга прогресу
                progress_bar.progress((idx + 1) / total_regions)
                
            st.success("Дані успішно завантажено!")
            
            # Оновлення списку завантажених файлів
            files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

    # ЗЧИТУВАННЯ ТА ОЧИЩЕННЯ
    for file in files:
        df = pd.read_csv(file, header=1, usecols=[0, 1, 2, 3, 4, 5, 6], 
                         names=['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI'])
        df['Year'] = df['Year'].astype(str).str.replace(r'<[^>]*>', '', regex=True)
        df['VHI'] = df['VHI'].astype(str).str.replace(r'<[^>]*>', '', regex=True)
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['VHI'] = pd.to_numeric(df['VHI'], errors='coerce')
        df = df.dropna(subset=['Year', 'VHI'])
        df['Year'] = df['Year'].astype(int)
        df['Week'] = df['Week'].astype(int)
        
        prov_id = int(os.path.basename(file).split('_')[2])
        df['Region_ID'] = prov_id
        df['Region_Name'] = UKR_REGIONS.get(prov_id, "Невідомо")
        
        all_dfs.append(df)
        
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df['Date'] = master_df['Year'].astype(str) + " - Тиждень " + master_df['Week'].astype(str)
    return master_df

# Завантаження даних
df = load_data()

# Session state for RESET
if 'reset' not in st.session_state:
    st.session_state.reset = False

def reset_filters():
    st.session_state.index_param = 'VHI'
    st.session_state.region_param = 'Вінницька'
    st.session_state.year_range = (1981, 2024)
    st.session_state.week_range = (1, 52)
    st.session_state.sort_asc = False
    st.session_state.sort_desc = False

# ІНТЕРФЕЙС
st.sidebar.header("Налаштування параметрів")

# Віджети фільтрів
selected_index = st.sidebar.selectbox("Індекс:", ['VCI', 'TCI', 'VHI'], key='index_param')
selected_region = st.sidebar.selectbox("Область:", list(UKR_REGIONS.values()), key='region_param')

min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
selected_years = st.sidebar.slider("Інтервал років:", min_value=min_year, max_value=max_year, value=(1981, 2024), key='year_range')

selected_weeks = st.sidebar.slider("Інтервал тижнів:", min_value=1, max_value=52, value=(1, 52), key='week_range')

st.sidebar.markdown("---")
st.sidebar.subheader("Сортування таблиці")
sort_asc = st.sidebar.checkbox("За зростанням", key='sort_asc')
sort_desc = st.sidebar.checkbox("За спаданням", key='sort_desc')

st.sidebar.markdown("---")
st.sidebar.button("Reset", on_click=reset_filters, type="primary")

# ЛОГІКА ФІЛЬТРАЦІЇ
filtered_df = df[
    (df['Region_Name'] == selected_region) &
    (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1]) &
    (df['Week'] >= selected_weeks[0]) & (df['Week'] <= selected_weeks[1])
]

if sort_asc and sort_desc:
    st.warning("Увімкнено одночасно сортування за зростанням та спаданням. Сортування скасовано, дані відображаються у хронологічному порядку.")
elif sort_asc:
    filtered_df = filtered_df.sort_values(by=selected_index, ascending=True)
elif sort_desc:
    filtered_df = filtered_df.sort_values(by=selected_index, ascending=False)
else:
    filtered_df = filtered_df.sort_values(by=['Year', 'Week'])

# ВКЛАДКИ
st.title(f"Аналіз індексу {selected_index} для регіону: {selected_region}")

tab1, tab2, tab3 = st.tabs(["Загальна таблиця", "Часовий графік", "Порівняння областей"])

with tab1:
    st.subheader(f"Таблиця даних ({selected_years[0]}-{selected_years[1]} рр.)")
    # Лише релевантні колонки
    st.dataframe(filtered_df[['Year', 'Week', 'VCI', 'TCI', 'VHI']], use_container_width=True)

with tab2:
    st.subheader(f"Динаміка {selected_index} у часі")
    
    plot_df = filtered_df.sort_values(by=['Year', 'Week']) 
    
    fig = px.line(plot_df, x='Date', y=selected_index, 
                  title=f'{selected_index} по тижнях',
                  labels={'Date': 'Час (Рік - Тиждень)', selected_index: 'Значення індексу'})
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Порівняння середніх значень з іншими областями")
    st.markdown(f"Відображається середнє значення {selected_index} за {selected_years[0]}-{selected_years[1]} роки (тижні з {selected_weeks[0]} по {selected_weeks[1]}).")
    
    # Середнє значення для всіх областей за вибраний період
    all_regions_filtered = df[
        (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1]) &
        (df['Week'] >= selected_weeks[0]) & (df['Week'] <= selected_weeks[1])
    ]
    
    avg_per_region = all_regions_filtered.groupby('Region_Name')[selected_index].mean().reset_index()
    avg_per_region = avg_per_region.sort_values(by=selected_index, ascending=False)
    
    # + колонка іншого кольору
    avg_per_region['Колір'] = avg_per_region['Region_Name'].apply(
        lambda x: 'Вибрана область' if x == selected_region else 'Інші області'
    )
    
    fig_comp = px.bar(avg_per_region, x='Region_Name', y=selected_index, color='Колір',
                      color_discrete_map={'Вибрана область': '#FF4B4B', 'Інші області': '#636EFA'},
                      title=f"Середній {selected_index} по Україні",
                      labels={'Region_Name': 'Область', selected_index: f'Середній {selected_index}'})
    
    st.plotly_chart(fig_comp, use_container_width=True)