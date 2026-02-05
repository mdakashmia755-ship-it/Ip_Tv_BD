import requests, re, json, base64, os
from concurrent.futures import ThreadPoolExecutor

# VPN SOCKS5 Proxy Settings
PROXIES = {
    "http": "socks5h://127.0.0.1:40000",
    "https": "socks5h://127.0.0.1:40000"
}

def is_video_live(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        # VPN দিয়ে লিংক চেক করা হচ্ছে
        with requests.get(url, headers=headers, proxies=PROXIES, stream=True, timeout=10) as r:
            if r.status_code == 200:
                # ভিডিও ডাটা আসছে কি না নিশ্চিত করতে ছোট অংশ পড়া
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: return True
                    break
        return False
    except:
        return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

# অনলাইন সোর্স লিস্ট (সঠিক M3U লিংক)
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/Mohamed-Sami/iptv-list/main/channels.m3u"
]

db = {}
all_links_to_check = []
headers_git = {"Authorization": f"token {TOKEN}"}

# ১. আপনার নিজের ফাইল থেকে লিংক সংগ্রহ
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers_git)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers_git).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', content, re.MULTILINE)
                for logo, name, link in matches:
                    all_links_to_check.append((logo, name.strip(), link.strip()))
except: pass

# ২. অনলাইন সোর্স থেকে লিংক সংগ্রহ
for s_url in SOURCES:
    try:
        data = requests.get(s_url, timeout=15).text
        matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', data, re.MULTILINE)
        for logo, name, link in matches:
            all_links_to_check.append((logo, name.strip(), link.strip()))
    except: pass

# ৩. ভেরিফিকেশন ফাংশন (সব এক সাথে চেক হবে)
def verify_and_build_db(links_list):
    print(f"মোট {len(links_list)}টি চ্যানেল চেক করা হচ্ছে... দয়া করে অপেক্ষা করুন।")
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(lambda x: (x[0], x[1], x[2], is_video_live(x[2])), links_list))
    
    for logo, name, link, is_live in results:
        if is_live:
            if name not in db:
                db[name] = []
            # ডুপ্লিকেট লিংক এড়াতে
            if not any(item['link'] == link for item in db[name]):
                db[name].append({"link": link, "logo": logo})
                print(f"✅ সচল: {name}")
        else:
            # আপনি চাইলে অচলগুলো লগে দেখতে পারেন (ঐচ্ছিক)
            pass

# চেকিং শুরু
verify_and_build_db(all_links_to_check)

# ডাটাবেস সেভ
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)

print(f"সব কাজ শেষ! মোট সচল চ্যানেল সংখ্যা: {len(db)}")
