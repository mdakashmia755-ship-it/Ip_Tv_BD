import requests, re, json, base64, os
from concurrent.futures import ThreadPoolExecutor

# লিংক সচল কি না তা চেক করার সবচাইতে দ্রুত উপায়
def is_link_active(url):
    try:
        # ব্রাউজারের মতো রিকোয়েস্ট পাঠানো
        headers = {"User-Agent": "Mozilla/5.0"}
        # মাত্র ৫ সেকেন্ড সময় দেওয়া হয়েছে, এর বেশি লাগলে বট পরের লিংকে চলে যাবে
        r = requests.get(url, headers=headers, stream=True, timeout=5)
        
        # যদি সার্ভার ২০০ ওকে দেয়, তবে ধরে নেওয়া হবে এটি সচল
        if r.status_code == 200:
            return True
        return False
    except:
        return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt"

# সোর্স লিস্ট (এখানে আমি সরাসরি লিংকগুলো দিচ্ছি যাতে ভুল না হয়)
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/Mohamed-Sami/iptv-list/main/channels.m3u"
]

db = {}
raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}

# ১. আপনার নিজের ফাইল পড়া
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                raw_content += base64.b64decode(f_res['content']).decode('utf-8') + "\n"
except: pass

# ২. অনলাইন সোর্স পড়া
for s_url in SOURCES:
    try:
        r = requests.get(s_url, timeout=10)
        if r.status_code == 200:
            raw_content += r.text + "\n"
    except: pass

# রেজেক্স দিয়ে ডাটা ফিল্টার (সঠিক ফরম্যাট নিশ্চিত করা)
matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)

# ৩. দ্রুত চেক করার জন্য মাল্টি-থ্রেডিং (একসাথে ৩০টি লিংক চেক হবে)
def start_checking(all_matches):
    valid_db = {}
    # worker বাড়িয়ে ৩০ করা হয়েছে যাতে ১ মিনিটে ৫০০ লিংক চেক হয়
    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_data = {executor.submit(is_link_active, m[2]): m for m in all_matches}
        
        for future in future_to_data:
            logo, name, link = future_to_data[future]
            try:
                if future.result(): # যদি সচল হয়
                    clean_name = name.strip()
                    if clean_name not in valid_db:
                        valid_db[clean_name] = []
                    valid_db[clean_name].append({"link": link.strip(), "logo": logo})
                    print(f"✅ সচল: {clean_name}")
                else:
                    print(f"❌ অচল: {name}")
            except: pass
    return valid_db

# ডাটাবেস আপডেট
final_data = start_checking(matches)
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print(f"মোট {len(final_data)}টি সচল চ্যানেল পাওয়া গেছে।")
