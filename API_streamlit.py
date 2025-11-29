import streamlit as st
import google.generativeai as genai
import requests
import urllib3

# ------------------------------
# 忽略 SSL 警告
# ------------------------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------
# API Keys
# ------------------------------
GEMINI_API_KEY = "AIzaSyD8rUxv5SaOhu4tNZmNXZGZnpmi5oo-d7U"
CWA_API_KEY = "CWA-9B8EC981-1891-49B2-8EA8-A84BF57CF47B"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ------------------------------
# 取得天氣
# ------------------------------
def get_weather(location="臺北市"):
    url = (
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
        f"?Authorization={CWA_API_KEY}&locationName={location}"
    )
    try:
        r = requests.get(url, verify=False, timeout=10)
        data = r.json()

        loc = data["records"]["location"][0]
        weather = loc["weatherElement"]

        wx = weather[0]["time"][0]["parameter"]["parameterName"]
        mint = weather[2]["time"][0]["parameter"]["parameterName"]
        maxt = weather[4]["time"][0]["parameter"]["parameterName"]

        # 降雨機率若缺失就預設 0%
        try:
            pop = int(weather[1]["time"][0]["parameter"]["parameterName"])
        except:
            pop = 0

        return wx, int(mint), int(maxt), pop

    except Exception as e:
        st.error(f"例外錯誤：{e}")
        return None, None, None, None

# ------------------------------
# AI 穿著與雨具建議
# ------------------------------
def generate_advice(wx, mint, maxt, pop):
    prompt = f"""
今天的天氣資訊：
- 天氣：{wx}
- 氣溫：{mint}~{maxt}°C
- 降雨機率：{pop}%

請用溫和、貼心語氣給穿著與雨具建議，字數 60 字內。
請直接給出具體建議，不要提任何不確定性或資料缺失。
"""
    res = model.generate_content(prompt)
    return res.text

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("🌤️ 今日天氣穿著建議助手")

city = st.selectbox(
    "選擇縣市",
    ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
)

# session_state 保存天氣資料
if "wx" not in st.session_state:
    st.session_state.wx = None
    st.session_state.mint = None
    st.session_state.maxt = None
    st.session_state.pop = None

# ------------------------------
# 按鈕：取得天氣
# ------------------------------
if st.button("取得今日天氣"):
    wx, mint, maxt, pop = get_weather(city)

    if wx is None:
        st.error("⚠️ 無法取得天氣資料")
    else:
        st.session_state.wx = wx
        st.session_state.mint = mint
        st.session_state.maxt = maxt
        st.session_state.pop = pop

        st.success(f"🌈 天氣：{wx}")
        st.write(f"🌡 溫度：{mint}°C ~ {maxt}°C")
        st.write(f"💧 降雨機率：{pop}%")

        st.subheader("👕 AI 穿著建議")
        st.info(generate_advice(wx, mint, maxt, pop))

# ------------------------------
# AI 問答
# ------------------------------
st.markdown("---")
st.header("🌈 詢問 AI 天氣問題")

q = st.text_input("你想問什麼？")

if st.button("詢問 AI"):
    if q.strip() == "":
        st.warning("請輸入問題")
    elif st.session_state.wx is None:
        st.warning("請先按上方『取得今日天氣』")
    else:
        prompt = f"""
以下是 {city} 今日天氣：
- 天氣：{st.session_state.wx}
- 氣溫：{st.session_state.mint}~{st.session_state.maxt}°C
- 降雨機率：{st.session_state.pop}%

使用者問題：{q}

請根據上述天氣資訊，用溫和、貼心語氣直接給出合理建議（60 字內）。
"""
        res = model.generate_content(prompt)
        st.success(res.text)
