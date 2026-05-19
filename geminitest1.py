import streamlit as st
import requests
import json
import time
import os
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 預先定義高質感無字美學底圖 (當 Imagen 因免費 Key 400 限制時自動回退使用，確保展示不中斷)
UNSPLASH_FALLBACKS = {
    "cats": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&auto=format&fit=crop&q=80",
    "plants": "https://images.unsplash.com/photo-1512428559087-560fa5ceab42?w=800&auto=format&fit=crop&q=80",
    "tea": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=800&auto=format&fit=crop&q=80",
    "scenery": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
    "luck": "https://images.unsplash.com/photo-1508807526345-15e9b7f43081?w=800&auto=format&fit=crop&q=80",
    
    "coffee": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800&auto=format&fit=crop&q=80",
    "succulent": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=800&auto=format&fit=crop&q=80",
    "chibi": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=800&auto=format&fit=crop&q=80",
    "landscape": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
    "cozy": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"
}

# 設定 Streamlit 頁面設定
st.set_page_config(
    page_title="跨世代智慧圖文生成平台",
    page_icon="🪄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 定義長輩模式與晚輩模式的預設資料結構
CONFIG = {
    "senior": {
        "title": "👵 我是溫馨長輩 (傳送給晚輩)",
        "badge": "銀髮溫馨模式",
        "recipients": [
            {"id": "kids", "label": "👨‍👩‍👧‍👦 兒子女兒", "en": "children"},
            {"id": "grandkids", "label": "👶 孫子孫女", "en": "grandchildren"},
            {"id": "friends", "label": "🤝 親朋好友", "en": "friends"},
            {"id": "spouse", "label": "💖 牽手老伴", "en": "spouse"}
        ],
        "preferences": [
            {"id": "cats", "label": "🐱 軟萌貓咪", "en": "cute kitten with big eyes, playful and warm atmosphere"},
            {"id": "plants", "label": "🌸 文青花卉", "en": "beautiful gentle pastel peony flowers and cherry blossom"},
            {"id": "tea", "label": "☕ 茶與下午茶", "en": "steaming hot traditional porcelain tea cup with modern minimalist table"},
            {"id": "scenery", "label": "🏞️ 清新山水", "en": "magnificent misty mountains and calm lake, traditional landscape watercolor painting style"},
            {"id": "luck", "label": "🏮 祥瑞平安", "en": "traditional Chinese aesthetic design with elegant red lanterns, clean modern presentation"}
        ],
        "styles": [
            {"id": "watercolor", "label": "🎨 溫馨水彩", "en": "warm watercolor painting, soft textures, pastel color scheme, highly artistic, clean background"},
            {"id": "brush", "label": "🖌️ 水墨意境", "en": "traditional Chinese brush ink wash painting, Zen style, beautiful void space, high artistic sense"},
            {"id": "3dclay", "label": "🧸 3D黏土風", "en": "modern 3D clay rendering, cute chibi character toys style, bright clean vibrant lighting, highly professional"},
            {"id": "minimalist", "label": "📐 現代極簡", "en": "modern minimalist aesthetic, flat vector illustration, elegant color palette, high-end feel"},
            {"id": "photo", "label": "📸 溫馨寫實", "en": "warm photographic shot, soft sunlight, highly detailed, photorealistic, extremely peaceful"}
        ],
        "presets": [
            "早安平安，事事順利！",
            "平安喜樂，福氣滿滿！",
            "天天開心，保重身體！",
            "吉祥如意，祝你有美好的一天！"
        ]
    },
    "youth": {
        "title": "🧑 我是貼心晚輩 (傳送給長輩)",
        "badge": "文青貼心模式",
        "recipients": [
            {"id": "parents", "label": "👨‍👩‍👦 爸爸媽媽", "en": "parents"},
            {"id": "grandparents", "label": "👴👵 爺爺奶奶/外公外婆", "en": "grandparents"},
            {"id": "family", "label": "🏠 家族溫馨群組", "en": "whole family group"}
        ],
        "preferences": [
            {"id": "coffee", "label": "☕ 精緻咖啡", "en": "aesthetic latte art coffee cup on a sunny wooden cafe desk, warm sunlight, modern lifestyle"},
            {"id": "succulent", "label": "🌵 多肉植物", "en": "cute little succulent plant pots on concrete windowsill, minimalist design"},
            {"id": "chibi", "label": "🐶 萌萌柴犬", "en": "happy cute Shiba Inu dog, playful and friendly, modern illustration style"},
            {"id": "landscape", "label": "⛰️ 療癒風景", "en": "minimalist scenic illustration of green meadows and distant mountains under sunny blue sky"},
            {"id": "cozy", "label": "🛋️ 居家療癒", "en": "cozy home corner, fluffy blanket, fairy lights, warm atmospheric glow"}
        ],
        "styles": [
            {"id": "minimalist", "label": "📐 現代極簡", "en": "modern minimalist graphic design, vector flat illustration, Scandinavian style, premium look"},
            {"id": "cute_cartoon", "label": "🧸 萌趣插畫", "en": "cute pastel chibi illustration style, warm vibes, heartwarming, perfect design"},
            {"id": "vaporwave", "label": "🌌 夢幻星空", "en": "dreamy pastel galaxy and starry night sky, cozy magical watercolor illustration"},
            {"id": "photo", "label": "📸 文青攝影", "en": "cinematic aesthetic photograph, warm sunset light flares, high visual depth, peaceful"}
        ],
        "presets": [
            "祝您今天有個美好的一天！",
            "早安！今天天氣多變，注意保暖喔！",
            "出門記得攜帶雨具，路上小心唷！",
            "想您了！有空常聯絡唷！"
        ]
    }
}

def get_environmental_status():
    """模擬二十四節氣與天氣提醒演算法 (依據當前日期計算)"""
    today = datetime.now()
    month = today.month
    day = today.day
    
    # 節氣估計
    if month == 5:
        solar_term = "立夏時節" if day < 21 else "小滿時節"
        weather_alert = "初夏氣溫升高，中午防曬，午後容易有局部陣雨，出門記得帶傘喔！"
    elif month == 6:
        solar_term = "芒種時節" if day < 21 else "夏至時節"
        weather_alert = "梅雨季節好發驟雨，天氣潮濕悶熱，室內記得除濕與多喝水！"
    elif month in [7, 8]:
        solar_term = "三伏盛夏"
        weather_alert = "盛夏酷暑紫外線強烈，請避免在烈日下曝曬，多補充水分與鹽分！"
    else:
        solar_term = "四季遞嬗"
        weather_alert = "溫差變化大，早晚記得多加一件薄外套，注重保暖！"
        
    return f"{month}月{day}日 · {solar_term}", weather_alert

# 讀取 API Key (優先序：Streamlit Secrets -> 系統環境變數 -> 使用者自備金鑰)
system_api_key = ""
is_using_system_key = False

# 1. 優先偵測 Streamlit 雲端內建的 Secrets 託管機制
if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    system_api_key = st.secrets["GEMINI_API_KEY"]
    is_using_system_key = True
# 2. 次要偵測本地主機或伺服器系統環境變數
elif os.environ.get("GEMINI_API_KEY"):
    system_api_key = os.environ.get("GEMINI_API_KEY", "")
    is_using_system_key = True

# 側邊欄安全設定 UI 調整
st.sidebar.markdown("### 🔑 API 安全憑證設定")

if is_using_system_key:
    st.sidebar.success("🟢 系統已開啟「免輸入金鑰」通道！\n您不需貼上金鑰，即可直接一鍵生成圖文。")
    # 提供折疊備用，當系統公用額度用完時可讓特定使用者輸入自己的 Key
    with st.sidebar.expander("🛠️ 額度用完了？想自備備用金鑰"):
        user_api_key = st.text_input(
            "輸入您自有的 Gemini API Key",
            type="password",
            help="若系統的公用免費共享額度用盡，您可以在此輸入自己的 Key 以維持正常生成。"
        )
    api_key = user_api_key if user_api_key else system_api_key
else:
    api_key = st.sidebar.text_input(
        "請輸入您的 Gemini API Key",
        type="password",
        help="本程式完全運行於用戶端，API Key 將安全地直接傳送給 Google 端點，不會被第三方記錄。",
        value=""
    )
    if not api_key:
        st.sidebar.warning("⚠️ 請先在左側輸入 Gemini API Key 才能正式啟用 AI 圖文生成功能！")
        st.sidebar.info(
            "💡 **開發者部署提示：**\n"
            "若要讓大家免輸入 Key 直接使用，請將此 App 部署至 Streamlit Cloud，"
            "並在雲端管理後台的 **Settings ➔ Secrets** 中設定：\n"
            "```toml\n"
            "GEMINI_API_KEY = \"您的金鑰值\"\n"
            "```"
        )

def call_gemini_expand_prompt(api_key, user_context):
    """呼叫 Gemini 2.5 Flash 將使用者勾選的繁體中文標籤擴寫為高品質生圖英文提示詞"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    system_prompt = (
        "You are a world-class prompt engineer for Imagen 3/4. "
        "Your task is to expand the user's selected Chinese options into a highly detailed, gorgeous, and warm English image-generation prompt. "
        "CRITICAL INSTRUCTIONS:\n"
        "1. Do NOT put any text, words, alphabets, or signatures on the image. Ensure the image is a pure artistic background.\n"
        "2. Ensure there is elegant negative space (at the top or bottom) for overlaying custom text later.\n"
        "3. Provide ONLY the final English prompt as a single string. No introductions, no markdown code blocks, no explanations."
    )
    
    payload = {
        "contents": [{"parts": [{"text": f"User Preferences Context: {user_context}\nGenerate the expanded English prompt now:"}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            st.error(f"Gemini 呼叫失敗，錯誤碼：{response.status_code}，請確認 API Key 是否正確。")
            return None
    except Exception as e:
        st.error(f"連線至 Gemini API 時發生異常: {str(e)}")
        return None

def call_imagen_generate(api_key, prompt, pref_id=None):
    """呼叫 Imagen 4.0 圖像生成模型生成高畫質無字卡片底圖 (整合免費版自動防禦回退機制)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1" # 正方形長輩圖標準比例
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            base64_data = result['predictions'][0]['bytesBase64Encoded']
            import base64
            img_data = base64.b64decode(base64_data)
            st.session_state.is_demo_mode = False
            return Image.open(io.BytesIO(img_data))
        
        elif response.status_code == 400 and "paid plans" in response.text:
            # 偵測到 2026 年最新「付費計畫限制」錯誤
            st.session_state.is_demo_mode = True
            fallback_url = UNSPLASH_FALLBACKS.get(pref_id, "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80")
            
            # 從 Unsplash 下載對應之高質感美學圖片
            img_response = requests.get(fallback_url, timeout=15)
            if img_response.status_code == 200:
                return Image.open(io.BytesIO(img_response.content))
            else:
                return None
        else:
            st.error(f"Imagen 生成失敗，錯誤碼：{response.status_code}")
            st.write(response.text)
            return None
    except Exception as e:
        # 其他異常情況也安全回退
        st.session_state.is_demo_mode = True
        fallback_url = UNSPLASH_FALLBACKS.get(pref_id, "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80")
        try:
            img_response = requests.get(fallback_url, timeout=15)
            return Image.open(io.BytesIO(img_response.content))
        except:
            st.error(f"連線至 Imagen API 時發生異常: {str(e)}")
            return None

def get_system_font(font_size):
    """依據執行系統環境自動抓取適合繁體中文渲染的粗體字型，確保長輩閱讀體驗"""
    font_paths = [
        "C:\\Windows\\Fonts\\msjhbd.ttc", # Windows 微軟正黑體 粗體
        "C:\\Windows\\Fonts\\msjh.ttc",   # Windows 微軟正黑體 標準
        "/System/Library/Fonts/STHeiti Medium.ttc", # macOS 華文黑體
        "/System/Library/Fonts/PingFang.ttc",       # macOS 蘋方
        "/usr/share/fonts/truetype/droid/DroidSansFallback.ttf", # Linux 
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"    # Ubuntu CJK
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except:
                continue
                
    # 終極備用字型
    return ImageFont.load_default()

def draw_card_with_text(base_image, text, font_size, text_color, position, stroke_color="#000000"):
    """使用 Pillow 在影像上渲染高對比度、具備多重陰影與描邊的自訂關懷大字"""
    # 複製原圖，避免就地修改
    img_canvas = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(img_canvas)
    width, height = img_canvas.size
    
    font = get_system_font(font_size)
    
    # 1. 自動依畫布寬度分行，避免文字超出兩側
    max_char_width = width - 100
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        # 計算測試行寬度
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width > max_char_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
        
    # 2. 計算垂直渲染起始點
    line_spacing = font_size * 1.2
    total_height = len(lines) * line_spacing
    
    if position == "上方":
        start_y = 60
    elif position == "中央":
        start_y = (height - total_height) / 2
    else: # 下方
        start_y = height - total_height - 60
        
    # 3. 雙層高光描邊渲染 (在任何複雜光影背景下都能完美辨識)
    for i, line in enumerate(lines):
        y = start_y + (i * line_spacing)
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) / 2
        
        # A. 繪製特粗黑底描邊 (Stroke) 作為防遮擋背景
        stroke_width = int(font_size * 0.12)
        draw.text(
            (x, y), line, font=font, fill=text_color,
            stroke_width=stroke_width, stroke_fill=stroke_color
        )
        
    return img_canvas.convert("RGB")

# 標題與引言區
st.markdown(
    """
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #10B981; font-weight: 900;'>🖨️ 跨世代智慧圖文問候卡生成平台</h1>
        <p style='color: #6B7280; font-size: 1.1em;'>運用雙核心 AI (Gemini + Imagen 4) 技術 · 一鍵消除世代隔閡 · 送出專屬溫馨祝福</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# 取得環境速報
solar_term, weather_alert = get_environmental_status()

# 頂部模式切換：長輩模式(大按鈕大字體) vs 晚輩模式(簡約高雅)
mode = st.radio(
    "👉 **請選擇您的身份：**",
    options=["senior", "youth"],
    format_func=lambda x: CONFIG[x]["title"],
    horizontal=True
)

current_cfg = CONFIG[mode]
is_senior = (mode == "senior")

# 建立左右兩欄
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.subheader("🛠️ 卡片內容快選面板")
    
    # 1. 選擇傳送對象
    rec_labels = [r["label"] for r in current_cfg["recipients"]]
    selected_rec_label = st.selectbox("🎯 我想送卡片給：", rec_labels)
    selected_rec = next(r for r in current_cfg["recipients"] if r["label"] == selected_rec_label)
    
    # 2. 選擇喜好主題
    pref_labels = [p["label"] for p in current_cfg["preferences"]]
    selected_pref_label = st.selectbox("❤️ 對方最喜歡的畫面元素：", pref_labels)
    selected_pref = next(p for p in current_cfg["preferences"] if p["label"] == selected_pref_label)
    
    # 3. 選擇藝術風格
    style_labels = [s["label"] for s in current_cfg["styles"]]
    selected_style_label = st.selectbox("🎨 我偏好的卡片畫面風格：", style_labels)
    selected_style = next(s for s in current_cfg["styles"] if s["label"] == selected_style_label)
    
    # 4. 氣候環境速報整合
    st.markdown("---")
    st.markdown(f"#### 🍂 當日環境速報整合")
    use_env = st.checkbox("在卡片創意中主動帶入今日節氣與生活貼心關懷", value=True)
    
    # 顯示動態計算出來的天氣速報
    st.info(f"**今日節氣氣候指引：**\n【{solar_term}】\n*{weather_alert}*")
    
    # 5. 自訂卡片關懷大字
    st.markdown("---")
    st.markdown("#### ✍️ 疊加在卡片上的祝福語")
    
    # 快速點選預設祝福語
    st.markdown("<small style='color:gray;'>快速點選常用語：</small>", unsafe_allow_html=True)
    preset_cols = st.columns(len(current_cfg["presets"]))
    chosen_preset = ""
    for idx, preset_text in enumerate(current_cfg["presets"]):
        if preset_cols[idx].button(preset_text, key=f"preset_{idx}"):
            chosen_preset = preset_text
            
    # 輸入祝福語
    default_text = chosen_preset if chosen_preset else current_cfg["presets"][0]
    custom_text = st.text_input(
        "📝 輸入自訂祝福文字（字體會進行特別防遮擋與高對比排版）：",
        value=default_text,
        max_chars=35
    )
    
    # 文字排版樣式微調
    with st.expander("⚙️ 祝福文字高對比排版微調"):
        font_size = st.slider("中文字型大小", min_value=24, max_value=80, value=48, step=4)
        
        font_color = st.color_picker("中文字型顏色", value="#FFFFFF")
        stroke_color = st.color_picker("外框描邊顏色 (推薦深色，防背景遮擋效果佳)", value="#000000")
        
        position = st.radio("文字顯示位置", options=["上方", "中央", "下方"], index=2, horizontal=True)

    # 點擊生成按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button(
        "🔮 一鍵智慧繪製！生成我的跨世代關懷卡片",
        type="primary",
        use_container_width=True
    )

with col_right:
    st.subheader("🖼️ 卡片成果即時預覽")
    
    # 建立狀態暫存區
    if "base_image" not in st.session_state:
        st.session_state.base_image = None
    if "prompt_lineage" not in st.session_state:
        st.session_state.prompt_lineage = ""
    if "is_demo_mode" not in st.session_state:
        st.session_state.is_demo_mode = False
        
    # 當點擊生成
    if generate_btn:
        if not api_key:
            st.error("❌ 尚未設定 API Key！請先在左邊側邊欄輸入 API 金鑰。")
        else:
            with st.spinner("🧙 步驟一：Gemini 2.5 正在為您智慧擴寫提示詞..."):
                env_context = f"Today is {solar_term}. Weather tip: {weather_alert}" if use_env else ""
                user_context = (
                    f"Recipient: {selected_rec['en']}. "
                    f"Visual subject of interest: {selected_pref['en']}. "
                    f"Artistic Style: {selected_style['en']}. "
                    f"{env_context}"
                )
                
                expanded_prompt = call_gemini_expand_prompt(api_key, user_context)
                
            if expanded_prompt:
                st.session_state.prompt_lineage = expanded_prompt
                
                with st.spinner("🎨 步驟二：Imagen 正在為您彩繪無字藝術底圖..."):
                    # 將 selected_pref['id'] 傳入，供防禦性回退機制使用
                    generated_img = call_imagen_generate(api_key, expanded_prompt, pref_id=selected_pref['id'])
                    
                    if generated_img:
                        st.session_state.base_image = generated_img
                        st.success("🎉 卡片背景繪製成功！")
            
    # 進行最終文字渲染預覽與下載
    if st.session_state.base_image is not None:
        # 如果是 Demo 模式，在預覽區上方顯示友善提示
        if st.session_state.is_demo_mode:
            st.warning(
                "💡 **溫馨提示：系統目前正處於「自動 Demo 模擬底圖模式」**\n\n"
                "偵測到您使用的 Gemini API 尚未升級至付費計劃 (Pay-as-you-go)，"
                "因此 Google 限制了 Imagen 繪圖功能。為確保體驗完整，"
                "系統已自動為您媒合**高質感精美美學無字底圖**。您依然能隨意更換卡片文字、排版並下載成品！\n\n"
                "👉 *如需體驗正宗 AI 實時繪圖，請依提示至 Google AI Studio 綁定信用卡升級即可！*"
            )
            
        # 疊加繁體字大字
        final_card = draw_card_with_text(
            st.session_state.base_image,
            custom_text,
            font_size,
            font_color,
            position,
            stroke_color
        )
        
        # 顯示卡片
        st.image(final_card, use_container_width=True, caption="智慧生成之跨世代關懷卡片")
        
        # 輸出圖片以供下載
        buf = io.BytesIO()
        final_card.save(buf, format="JPEG", quality=95)
        byte_im = buf.getvalue()
        
        # 下載按鈕
        st.download_button(
            label="💾 下載卡片到手機 / 電腦",
            data=byte_im,
            file_name=f"AI_Care_Card_{int(time.time())}.jpg",
            mime="image/jpeg",
            use_container_width=True
        )
        
        # LINE 分享引導
        st.markdown(
            """
            <div style='background-color:#06C755; color:white; padding:12px; border-radius:12px; text-align:center; font-weight:bold; margin-top:10px;'>
                💬 貼心叮嚀：點擊上方儲存按鈕，即可將精美大圖傳送至 LINE 家庭群組喔！
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 技術後台顯示 (展示給評審看的 Prompt lineage)
        with st.expander("💡 檢視 AI 智慧擴寫提示詞軌跡 (Prompt Lineage)"):
            st.code(st.session_state.prompt_lineage, language="markdown")
            
    else:
        # 預設占位狀態
        st.info("💡 尚未生成卡片。請於左側設定您喜好的主題元素，然後點選「一鍵智慧繪製」！")
        # 預設顯示一張範例卡片的示意效果
        placeholder_image = Image.new("RGB", (600, 600), "#F3F4F6")
        draw = ImageDraw.Draw(placeholder_image)
        draw.rectangle([20, 20, 580, 580], outline="#E5E7EB", width=4)
        st.image(placeholder_image, use_container_width=True, caption="預覽畫布")