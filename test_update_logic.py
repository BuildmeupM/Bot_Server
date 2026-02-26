import json
from pathlib import Path

# mock data
id_card = "0991026600041"
attachments = [
    {
        "recipient_id_card": "0991026600041",
        "recipient_name": "Mr. Saw Kyaw Khi Phaung",
        "payment_month": 1,
        "payment_year": 2025
    }
]
social_security = []
monthly_map = {
    "2025-01": {
        "income": 15500.0,
        "tax": 0.0,
        "contribution": 750.0,
        "income_type": "40(1)"
    }
}
company = "LTFชั่วคราว"
from datetime import datetime

found_ss_keys = set()
updated_social_security = 0

for ss in social_security:
    ss_id_card = str(ss.get('recipient_id_card', '')).strip().replace(' ', '').replace('-', '')
    if ss_id_card != id_card:
        continue
    month = ss.get('payment_month')
    year = ss.get('payment_year')
    if month is None or year is None:
        continue
    key = f"{year}-{str(month).zfill(2)}"
    if key in monthly_map:
        contribution = monthly_map[key].get('contribution', 0)
        ss['social_security_contribution'] = f"{contribution:.2f}"
        updated_social_security += 1
        found_ss_keys.add(key)

print(f"found_ss_keys: {found_ss_keys}")

recipient_name = id_card
for att in attachments:
    att_id_card = str(att.get('recipient_id_card', '')).strip().replace(' ', '').replace('-', '')
    if att_id_card == id_card and att.get('recipient_name'):
        recipient_name = att.get('recipient_name')
        break

for key, md in monthly_map.items():
    if key not in found_ss_keys:
        contribution = md.get('contribution', 0)
        print(f"Processing key {key}, contribution: {contribution}")
        if contribution > 0:
            year_str, month_str = key.split('-')
            new_ss = {
                "recipient_id_card": id_card,
                "recipient_name": recipient_name,
                "payment_month": int(month_str),
                "payment_year": int(year_str),
                "salary": f"{md.get('income', 0):.2f}",
                "social_security_contribution": f"{contribution:.2f}",
                "company": company,
                "file_name": f"เพิ่มเติมจากระบบ_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "created_at": datetime.now().isoformat()
            }
            social_security.append(new_ss)
            updated_social_security += 1

print(f"Updated: {updated_social_security}")
print(json.dumps(social_security, indent=2))
