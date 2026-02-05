import requests, re, json, base64, subprocess, os

# ভিডিও সচল কি না তা FFmpeg দিয়ে চেক করার ফাংশন
def is_video_playing(url):
    try:
        # ব্রাউজারের পরিচয় ব্যবহার করা হয়েছে যাতে সার্ভার ব্লক না করে
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        command = [
            'ffmpeg', '-t', '3', 
            '-user_agent', user_agent,
            '-headers', f'Referer: https://google.com/\r\n',
            '-i', url, 
            '-f', 'null', '-'
        ]
        # ২০ সেকেন্ড সময় দেওয়া হয়েছে ধীরগতির লিংকের জন্য
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return result.returncode == 0
    except:
        # FFmpeg ফেল করলে সরাসরি HTTP কানেকশন চেক করবে
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            return r.status_code < 400
        except: return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

# এখানে কিছু জনপ্রিয় পাবলিক গিটহাব সোর্স যুক্ত করা হয়েছে
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/Mohamed-Sami/iptv-list/main/channels.m3u",
    "https://raw.githubusercontent.com/Tiptopiptv/M3u/main/Sports.m3u"
]

raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}

# ১. [cite_start]আপনার নিজস্ব প্রাইভেট রেপো থেকে ডাটা সংগ্রহ [cite: 1]
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                raw_content += content + "\n"
except: pass

# ২. অন্যান্য পাবলিক গিটহাব সোর্স থেকে ডাটা সংগ্রহ
for s_url in SOURCES:
    try:
        raw_content += requests.get(s_url, timeout=15).text + "\n"
    except: pass

db = {}
# [cite_start]স্মার্ট রেজেক্স: আপনার iptv.txt এবং অনলাইন সোর্স উভয়ই হ্যান্ডেল করবে [cite: 1]
matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)

for logo, name, link in matches:
    # [cite_start]অদৃশ্য স্পেস পরিষ্কার করা (যেমন আপনার ATN Bangla-তে ছিল) [cite: 1]
    name = name.replace('\xa0', ' ').strip()
    link = link.strip()
    
    if name not in db: db[name] = []
    
    if not any(item['link'] == link for item in db[name]):
        print(f"চেক করা হচ্ছে: {name}")
        if is_video_playing(link):
            db[name].append({"link": link, "logo": logo})
            print(f"সফল: {name} ডাটাবেসে যুক্ত হয়েছে।")

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
