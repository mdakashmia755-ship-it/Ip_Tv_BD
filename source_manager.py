import requests, re, json, base64, os
from concurrent.futures import ThreadPoolExecutor

def is_video_active(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        # VPN কানেক্টেড থাকলে এটি এখন বিডি বা এশিয়ান আইপি দিয়ে চেক করবে
        r = requests.get(url, headers=headers, stream=True, timeout=7)
        return r.status_code == 200
    except:
        return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/Mohamed-Sami/iptv-list/main/channels.m3u"
]

db = {}
headers = {"Authorization": f"token {TOKEN}"}

# ১. আপনার নিজের ফাইল সরাসরি সেভ (Priority)
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                raw_content = base64.b64decode(f_res['content']).decode('utf-8')
                matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)
                for logo, name, link in matches:
                    name = name.strip()
                    if name not in db: db[name] = []
                    db[name].append({"link": link.strip(), "logo": logo})
except: pass

# ২. অনলাইন সোর্স চেকিং
all_online = []
for s_url in SOURCES:
    try:
        data = requests.get(s_url, timeout=10).text
        all_online.extend(re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', data, re.MULTILINE))
    except: pass

def verify_and_add(matches_list):
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(lambda m: (m[0], m[1], m[2], is_video_active(m[2])), matches_list))
    for logo, name, link, is_live in results:
        if is_live and name.strip() not in db:
            db[name.strip()] = [{"link": link.strip(), "logo": logo}]

verify_and_add(all_online)
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
