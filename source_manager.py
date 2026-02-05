import requests, re, json, base64, subprocess, os

def is_video_playing(url):
    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        command = [
            'ffmpeg', '-t', '3', 
            '-user_agent', user_agent,
            '-headers', f'Referer: https://google.com/\r\n',
            '-i', url, 
            '-f', 'null', '-'
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return result.returncode == 0
    except: return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

# এখানে আপনি যত খুশি অন্য সোর্স বা লিংক যোগ করতে পারেন
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "অন্য_লিংক_এখানে"
]

raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}

# ১. আপনার প্রাইভেট রিপোজিটরি থেকে ডাটা সংগ্রহ 
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                raw_content += content + "\n"
except: pass

# ২. অন্যান্য পাবলিক সোর্স থেকে ডাটা সংগ্রহ
for url in SOURCES:
    try:
        raw_content += requests.get(url, timeout=10).text + "\n"
    except: pass

db = {}
# স্মার্ট রেজেক্স: tvg-logo এবং নাম খুঁজে বের করবে 
matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)

for logo, name, link in matches:
    name, link = name.strip(), link.strip()
    if name not in db: db[name] = []
    
    if not any(item['link'] == link for item in db[name]):
        print(f"Checking {name} from sources...")
        if is_video_playing(link):
            db[name].append({"link": link, "logo": logo})
        else:
            # বেসিক চেক (যদি FFmpeg ফেল করে)
            try:
                r = requests.head(link, timeout=10, allow_redirects=True)
                if r.status_code < 400:
                    db[name].append({"link": link, "logo": logo})
            except: pass

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
