import requests, re, json, base64, subprocess

# ভিডিও সচল কি না তা FFmpeg দিয়ে চেক করার ফাংশন
def is_video_playing(url):
    try:
        # -t 2 মানে ২ সেকেন্ড ডাটা চেক করবে। ভিডিও না চললে এটি Error দেবে।
        command = ['ffmpeg', '-t', '2', '-i', url, '-f', 'null', '-']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        return result.returncode == 0
    except: return False

# কনফিগারেশন
TOKEN = "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" # এখানে আপনার টোকেন বসাবেন
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt"
SOURCES = ["https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u"]

# ডাটা সংগ্রহ করা শুরু
raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}
res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
if res.status_code == 200:
    for file in res.json():
        if file['name'].endswith('.txt'):
            f_res = requests.get(file['url'], headers=headers).json()
            raw_content += base64.b64decode(f_res['content']).decode('utf-8') + "\n"

# বর্তমান ডাটাবেস লোড করা
try:
    with open('database.json', 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {}

# সোর্স থেকে নতুন লিংক প্রসেস করা
chunks = re.findall(r'tvg-logo="(.*?)",(.*?)\n(http.*?)$', raw_content, re.MULTILINE)
for logo, name, link in chunks:
    name, link = name.strip(), link.strip()
    if name not in db: db[name] = []
    
    # ডুপ্লিকেট লিংক চেক
    if not any(item['link'] == link for item in db[name]):
        if is_video_playing(link): # ভিডিও চললে তবেই স্টোরে ঢুকবে
            db[name].append({"link": link, "logo": logo})

# ডাটাবেস সেভ করা
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
