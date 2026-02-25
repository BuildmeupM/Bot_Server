import re

def parse_thai_address(address_str):
    if not address_str or not isinstance(address_str, str):
        return {}
    
    address_str = address_str.strip()
    result = {
        'building': '', 'room_number': '', 'floor': '', 'village': '', 
        'house_number': '', 'moo': '', 'soi': '', 'intersection': '', 
        'road': '', 'province': '', 'district': '', 'subdistrict': '', 'postal_code': ''
    }
    
    # หารหัสไปรษณีย์
    postal_match = re.search(r'\b(\d{5})\b', address_str)
    if postal_match:
        result['postal_code'] = postal_match.group(1)
        address_str = address_str.replace(postal_match.group(0), '').strip()
    
    # หาจังหวัด
    province_patterns = [r'จ\.\s*([^\s]+)', r'จังหวัด\s*([^\s]+)', r'กรุงเทพมหานคร', r'กรุงเทพ']
    for pattern in province_patterns:
        match = re.search(pattern, address_str)
        if match:
            if 'กรุงเทพ' in pattern:
                result['province'] = 'กรุงเทพมหานคร'
            else:
                result['province'] = match.group(1) if match.lastindex else match.group(0)
            address_str = re.sub(pattern, '', address_str).strip()
            break
            
    # หาอำเภอ/เขต
    for pattern in [r'อ\.\s*([^\s]+)', r'เขต\s*([^\s]+)', r'อำเภอ\s*([^\s]+)']:
        match = re.search(pattern, address_str)
        if match:
            result['district'] = match.group(1) if match.lastindex else match.group(0).replace('อ.', '').replace('เขต', '').replace('อำเภอ', '').strip()
            address_str = re.sub(pattern, '', address_str).strip()
            break
            
    # หาตำบล/แขวง
    for pattern in [r'ต\.\s*([^\s]+)', r'แขวง\s*([^\s]+)', r'ตำบล\s*([^\s]+)']:
        match = re.search(pattern, address_str)
        if match:
            result['subdistrict'] = match.group(1) if match.lastindex else match.group(0).replace('ต.', '').replace('แขวง', '').replace('ตำบล', '').strip()
            address_str = re.sub(pattern, '', address_str).strip()
            break
            
    # หาหมู่ที่
    match = re.search(r'หมู่ที่\s*(\d+)', address_str)
    if match:
        result['moo'] = match.group(1)
        address_str = re.sub(r'หมู่ที่\s*\d+', '', address_str).strip()
        
    # หาหมู่บ้าน
    match = re.search(r'หมู่บ้าน\s*([^\s]+)', address_str)
    if match:
        result['village'] = match.group(1)
        address_str = re.sub(r'หมู่บ้าน\s*[^\s]+', '', address_str).strip()
        
    # หาซอย
    for pattern in [r'ซ\.\s*([^\s]+(?:\s+\d+)?)', r'ซอย\s*([^\s]+(?:\s+\d+)?)']:
        match = re.search(pattern, address_str)
        if match:
            result['soi'] = match.group(1).strip()
            address_str = re.sub(pattern, '', address_str).strip()
            break
            
    # หาแยก
    match = re.search(r'แยก\s*([^\s]+)', address_str)
    if match:
        result['intersection'] = match.group(1)
        address_str = re.sub(r'แยก\s*[^\s]+', '', address_str).strip()
        
    # หาถนน
    for pattern in [r'ถ\.\s*([^\s]+)', r'ถนน\s*([^\s]+)']:
        match = re.search(pattern, address_str)
        if match:
            result['road'] = match.group(1).strip()
            address_str = re.sub(pattern, '', address_str).strip()
            break
            
    print(f"DEBUG After stripping others, address_str is: '{address_str}'")
    
    # หาเลขที่ (มักอยู่ต้นสุด)
    house_match = re.match(r'^(\d+(?:/\d+)?)', address_str)
    if house_match:
        result['house_number'] = house_match.group(1)
        address_str = address_str[len(house_match.group(0)):].strip()
        
    # หาอาคาร (ถ้ามี)
    match = re.search(r'อาคาร\s*([^\s]+)', address_str)
    if match:
        result['building'] = match.group(1)
        address_str = re.sub(r'อาคาร\s*[^\s]+', '', address_str).strip()
        
    # หาห้องเลขที่
    match = re.search(r'ห้อง\s*(\d+)', address_str)
    if match:
        result['room_number'] = match.group(1)
        address_str = re.sub(r'ห้อง\s*\d+', '', address_str).strip()
        
    # หาชั้นที่
    match = re.search(r'ชั้น\s*(\d+)', address_str)
    if match:
        result['floor'] = match.group(1)
        address_str = re.sub(r'ชั้น\s*\d+', '', address_str).strip()
        
    return result

test_addr = "120/734 ชั้นที่ 2-3 ซอยวชิรธรรมสาธิต 12 แขวงบางนาเหนือ เขตบางนา กรุงเทพมหานคร 10260"
print(parse_thai_address(test_addr))
