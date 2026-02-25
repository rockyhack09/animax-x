import os
import json
import firebase_admin
from firebase_admin import credentials, db
import re
import feedparser

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
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Unbreakable RSS Mode) ---")
    
    # এটি একটি নির্ভরযোগ্য RSS Feed যা নিয়মিত আপডেট হয়
    rss_url = "https://nyaa.si/?page=rss&c=1_2&f=0"
    
    try:
        print(f"RSS Feed থেকে ডেটা আনা হচ্ছে...")
        
        # ফিড পার্স করা হচ্ছে
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            print(f"✓ সফল! {len(feed.entries)} টি আইটেম পাওয়া গেছে।")
            
            ref = db.reference('animes')
            count = 0
            
            for entry in feed.entries:
                try:
                    full_title = entry.title
                    
                    # টাইটেল থেকে এনিমি নাম এবং এপিসোড নম্বর আলাদা করা
                    # উদাহরণ: [SubsPlease] Boku no Hero Academia S07 - 05 (1080p) [F214A5A0].mkv
                    match = re.search(r'\] (.*?) - (\d+)', full_title)
                    if not match:
                        continue
                        
                    title = match.group(1).strip()
                    episode_num = match.group(2).strip()
                    
                    anime_id = clean_id(f"{title}-episode-{episode_num}")
                    
                    # ফায়ারবেসে চেক করা
                    if not ref.child(anime_id).get():
                        watch_link = entry.link
                        
                        # RSS ফিডে ছবি থাকে না, তাই একটি ডিফল্ট ছবি ব্যবহার করছি
                        default_image = "https://i.ibb.co/6nB0Y58/placeholder.png"
                        
                        # ফায়ারবেসে আপলোড
                        ref.child(anime_id).set({
                            'title': title,
                            'image': default_image,
                            'episode': f"Episode {episode_num}",
                            'link': watch_link,
                            'type': 'RSS-Update'
                        })
                        print(f"✓ নতুন এনিমি যুক্ত হয়েছে: {title} - Episode {episode_num}")
                        count += 1
                except Exception as inner_e:
                    continue
            
            print(f"\nকাজ শেষ! মোট {count}টি নতুন এনিমি ডাটাবেজে আপডেট হয়েছে।")
        else:
            print("RSS Feed খালি পাওয়া গেছে বা লোড হয়নি।")
            
    except Exception as e:
        print(f"মারাত্মক সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()
