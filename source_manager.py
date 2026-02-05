import requests, re, json, base64, subprocess, os

# FFmpeg দিয়ে ভিডিও সচল কি না তা গভীরভবে চেক করার ফাংশন
def is_video_playing(url):
    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        command = [
            'ffmpeg', '-t', '3', 
            '-user_agent', user_agent,
            '-headers', f'Referer: https://google.com/\r\n',
            '-i', url, 
            '-f', 'null', '-'
        ]
        # ২০ সেকেন্ড সময় দেওয়া হয়েছে যাতে ধীরগতির লিংকগুলোও ধরা পড়ে
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return result.returncode == 0
    except: return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

# এখানে আপনার অন্যান্য অনলাইন সোর্স লিংক দিতে পারেন
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u"
]

raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}

# ১. প্রাইভেট রিপোজিটরি থেকে ডাটা সংগ্রহ
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                raw_content += content + "\n"
except: print("Private repo access error.")

# ২. অনলাইন সোর্স থেকে ডাটা সংগ্রহ
for s_url in SOURCES:
    try: raw_content += requests.get(s_url, timeout=15).text + "\n"
    except: pass

db = {}
# আপনার iptv.txt ফাইলের group-title এবং কমা হ্যান্ডেল করার জন্য শক্তিশালী Regex 
# এটি লোগো, নাম এবং ঠিক নিচের লাইনের লিংকটি খুঁজে নেবে
matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)

for logo, name, link in matches:
    name, link = name.strip(), link.strip()
    if name not in db: db[name] = []
    
    # ডুপ্লিকেট লিংক ফিল্টার
    if not any(item['link'] == link for item in db[name]):
        print(f"Checking: {name}")
        # ভিডিও চেক করা হচ্ছে
        if is_video_playing(link):
            db[name].append({"link": link, "logo": logo})
            print(f"Done: {name} added.")
        else:
            # যদি FFmpeg ফেল করে, তবে বেসিক HTTP রিকোয়েস্ট দিয়ে একবার চেষ্টা করবে
            try:
                r = requests.head(link, timeout=10, allow_redirects=True)
                if r.status_code < 400:
                    db[name].append({"link": link, "logo": logo})
                    print(f"Added via backup check: {name}")
            except: print(f"Skipped: {name} (Dead Link)")

# ডাটাবেস আপডেট
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
