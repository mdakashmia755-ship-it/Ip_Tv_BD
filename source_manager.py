import requests, re, json, base64, os
from concurrent.futures import ThreadPoolExecutor

# ভিপিএন প্রক্সি সেটিংস
PROXIES = {
    "http": "socks5h://127.0.0.1:40000",
    "https": "socks5h://127.0.0.1:40000"
}

# ভিডিও লিংকটি সচল কি না তা পরীক্ষা করার ফাংশন
def is_video_live(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        # প্রক্সি ব্যবহার করে স্ট্রীম চেক করা হচ্ছে
        with requests.get(url, headers=headers, proxies=PROXIES, stream=True, timeout=10) as r:
            if r.status_code == 200:
                # ভিডিও ডাটা আসছে কি না নিশ্চিত করতে প্রথম ১ কিলোবাইট পড়া হচ্ছে
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: return True
                    break
        return False
    except:
        return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

# অনলাইন এম৩ইউ সোর্সগুলো
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/Mohamed-Sami/iptv-list/main/channels.m3u"
]

db = {}
headers_git = {"Authorization": f"token {TOKEN}"}

# ১. আপনার নিজস্ব ফাইল প্রসেস করা (সরাসরি যুক্ত হবে কোনো চেক ছাড়াই)
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers_git)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers_git).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', content, re.MULTILINE)
                for logo, name, link in matches:
                    name = name.strip()
                    if name not in db: db[name] = []
                    db[name].append({"link": link.strip(), "logo": logo})
                    print(f"ব্যক্তিগত ফাইল থেকে যুক্ত: {name}")
except: pass

# ২. অনলাইন সোর্স থেকে ডাটা সংগ্রহ
all_online = []
for s_url in SOURCES:
    try:
        data = requests.get(s_url, timeout=15).text
        all_online.extend(re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', data, re.MULTILINE))
    except: pass

# ৩. দ্রুত যাচাইকরণ (৩০টি চ্যানেল একসাথে চেক হবে)
def verify_links(matches_list):
    print(f"মোট {len(matches_list)}টি অনলাইন লিংক চেক করা হচ্ছে...")
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(lambda m: (m[0], m[1], m[2], is_video_live(m[2])), matches_list))
    
    for logo, name, link, is_live in results:
        name = name.strip()
        if is_live:
            if name not in db:
                db[name] = []
            # ডুপ্লিকেট লিংক চেক
            if not any(x['link'] == link for x in db[name]):
                db[name].append({"link": link.strip(), "logo": logo})
                print(f"সচল পাওয়া গেছে: {name}")

verify_links(all_online)

# ডাটাবেস সেভ করা
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)

print(f"সব কাজ শেষ! মোট চ্যানেল সংখ্যা: {len(db)}")
