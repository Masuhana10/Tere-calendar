import requests
import json
from datetime import datetime, timedelta
import re

# 現在の年月を自動で取得
current_ym = datetime.now().strftime("%Y%m")

# 🎯 推しメンのID（池田瑛紗さんは 55397）
TARGET_MEMBER_ID = "55397"

url = 'https://www.nogizaka46.com/s/n46/api/list/schedule'

# 全員のスケジュールを一括取得
params = {
    'ima': '4923',
    'dy': current_ym,
    'callback': 'res'
}
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"{current_ym[:4]}年{current_ym[4:]}月のスケジュールを取得して、究極のフィルターをかけます...")
response = requests.get(url, headers=headers, params=params)
response.encoding = 'utf-8'

json_text = response.text.strip()
if json_text.startswith('res('): json_text = json_text[4:]
if json_text.endswith(');'): json_text = json_text[:-2]
elif json_text.endswith(')'): json_text = json_text[:-1]

data = json.loads(json_text)
schedule_list = data.get('data', [])

ics_lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Nogizaka46 Oshi Calendar//EN",
    "CALSCALE:GREGORIAN",
    "X-WR-CALNAME:てれぱん＆乃木坂46スケジュール",
    "X-WR-TIMEZONE:Asia/Tokyo"
]

def parse_custom_time(date_str, time_str):
    if not time_str: return None
    hours, minutes = map(int, time_str.split(':'))
    base_date = datetime.strptime(date_str, "%Y/%m/%d")
    days = hours // 24
    remaining_hours = hours % 24
    return base_date + timedelta(days=days, hours=remaining_hours, minutes=minutes)

for item in schedule_list:
    arti_code = item.get('arti_code', [])
    
    # 🛡️【究極のフィルター】
    if not arti_code or TARGET_MEMBER_ID in str(arti_code):
        pass # チェック合格
    else:
        continue # 他のメンバー単独の予定は捨てる

    title = item.get('title', 'タイトルなし')
    date_str = item.get('date', '') 
    start_time_str = item.get('start_time', '')
    end_time_str = item.get('end_time', '')
    text_html = item.get('text', '')
    link = item.get('link', '')

    if not date_str:
        continue

    desc = re.sub(r'<br\s*/?>', '\\n', text_html)
    desc = re.sub(r'<[^>]+>', '', desc)
    if link:
        desc += f"\\n\\n▼詳細リンク\\n{link}"

    try:
        date_obj = datetime.strptime(date_str, "%Y/%m/%d")
        
        if start_time_str == '':
            start_str = date_obj.strftime("%Y%m%d")
            end_obj = date_obj + timedelta(days=1)
            end_str = end_obj.strftime("%Y%m%d")
            dtstart_line = f"DTSTART;VALUE=DATE:{start_str}"
            dtend_line = f"DTEND;VALUE=DATE:{end_str}"
        else:
            start_dt = parse_custom_time(date_str, start_time_str)
            start_str = start_dt.strftime("%Y%m%dT%H%M%S")
            if end_time_str != '':
                end_dt = parse_custom_time(date_str, end_time_str)
                if end_dt < start_dt: end_dt += timedelta(days=1)
                end_str = end_dt.strftime("%Y%m%dT%H%M%S")
            else:
                end_dt = start_dt + timedelta(hours=1)
                end_str = end_dt.strftime("%Y%m%dT%H%M%S")
            
            dtstart_line = f"DTSTART;TZID=Asia/Tokyo:{start_str}"
            dtend_line = f"DTEND;TZID=Asia/Tokyo:{end_str}"
            
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            dtstart_line,
            dtend_line,
            f"DESCRIPTION:{desc}",
            f"URL:{link}",
            "END:VEVENT"
        ])
        print(f"追加: {date_str} {start_time_str} - {title}")
        
    except Exception as e:
        print(f"エラー（スキップしました）: {title} - {e}")

ics_lines.append("END:VCALENDAR")

output_file = 'oshi_schedule.ics'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(ics_lines))

print(f"\n🎉 完了！カレンダーファイル '{output_file}' を保存しました。")
