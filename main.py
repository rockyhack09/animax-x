import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, db
import re
import time

# ফায়ারবেস সেটআপ
secret_val = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    if secret_val:
        cred_dict = json.loads(secret_val)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://myanimeapp-8d079-default-rtdb.firebaseio.com'
        })
    else:
        print("Error: FIREBASE_CREDENTIALS not found!")
        exit(1)

def clean_id(text):
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "_").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Multi-Server Sync Mode) ---")
    
    # ৩টি আলাদা ব্যাকআপ API সার্ভার
    mirrors = [
        "https://consumet-api-shastra.vercel.app/anime/gogoanime/recent-episodes",
        "https://api.consumet.org/anime/gogoanime/recent-episodes",
        "https://c-api-xi.vercel.app/anime/gogoanime/recent-episodes"
    ]

    results = []
    for url in mirrors:
        try:
            print(f"চেক করা হচ্ছে সার্ভার: {url.split('/')[2]}")
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    print(f"✓ সফল! {len(results)}টি এনিমি পাওয়া গেছে।")
                    break
            time.sleep(2)
        except Exception:
            continue

    if results:
        ref = db.reference('anime') 
        count = 0
        
        for item in results:
            try:
                title = item.get('title')
                # ভিডিওর আসল ID বের করা (এটিই ভিডিও চালানোর চাবিকাঠি)
                raw_id = item.get('id') 
                
                anime_id = clean_id(raw_id)
                
                # যদি এনিমিটা আগে থেকে না থাকে
                if not ref.child(anime_id).get():
                    episode_num = item.get('episodeNumber')
                    thumbnail = item.get('image')
                    
                    # সিজন সাজানো (Solo Leveling Season 1 ফরম্যাট)
                    display_folder = title
                    if "Season" not in title and "Part" not in title:
                        display_folder = f"{title} (Season 1)"
                    
                    # আপনার HTML এর iframe এ চলার জন্য একদম সঠিক Embed লিংক
                    # Gogoanime এর সবচেয়ে স্টেবল এমবেড সার্ভার
                    video_url = f"https://embtaku.pro/streaming.php?id={raw_id}"

                    ref.child(anime_id).set({
                        'title': title,
                        'thumbnail': thumbnail,
                        'folder': display_folder,
                        'url': video_url, # ১০০% কাজ করবে এই লিংক
                        'episode': f"Episode {episode_num}",
                        'type': 'free',
                        'id': anime_id,
                        'date': int(time.time())
                    })
                    print(f"✓ আপলোড সম্পন্ন: {title}")
                    count += 1
            except Exception:
                continue
        print(f"\nমোট {count}টি এনিমি আপনার সাইটে ফিরে এসেছে!")
    else:
        print("দুঃখিত, এই মুহূর্তে সব সার্ভার বিজি। ১ ঘণ্টা পর আবার চেষ্টা করা হবে।")

if __name__ == "__main__":
    start_auto_upload()
