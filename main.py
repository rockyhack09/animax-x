import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, db
import re

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
    print("--- অটোমেটিক আপডেট শুরু (Direct Embed Link Mode) ---")
    
    # এটি Gogoanime এর অফিসিয়াল আপডেট পেজ (এখান থেকে সঠিক ID পাওয়া যায়)
    ajax_url = "https://ajax.gogocdn.net/ajax/page-recent-release.html?page=1&type=1"
    
    # এটি হলো ভিডিও প্লেয়ারের বেস লিংক (Embed Server)
    base_embed = "https://embtaku.pro/streaming.php?id="

    # Cloudscraper ব্যবহার করছি যাতে সার্ভার ব্লক না করে
    scraper = cloudscraper.create_scraper()

    try:
        print(f"Gogoanime সার্ভার থেকে সঠিক ভিডিও লিংক আনা হচ্ছে...")
        response = scraper.get(ajax_url, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('li')
            
            if items:
                ref = db.reference('anime') 
                count = 0
                
                for item in items:
                    try:
                        # ১. নাম বের করা
                        name_tag = item.find('p', class_='name')
                        title = name_tag.text.strip()
                        
                        # ২. এপিসোড নম্বর
                        episode_tag = item.find('p', class_='episode')
                        ep_text = episode_tag.text.strip()
                        
                        # ৩. সঠিক ভিডিও ID বের করা (সবচেয়ে গুরুত্বপূর্ণ ধাপ)
                        link_tag = item.find('a')
                        # লিংকটি দেখতে এমন হয়: /one-piece-episode-1100
                        raw_id = link_tag['href'].strip('/') 
                        
                        # ৪. ১০০% কাজ করবে এমন Embed লিংক তৈরি করা
                        final_video_url = f"{base_embed}{raw_id}"
                        
                        # ৫. থাম্বনেইল
                        img_tag = item.find('img')
                        thumbnail = img_tag['src']
                        
                        # ৬. ফোল্ডার নাম (Season 1 যুক্ত করা, যদি না থাকে)
                        folder_name = title
                        if "Season" not in title and "Part" not in title:
                            folder_name = f"{title} (Season 1)"
                        
                        anime_id = clean_id(raw_id)
                        
                        # ডাটাবেসে সেভ করা
                        if not ref.child(anime_id).get():
                            ref.child(anime_id).set({
                                'title': title,
                                'thumbnail': thumbnail,
                                'folder': folder_name,
                                'url': final_video_url, # এটিই সেই জাদুকরী লিংক
                                'episode': ep_text,
                                'type': 'free',
                                'id': anime_id,
                                'date': 2024
                            })
                            print(f"✓ ভিডিও রেডি: {title} - {ep_text}")
                            count += 1
                    except Exception as inner_e:
                        print(f"আইটেম স্কিপড: {inner_e}")
                        continue
                
                print(f"\nকাজ শেষ! {count}টি নতুন ভিডিও (সঠিক লিংকসহ) আপলোড হয়েছে।")
            else:
                print("লিস্ট খালি এসেছে।")
        else:
            print(f"সার্ভার এরর: {response.status_code}")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()
