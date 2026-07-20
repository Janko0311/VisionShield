let currentLang = 'zh';
let currentMode = 'normal';


let lastSpokenSector = ""; 

// --- Language Configuration Pack ---
const langPack = {
    zh: { r_title: "實時邊緣探測地圖", r_desc: "環形指針與硬件 Servo 轉動角度毫秒級同步。", t_title: "智能決策數據指標", m_metric: "核心指標", m_val: "即時數據", t1: "當前雷達方位", t2: "障礙物實時距離", t3: "自主避險警告", safe: "✅ 前方路徑安全", left: "⚠️ 左前方危險", right: "⚠️ 右前方危險", center: "🛑 正前方危險", clear: "路徑暢通" },
    en: { r_title: "Real-time Detection Map", r_desc: "Circular gauge syncs with hardware Servo in real-time.", t_title: "AI Decision Telemetry", m_metric: "Metrics", m_val: "Telemetry", t1: "Current Sector", t2: "Real-time Distance", t3: "Collision Alert", safe: "✅ Path Clear", left: "⚠️ Left Alert", right: "⚠️ Right Alert", center: "🛑 Center Alert", clear: "Clear" }
};

// --- UI Language & Mode Selectors ---
function setLang(lang) {
    currentLang = lang;
    document.getElementById('btn-zh').classList.toggle('active', lang === 'zh');
    document.getElementById('btn-en').classList.toggle('active', lang === 'en');
    lastSpokenSector = "";
}

function setMode(mode) {
    currentMode = mode;
    document.getElementById('btn-norm').classList.toggle('active', mode === 'normal');
    document.getElementById('btn-fire').classList.toggle('active', mode === 'fire');
    document.getElementById('btn-norm').style.background = mode === 'normal' ? 'rgba(94,92,230,0.25)' : 'none';
    document.getElementById('btn-fire').style.background = mode === 'fire' ? 'rgba(248,113,113,0.25)' : 'none';
}


function webSpeak(sectorKey, text) {    
    if ((window.speechSynthesis && window.speechSynthesis.speaking) || lastSpokenSector === sectorKey) {
        return; 
    }

    if ('speechSynthesis' in window) {
        lastSpokenSector = sectorKey;
        
        let utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = currentLang === 'zh' ? 'zh-HK' : 'en-US';
        
        utterance.onerror = function() {
            lastSpokenSector = "";
        };

        window.speechSynthesis.speak(utterance);
    }
}

// --- Adaptive Data Ingestion Loop ---
async function fetchRadarData() {
    let paths = ['./data.json', 'data.json', '/data.json', '../data.json'];
    for (let path of paths) {
        try {
            let res = await fetch(path + '?t=' + Date.now());
            if (res.ok) {
                let data = await res.json();
                if (data && typeof data.angle !== 'undefined') {
                    updateDashboard(data.angle, data.distance);
                    return;
                }
            }
        } catch (e) {}
    }
}


setInterval(fetchRadarData, 200);


function updateDashboard(angle, dist) {
    let percent = (angle / 180) * 100;
    let color = currentMode === 'fire' ? '#F87171' : '#8B5CF6';
    

    let radarCircle = document.getElementById('radar-circle');
    if (radarCircle) radarCircle.style.background = `conic-gradient(${color} ${percent}%, rgba(255, 255, 255, 0.1) ${percent}%)`;
    
    let lblAngle = document.getElementById('lbl-angle');
    if (lblAngle) lblAngle.innerText = angle + '°';
    
    
    let sector = currentLang === 'zh' ? 
        (angle < 65 ? '左前方' : (angle > 115 ? '右前方' : '正前方')) : 
        (angle < 65 ? 'Left' : (angle > 115 ? 'Right' : 'Center'));
    let valSector = document.getElementById('val-sector');
    if (valSector) valSector.innerText = sector;
    

    let valDistance = document.getElementById('val-distance');
    if (valDistance) {
        valDistance.innerText = dist >= 400 ? langPack[currentLang].clear : dist + ' cm';
    }
    

    let alertSpan = document.getElementById('val-alert');
    if (alertSpan) {
        if (dist < 40) {
            alertSpan.className = 'alert-active';
            alertSpan.style.color = '#F87171'; 
            
            if (currentLang === 'zh') {
                if (angle < 65) { 
                    alertSpan.innerText = langPack.zh.left; 
                    webSpeak("left", "注意，左前方有障礙物"); 
                } else if (angle > 115) { 
                    alertSpan.innerText = langPack.zh.right; 
                    webSpeak("right", "注意，右前方有障礙物"); 
                } else { 
                    alertSpan.innerText = langPack.zh.center; 
                    webSpeak("center", "請停步，正前方有危險"); 
                }
            } else {
                if (angle < 65) { 
                    alertSpan.innerText = langPack.en.left; 
                    webSpeak("left", "Warning, left obstacle"); 
                } else if (angle > 115) { 
                    alertSpan.innerText = langPack.en.right; 
                    webSpeak("right", "Warning, right obstacle"); 
                } else { 
                    alertSpan.innerText = langPack.en.center; 
                    webSpeak("center", "Stop, danger ahead"); 
                }
            }
        } else {
            alertSpan.className = ''; 
            alertSpan.style.color = '#10B981'; 
            alertSpan.innerText = langPack[currentLang].safe;
            
            
            lastSpokenSector = ""; 
        }
    }
}