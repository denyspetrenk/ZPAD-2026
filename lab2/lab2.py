import urllib.request
import pandas as pd
from datetime import datetime


# Завантаження файлів областей

current_year = datetime.now().year

for i in range(1, 28):

    url = f'https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={i}&year1=1981&year2={current_year}&type=Mean'

    try:
        print(f"Завантаження даних для ID {i}...")
        
        # Відкриваємо та читаємо дані
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            
            clean_content = content.replace('<pre>', '').replace('</pre>', '')

            # Зберігаємо у файл
            filename = f'vhi_id_{i}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
            with open(filename, 'w') as f:
                f.write(clean_content)
                
        print(f"Збережено у файл: {filename}")
    except Exception as e:
        print(f"Помилка при завантаженні ID {i}: {e}")
