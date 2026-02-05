import requests, re, json, base64, os
from concurrent.futures import ThreadPoolExecutor

# ভিডিও সোর্সকে ধোঁকা দেওয়ার জন্য হেডার্স (Spoofing)
def is_video_active(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
            "Referer": "https://www.toffee.com/", # বাংলাদেশি স্ট্রিমিং সাইটের মতো অভিনয় করবে
            "Accept-Language": "bn-BD,bn;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        # মাত্র ৬ সেকেন্ড সময় দেওয়া হয়েছে
        with requests.get(url, headers=headers, stream=True, timeout=6) as r:
            if r.status_code == 200:
                # ভিডিও ডাটার ছোট একটি টুকরো পড়ার চেষ্টা
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: return True
                    break
        return False
    except:
        return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

SOURCES = ["https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u"]

db = {}
headers = {"Authorization": f"token {TOKEN}"}

# ১. আপনার নিজের ফাইলটি কোনো চেক ছাড়াই সরাসরি সেভ হবে (Priority 1)
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', content, re.MULTILINE)
                for logo, name, link in matches:
                    name = name.strip()
                    if name not in db: db[name] = []
                    db[name].append({"link": link.strip(), "logo": logo})
                    print(f"আপনার ফাইল থেকে যুক্ত হয়েছে: {name}")
except: pass

# ২. অনলাইন সোর্স ফিল্টারিং (দ্রুত চেকিং)
all_online = []
for s_url in SOURCES:
    try:
        data = requests.get(s_url, timeout=10).text
        all_online.extend(re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', data, re.MULTILINE))
    except: pass

def fast_verify(matches_list):
    with ThreadPoolExecutor(max_workers=25) as executor:
        results = list(executor.map(lambda m: (m[0], m[1], m[2], is_video_active(m[2])), matches_list))
    
    for logo, name, link, is_live in results:
        name = name.strip()
        if is_live and name not in db:
            db[name] = [{"link": link.strip(), "logo": logo}]
            print(f"অনলাইন সোর্স সচল: {name}")
    return db

fast_verify(all_online)

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
