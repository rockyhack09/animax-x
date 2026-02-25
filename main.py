import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, db
import re

# গিটহাবের সিক্রেট বক্স থেকে চাবি বের করা হচ্ছে
secret_val = os.environ.get("FIREBASE_CREDENTIALS")

# ফায়ারবেস কানেকশন
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
    return re.sub(r'[.#$\[\]]', '', text).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক এনিমি আপডেট শুরু (GitHub Actions) ---")
    
    # ব্যাকআপ সহ একাধিক API সার্ভারের লিস্ট
    api_urls = [
        "https://api-consumet.vercel.app/anime/gogoanime/recent-episodes",
        "https://api.consumet.org/anime/gogoanime/recent-episodes",
        "https://consumet-api-clone.vercel.app/anime/gogoanime/recent-episodes"
    ]

    data = None
    
    # সার্ভার চেক করা
    for api_url in api_urls:
        try:
            print(f"চেক করা হচ্ছে: {api_url} ...")
            response = requests.get(api_url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                print("✓ ডেটা পাওয়া গেছে।")
                break
        except Exception:
            continue

    if data and 'results' in data:
        results = data.get('results', [])
        ref = db.reference('animes')
        count = 0
        
        for item in results:
            try:
                title = item.get('title')
                anime_id = clean_id(title)
                
                # ডাটাবেসে না থাকলে নতুন এনিমি সেভ করা
                if not ref.child(anime_id).get():
                    episode_num = item.get('episodeNumber')
                    img_url = item.get('image')
                    watch_link = item.get('url')
                    
                    # লিংকের আগে ডোমেইন ঠিক করা
                    full_link = watch_link
                    if watch_link.startswith('/'):
                        full_link = f"https://anitaku.pe{watch_link}"

                    ref.child(anime_id).set({
                        'title': title,
                        'image': img_url,
                        'episode': f"Episode {episode_num}",
                        'link': full_link,
                        'type': 'Auto-Update'
                    })
                    print(f"নতুন আপলোড: {title}")
                    count += 1
            except Exception:
                continue
        print(f"কাজ শেষ! মোট {count}টি নতুন এনিমি যুক্ত হয়েছে।")
    else:
        print("কোনো সার্ভার থেকেই ডেটা পাওয়া যায়নি বা কোনো নতুন আপডেট নেই।")

if __name__ == "__main__":
    start_auto_upload()
