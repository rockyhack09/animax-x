import os
import json
import requests
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
        print("Error: FIREBASE_CREDENTIALS not found in GitHub Secrets!")
        exit(1)

def clean_id(text):
    return re.sub(r'[.#$\[\]]', '', text).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক এনিমি আপডেট শুরু (API Mode) ---")
    
    # ৫টি আলাদা ফ্রি API সার্ভার (একটি নষ্ট হলে অন্যটি কাজ করবে)
    api_urls = [
        "https://consumet-api-clone.vercel.app/anime/gogoanime/recent-episodes",
        "https://api.consumet.org/anime/gogoanime/recent-episodes",
        "https://c-api-xi.vercel.app/anime/gogoanime/recent-episodes",
        "https://consumet-api-drab.vercel.app/anime/gogoanime/recent-episodes",
        "https://api-consumet.vercel.app/anime/gogoanime/recent-episodes"
    ]

    results = []
    
    # লুপ চালিয়ে একটি একটি করে সার্ভার চেক করা
    for api_url in api_urls:
        try:
            domain_name = api_url.split('/')[2]
            print(f"চেক করা হচ্ছে সার্ভার: {domain_name} ...")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(api_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    print("✓ সার্ভার কাজ করছে! ডেটা পাওয়া গেছে।\n")
                    break # ডেটা পেলে আর অন্য সার্ভার চেক করবে না
            else:
                print(f"✗ সার্ভার ডাউন (Error {response.status_code})। পরেরটিতে যাচ্ছি...")
        except Exception:
            print("✗ সার্ভার টাইমআউট। পরেরটিতে যাচ্ছি...")
            continue

    # যদি কোনো একটি সার্ভার থেকে ডেটা পাওয়া যায়
    if results:
        ref = db.reference('animes')
        count = 0
        
        for item in results:
            try:
                title = item.get('title')
                anime_id = clean_id(title)
                
                # ফায়ারবেসে আগে থেকে না থাকলে তবেই সেভ করবে
                if not ref.child(anime_id).get():
                    ep_num = item.get('episodeNumber')
                    img_url = item.get('image', 'No Image')
                    watch_link = item.get('url', '')

                    # লিংকের ফরম্যাট ঠিক করা
                    full_link = watch_link
                    if watch_link.startswith('/'):
                        full_link = f"https://anitaku.pe{watch_link}"

                    ref.child(anime_id).set({
                        'title': title,
                        'image': img_url,
                        'episode': f"Episode {ep_num}",
                        'link': full_link,
                        'type': 'Auto-Update'
                    })
                    print(f"✓ নতুন আপলোড: {title} (Ep: {ep_num})")
                    count += 1
            except Exception as e:
                continue
        
        print(f"\nকাজ শেষ! মোট {count}টি নতুন এনিমি ডাটাবেজে যুক্ত হয়েছে।")
    else:
        # যদি কোনো সার্ভারই কাজ না করে, তবুও কোড ক্র্যাশ করবে না
        print("\nদুঃখিত! বর্তমানে সমস্ত ফ্রি API সার্ভার ডাউন আছে। গিটহাব ১ ঘণ্টা পর আবার অটোমেটিক চেক করবে।")

if __name__ == "__main__":
    start_auto_upload()
