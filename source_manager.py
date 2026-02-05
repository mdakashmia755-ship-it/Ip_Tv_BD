import requests, re, json, base64, subprocess, os

# ভিডিও সচল কি না তা চেক করার উন্নত ফাংশন
def is_video_playing(url):
    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        command = [
            'ffmpeg', '-t', '5', 
            '-user_agent', user_agent,
            '-headers', f'Referer: https://google.com/\r\n',
            '-i', url, 
            '-f', 'null', '-'
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return result.returncode == 0
    except:
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            return r.status_code < 400
        except: return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

# পাবলিক গিটহাব সোর্স লিস্ট
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/Mohamed-Sami/iptv-list/main/channels.m3u",
    "https://raw.githubusercontent.com/Tiptopiptv/M3u/main/Sports.m3u"
]

raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}

# ১. আপনার নিজের প্রাইভেট ফাইল (iptv.txt) থেকে ডাটা সংগ্রহ 
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                raw_content += content + "\n"
                print(f"আপনার ফাইল '{file['name']}' থেকে ডাটা নেওয়া হয়েছে।")
except:
    print("আপনার প্রাইভেট রেপোতে অ্যাক্সেস পাওয়া যায়নি।")

# ২. অন্যান্য পাবলিক সোর্স থেকে ডাটা সংগ্রহ
for s_url in SOURCES:
    try:
        raw_content += requests.get(s_url, timeout=15).text + "\n"
        print(f"পাবলিক সোর্স থেকে ডাটা নেওয়া হয়েছে: {s_url}")
    except: pass

db = {}
# স্মার্ট রেজেক্স: group-title থাকলেও ডাটা খুঁজে পাবে 
matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)

for logo, name, link in matches:
    name = name.replace('\xa0', ' ').strip()
    link = link.strip()
    
    if name not in db: db[name] = []
    
    if not any(item['link'] == link for item in db[name]):
        print(f"চেক করা হচ্ছে: {name}")
        if is_video_playing(link):
            db[name].append({"link": link, "logo": logo})
            print(f"সফল: {name} ডাটাবেসে যুক্ত হয়েছে।")

# ডাটাবেস সেভ করা
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
