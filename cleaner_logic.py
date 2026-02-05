import subprocess, json

def is_video_playing(url):
    try:
        command = ['ffmpeg', '-t', '2', '-i', url, '-f', 'null', '-']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        return result.returncode == 0
    except: return False

try:
    with open('database.json', 'r', encoding='utf-8') as f: db = json.load(f)
except: exit()

new_db, m3u = {}, "#EXTM3U\n"

for name, links in db.items():
    active_links = []
    for item in links:
        if is_video_playing(item['link']): # ভিডিও চেক
            active_links.append(item)
            if len(active_links) == 1:
                m3u += f'#EXTINF:-1 tvg-logo="{item["logo"]}",{name}\n{item["link"]}\n'
    if active_links: new_db[name] = active_links

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(new_db, f, indent=4, ensure_ascii=False)
with open('playlist.m3u', 'w', encoding='utf-8') as f:
    f.write(m3u)
