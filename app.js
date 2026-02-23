// --- FIREBASE CONFIG ---
const firebaseConfig = {
    apiKey: "AIzaSyBcWE5TCxamMSnJxqSm5X4mgSwSccIXcBI",
    authDomain: "myanimeapp-8d079.firebaseapp.com",
    databaseURL: "https://myanimeapp-8d079-default-rtdb.firebaseio.com",
    projectId: "myanimeapp-8d079",
    storageBucket: "myanimeapp-8d079.firebasestorage.app",
    messagingSenderId: "37482342893",
    appId: "1:37482342893:web:bebc7352e4bc102b725fe4"
};
if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
const auth = firebase.auth(), db = firebase.database();

let currentUser = null, isPremium = false, currentVideoId = null;
let adsLoaded = false, isMovieContent = false;
let currentLikesCountRef = null, currentUserLikeRef = null;

// --- ADVANCED PLAYER INITIALIZATION ---
const player = new Plyr('#main-video', {
    controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'settings', 'fullscreen'],
    settings: ['quality', 'speed'],
    speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }
});
let hlsInstance = null; // To manage HLS streaming

// --- AUTH SYSTEM ---
auth.onAuthStateChanged(user => {
    if (user) {
        currentUser = user;
        document.getElementById('profile-name').innerText = user.email.split('@')[0].toUpperCase();
        checkPremium(user.uid);
        if (document.getElementById('auth-screen').style.display === 'flex') {
            document.getElementById('auth-screen').style.display = 'none';
            switchTab('profile'); 
        }
    } else {
        currentUser = null; isPremium = false;
        document.getElementById('vip-badge').innerText = "FREE ACCOUNT";
        document.getElementById('vip-badge').style.background = "rgba(255,255,255,0.05)";
        document.getElementById('vip-badge').style.color = "var(--text-muted)";
        loadFreeUserAds();
        if(document.getElementById('profile-view').style.display === 'block') switchTab('home');
    }
});

function handleAuth(type) {
    const e = document.getElementById(type === 'login' ? 'email-in' : 'remail-in').value;
    const p = document.getElementById(type === 'login' ? 'pass-in' : 'rpass-in').value;
    if (type === 'login') auth.signInWithEmailAndPassword(e, p).catch(err => alert(err.message));
    else auth.createUserWithEmailAndPassword(e, p).catch(err => alert(err.message));
}
function toggleAuth() {
    const l = document.getElementById('login-form'), r = document.getElementById('reg-form');
    l.style.display = l.style.display === 'none' ? 'block' : 'none';
    r.style.display = r.style.display === 'none' ? 'block' : 'none';
}

function checkPremium(uid) {
    db.ref(`users/${uid}`).on('value', s => {
        const d = s.val();
        if(d && d.premiumExpiry > Date.now()) {
            isPremium = true;
            document.getElementById('vip-badge').innerText = "ROYAL VIP MEMBER 👑";
            document.getElementById('vip-badge').style.background = "var(--gold-gradient)";
            document.getElementById('vip-badge').style.color = "#000";
            document.getElementById('ad-banner-top').style.display = 'none';
        } else {
            isPremium = false;
        }
    });
}

// --- NAVIGATION & UI ---
function switchTab(tab) {
    document.querySelectorAll('.app-view').forEach(d => d.style.display = 'none');
    document.getElementById('auth-screen').style.display = 'none'; 
    closeSearch();
    
    if (tab === 'home') document.getElementById('main-app').style.display = 'block';
    if (tab === 'profile') {
        if (currentUser) document.getElementById('profile-view').style.display = 'block';
        else document.getElementById('auth-screen').style.display = 'flex';
    }
    document.querySelectorAll('nav i').forEach(i => i.classList.remove('active'));
    if(tab === 'home') document.querySelector('.fa-home').classList.add('active');
    if(tab === 'profile') document.querySelector('.fa-user').classList.add('active');
}

function switchInterface(to) {
    document.querySelectorAll('.app-view').forEach(d => d.style.display = 'none');
    if(to === 'movie') { document.getElementById('movie-box-view').style.display = 'block'; loadMovies(); } 
    else document.getElementById('main-app').style.display = 'block';
}

// --- LIVE SEARCH SYSTEM (NEW) ---
function openSearch() { document.getElementById('search-overlay').style.display = 'flex'; document.getElementById('search-input').focus(); }
function closeSearch() { document.getElementById('search-overlay').style.display = 'none'; document.getElementById('search-input').value = ""; document.getElementById('search-results').innerHTML = ""; }
function performSearch() {
    const q = document.getElementById('search-input').value.toLowerCase();
    const resDiv = document.getElementById('search-results');
    resDiv.innerHTML = "";
    if(q.length < 2) return;

    // Search Anime
    if(window.animeData) {
        Object.keys(window.animeData).forEach(name => {
            if(name.toLowerCase().includes(q)) {
                let thumb = window.animeData[name][0].thumbnail;
                resDiv.innerHTML += `<div class="folder-card" onclick="closeSearch(); openFolder('${name.replace(/'/g, "\\'")}')"><img src="${thumb}" loading="lazy"><div class="folder-info"><div class="folder-title">${name}</div></div></div>`;
            }
        });
    }
    // Search Movies
    if(window.movieData) {
        window.movieData.forEach(m => {
            if(m.title.toLowerCase().includes(q)) {
                let safeId = m.id || m.title.replace(/[^a-zA-Z0-9]/g, '_');
                resDiv.innerHTML += `<div class="folder-card" onclick="closeSearch(); playVideo('${m.title}', '${m.url}', '${safeId}', true, -1)"><img src="${m.thumbnail}" loading="lazy"><div class="folder-info"><div class="folder-title">${m.title}</div></div></div>`;
            }
        });
    }
}

// --- DATA LOADING ---
function loadContent() {
    db.ref('anime').on('value', snap => {
        const grid = document.getElementById('anime-grid'); grid.innerHTML = "";
        let folders = {};
        snap.forEach(c => { let d = c.val(); let f = (d.folder || 'Misc').trim(); if(!folders[f]) folders[f] = []; folders[f].push(d); });
        Object.keys(folders).forEach(name => {
            grid.innerHTML += `<div class="folder-card" onclick="openFolder('${name.replace(/'/g, "\\'")}')"><img src="${folders[name][0].thumbnail}" loading="lazy"><div class="folder-info"><div class="folder-title">${name}</div></div></div>`;
        });
        window.animeData = folders;
    });
}

function loadMovies() {
    db.ref('movies').on('value', snap => {
        const grid = document.getElementById('movie-grid'); grid.innerHTML = ""; window.movieData = []; 
        snap.forEach(c => {
            let d = c.val(); window.movieData.push(d);
            let safeId = d.id || d.title.replace(/[^a-zA-Z0-9]/g, '_');
            grid.innerHTML += `<div class="folder-card" onclick="playVideo('${d.title}', '${d.url}', '${safeId}', true, -1)"><img src="${d.thumbnail}" loading="lazy"><div class="folder-info"><div class="folder-title">${d.title}</div></div></div>`;
        });
    });
}

function openFolder(name) {
    const ep = window.animeData[name]; if(!ep || ep.length===0) return;
    playVideo(ep[0].title, ep[0].url, ep[0].id || ep[0].title.replace(/[^a-zA-Z0-9]/g, '_'), ep[0].type === 'premium', 0);
    const sel = document.getElementById('season-select'); sel.innerHTML = "";
    Object.keys(window.animeData).forEach(k => { let opt = document.createElement('option'); opt.value = k; opt.innerText = k; if(k===name) opt.selected = true; sel.appendChild(opt); });
    
    const cont = document.getElementById('episode-pill-container'); cont.innerHTML = "";
    ep.forEach((e, i) => {
        let btn = document.createElement('div'); btn.className = 'ep-pill'; btn.innerText = i+1; btn.id = `ep-btn-${i}`;
        btn.onclick = () => playVideo(e.title, e.url, e.id || e.title.replace(/[^a-zA-Z0-9]/g, '_'), e.type === 'premium', i);
        cont.appendChild(btn);
    });
}
function switchSeason(newFolder) { openFolder(newFolder); }

// --- VIDEO PLAYER LOGIC (Advanced + Continue Watching) ---
function playVideo(title, url, id, isPrem, index) {
    if(isPrem && !isPremium) { alert("ROYAL VIP REQUIRED! Please Login/Upgrade."); switchTab('profile'); return; }
    
    currentVideoId = id; document.getElementById('player-title').innerText = title;
    isMovieContent = (index === -1);
    document.getElementById('content-type-badge').innerText = isMovieContent ? "Movie" : "Anime";
    document.getElementById('episode-pill-container').style.display = isMovieContent ? 'none' : 'flex';
    document.querySelector('.dropdown-row').style.display = isMovieContent ? 'none' : 'flex';

    if(!isMovieContent) {
        document.querySelectorAll('.ep-pill').forEach(b => b.classList.remove('active'));
        let activeBtn = document.getElementById(`ep-btn-${index}`); if(activeBtn) activeBtn.classList.add('active');
    }

    const videoElement = document.getElementById('main-video');
    
    // Destroy previous HLS instance if exists
    if(hlsInstance) { hlsInstance.destroy(); hlsInstance = null; }

    // HLS Support (.m3u8) or standard MP4
    if(url.includes('.m3u8') && Hls.isSupported()) {
        hlsInstance = new Hls();
        hlsInstance.loadSource(url);
        hlsInstance.attachMedia(videoElement);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function() { checkProgressAndPlay(); });
    } else {
        videoElement.src = url;
        videoElement.addEventListener('loadedmetadata', checkProgressAndPlay, {once:true});
    }

    document.getElementById('player-view').style.display = 'block';
    loadForYouVideos(); loadSocialData(id);

    // Save history periodically
    videoElement.ontimeupdate = () => {
        if(currentUser && Math.floor(videoElement.currentTime) % 10 === 0 && videoElement.currentTime > 0) {
            db.ref(`users/${currentUser.uid}/watchlist/${id}`).set({ title: title, progress: videoElement.currentTime, date: Date.now() });
        }
    };
}

function checkProgressAndPlay() {
    if(currentUser) {
        db.ref(`users/${currentUser.uid}/watchlist/${currentVideoId}/progress`).once('value', s => {
            if(s.exists() && s.val() > 10) player.currentTime = s.val();
            player.play();
        });
    } else { player.play(); }
}

function closePlayer() {
    player.stop();
    if(hlsInstance) { hlsInstance.destroy(); hlsInstance = null; }
    document.getElementById('player-view').style.display = 'none';
}

function switchPlayerTab(tab) {
    document.querySelectorAll('.tab-item').forEach(e => e.classList.remove('active'));
    document.getElementById('tab-btn-' + tab).classList.add('active');
    document.getElementById('tab-content-foryou').style.display = tab==='foryou' ? 'block' : 'none';
    document.getElementById('tab-content-comments').style.display = tab==='comments' ? 'block' : 'none';
}

function loadForYouVideos() {
    const grid = document.getElementById('dynamic-rec-grid'); grid.innerHTML = "";
    if(isMovieContent && window.movieData) {
        window.movieData.forEach(m => grid.innerHTML += `<div class="rec-card" onclick="playVideo('${m.title}', '${m.url}', '${m.id}', true, -1)"><img src="${m.thumbnail}" loading="lazy"><div class="rec-title">${m.title}</div></div>`);
    } else if(window.animeData) {
        Object.keys(window.animeData).forEach(fName => grid.innerHTML += `<div class="rec-card" onclick="openFolder('${fName.replace(/'/g, "\\'")}')"><img src="${window.animeData[fName][0].thumbnail}" loading="lazy"><div class="rec-title">${fName}</div></div>`);
    }
}

// --- SOCIAL DATA ---
function loadSocialData(id) {
    if(currentUser) {
        db.ref(`likes/${id}/${currentUser.uid}`).on('value', s => {
            const btn = document.getElementById('like-btn');
            if(s.exists()) { btn.classList.add('liked'); btn.innerHTML = `<i class="fas fa-check"></i> Added`; } 
            else { btn.classList.remove('liked'); btn.innerHTML = `<i class="fas fa-plus"></i> My List`; }
        });
    }
}

function toggleLike() {
    if(!currentUser) { alert("Please login to add to list!"); switchTab('profile'); return; }
    const ref = db.ref(`likes/${currentVideoId}/${currentUser.uid}`);
    ref.once('value', s => { if(s.exists()) ref.remove(); else ref.set(true); });
}

function openHistory() {
    document.getElementById('history-view').style.display = 'block';
    db.ref(`users/${currentUser.uid}/watchlist`).limitToLast(20).on('value', s => {
        const c = document.getElementById('history-list-container'); c.innerHTML = "";
        if(!s.exists()) return c.innerHTML = "<p style='color:var(--text-muted); text-align:center;'>No history found.</p>";
        s.forEach(i => {
            const d = i.val();
            let min = d.progress ? Math.floor(d.progress / 60) + " min" : "Watched";
            c.innerHTML = `<div style="background:rgba(255,255,255,0.03); padding:18px; margin-bottom:12px; border-radius:14px; border:var(--glass-border); display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#fff; font-size:14px;">${d.title}</span><span style="color:var(--gold); font-size:11px;">${min}</span>
            </div>` + c.innerHTML;
        });
    });
}
function closeHistory() { document.getElementById('history-view').style.display = 'none'; }

function loadFreeUserAds() {
    if(adsLoaded) return; adsLoaded = true;
    let s1 = document.createElement('script'); s1.src = "https://pl28670634.effectivegatecpm.com/2f/28/1a/2f281ac58d64e6a580eb2d4171fe33d7.js"; document.body.appendChild(s1);
    let s2 = document.createElement('script'); s2.src = "https://pl28670723.effectivegatecpm.com/66/84/a1/6684a1bcf20a187f5844b6e689ba4482.js"; document.body.appendChild(s2);
}

// Init
loadContent(); loadMovies(); loadFreeUserAds(); switchTab('home');
