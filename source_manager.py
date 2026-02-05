import requests, re, json, base64, subprocess, os

def is_video_playing(url):
    try:
        # ১৫ সেকেন্ড সময় যাতে ধীরগতির সার্ভারও চেক হতে পারে
        command = ['ffmpeg', '-t', '2', '-i', url, '-f', 'null', '-']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        return result.returncode == 0
    except: return False

TOKEN = os.getenv("MY_PAT_TOKEN")
REPO_OWNER = "mdakashmia755-ship-it"
PRIVATE_REPO = "cheekiptvtxt" 

raw_content = ""
headers = {"Authorization": f"token {TOKEN}"}

# আপনার প্রাইভেট রিপোজিটরি থেকে ডাটা পড়া
try:
    res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{PRIVATE_REPO}/contents/", headers=headers)
    if res.status_code == 200:
        for file in res.json():
            if file['name'].endswith('.txt'):
                f_res = requests.get(file['url'], headers=headers).json()
                content = base64.b64decode(f_res['content']).decode('utf-8')
                raw_content += content + "\n"
except Exception as e:
    print(f"Error: {e}")

db = {}

# এটি হলো "Smart Regex" যা tvg-logo এবং কমার পরের নামকে যেকোনো টেক্সটের ভেতর থেকে খুঁজে নেবে
# এটি group-title বা অন্য কিছু থাকলেও কাজ করবে 
matches = re.findall(r'tvg-logo="([^"]+)".*?,\s*(.*?)\s*\n(http[^\s]+)', raw_content, re.MULTILINE)

for logo, name, link in matches:
    name, link = name.strip(), link.strip()
    if name not in db: db[name] = []
    
    # ডুপ্লিকেট লিংক এড়াতে চেক
    if not any(item['link'] == link for item in db[name]):
        print(f"যাচাই করা হচ্ছে: {name}")
        if is_video_playing(link):
            db[name].append({"link": link, "logo": logo})
            print(f"সফল: {name} সচল আছে।")
        else:
            print(f"ব্যর্থ: {name} কাজ করছে না।")

# ডাটাবেস আপডেট করা
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
