import requests
import json
from datetime import datetime, timedelta
import re

# 📅 今月と来月の年月を自動計算する
now = datetime.now()
current_ym = now.strftime("%Y%m")

# 12月の場合は、来年は「翌年の1月」にする
if now.month == 12:
    next_ym = f"{now.year + 1}01"
else:
    next_ym = f"{now.year}{now.month + 1:02d}"

# 取得する月のリスト（今月と来月）
target_months = [current_ym, next_ym]

# 🎯 推しメンのID（池田瑛紗さんは 55397）
TARGET_MEMBER_ID = "55397"
url = 'https://www.nogizaka46.com/s/n46/api/list/schedule'
headers = {'User-Agent': 'Mozilla/5.0'}

# 取得した全スケジュールを貯める箱
all_schedule_list = []

# 今月と来月の2回、通信を繰り返す
for ym in target_months:
    print(f"{ym[:4]}年{ym[4:]}月のスケジュールを取得中...")
    params = {'ima': '4923', 'dy': ym, 'callback': 'res'}
    response = requests.get(url, headers=headers, params=params)
    response.encoding = 'utf-8'

    json_text = response.text.strip()
    if json_text.startswith('res('): json_text = json_text[4:]
    if json_text.endswith(');'): json_text = json_text[:-2]
    elif json_text.endswith(')'): json_text = json_text[:-1]

    data = json.loads(json_text)
    # 取得した月のスケジュールを箱に追加
    all_schedule_list.extend(data.get('data', []))

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

# 2ヶ月分のスケジュールをまとめてフィルターにかける！
for item in all_schedule_list:
    arti_code = item.get('arti_code', [])
    
    # 🛡️【究極のフィルター】
    if not arti_code or TARGET_MEMBER_ID in str(arti_code):
        pass
    else:
        continue

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

print(f"\n🎉 完了！今月と来月のカレンダーファイル '{output_file}' を保存しました。")


