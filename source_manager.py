import requests, re, json, base64, subprocess, os

# ভিডিও সচল কি না তা FFmpeg দিয়ে চেক করার ফাংশন
def is_video_playing(url):
    try:
        # -t 2 মানে ২ সেকেন্ড ডাটা চেক করবে
        command = ['ffmpeg', '-t', '2', '-i', url, '-f', 'null', '-']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        return result.returncode == 0
    except: return False

# কনফিগারেশন
TOKEN = os.getenv("MY_PAT_TOKEN") # YAML থেকে টোকেন রিসিভ করছে
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt"
SOURCES = ["https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u"]

# ডাটা সংগ্রহ
raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}
res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
if res.status_code == 200:
    for file in res.json():
        if file['name'].endswith('.txt'):
            f_res = requests.get(file['url'], headers=headers).json()
            raw_content += base64.b64decode(f_res['content']).decode('utf-8') + "\n"

try:
    with open('database.json', 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {}

# নতুন লিংক প্রসেস ও ভিডিও চেক
chunks = re.findall(r'tvg-logo="(.*?)",(.*?)\n(http.*?)$', raw_content, re.MULTILINE)
for logo, name, link in chunks:
    name, link = name.strip(), link.strip()
    if name not in db: db[name] = []
    if not any(item['link'] == link for item in db[name]):
        if is_video_playing(link): # সোর্সেই ভিডিও চেক হচ্ছে
            db[name].append({"link": link, "logo": logo})

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
