import os
import json
import requests
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
    return re.sub(r'[.#$\[\]]', '', text).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Direct AJAX Mode) ---")
    
    # GogoAnime এর গোপন সোর্স লিংক (এটি তাদের ইন্টারনাল API)
    # এটি সাধারণত ব্লক থাকে না এবং খুব ফাস্ট কাজ করে
    ajax_url = "https://ajax.gogo-load.com/ajax/page-recent-release.html?page=1&type=1"
    base_url = "https://anitaku.pe" # ভিডিও লিংকের জন্য ডোমেইন

    try:
        print(f"সরাসরি সোর্স থেকে ডেটা আনা হচ্ছে: {ajax_url} ...")
        
        # মানুষের মতো ব্রাউজার সেজে রিকোয়েস্ট পাঠানো
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(ajax_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            anime_list = soup.find_all('li')
            
            if anime_list:
                print(f"✓ সফল! {len(anime_list)} টি আইটেম পাওয়া গেছে।")
                
                ref = db.reference('animes')
                count = 0
                
                for item in anime_list:
                    try:
                        # নাম বের করা
                        name_tag = item.find('p', class_='name')
                        title = name_tag.find('a').text.strip() if name_tag else "Unknown"
                        
                        anime_id = clean_id(title)
                        
                        # ডাটাবেসে চেক করা (আগেই আছে কি না)
                        if not ref.child(anime_id).get():
                            # এপিসোড নম্বর
                            ep_tag = item.find('p', class_='episode')
                            episode = ep_tag.text.strip() if ep_tag else "New Episode"
                            
                            # ছবি বের করা
                            img_tag = item.find('img')
                            img_url = img_tag['src'] if img_tag else ""
                            
                            # ভিডিও লিংক বের করা
                            link_tag = item.find('a')
                            partial_link = link_tag['href'] if link_tag else ""
                            full_link = f"{base_url}{partial_link}"
                            
                            # ফায়ারবেসে আপলোড
                            ref.child(anime_id).set({
                                'title': title,
                                'image': img_url,
                                'episode': episode,
                                'link': full_link,
                                'type': 'Auto-Update'
                            })
                            print(f"✓ নতুন এনিমি যুক্ত হয়েছে: {title}")
                            count += 1
                    except Exception as inner_e:
                        print(f"আইটেম এরর: {inner_e}")
                        continue
                
                print(f"\nমোট {count}টি নতুন এনিমি ডাটাবেজে আপডেট হয়েছে।")
            else:
                print("ডেটা পাওয়া গেছে কিন্তু কোনো লিস্ট নেই (Empty List)।")
        else:
            print(f"সার্ভার এরর! Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"মারাত্মক সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()
