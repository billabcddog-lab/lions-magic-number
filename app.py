import streamlit as st
import requests

# 1. 網頁標題與外觀設定
st.set_page_config(page_title="攻城獅戰績觀測站", page_icon="🦁")
st.title("🦁 攻城獅晉級之路：魔術數字觀測站")

# 2. 抓取最新戰績 (API)
api_url = "https://api.tpbl.basketball/api/divisions/9/games/standings"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(api_url, headers=headers)
    data = response.json()
    teams_list = data['data']

    # 3. 資料處理與排序
    total_games = 36
    lions_wins = 0
    processed_teams = []

    # 先找出攻城獅勝場
    for team in teams_list:
        name = team['team']['name']
        w = team['score_won_matches']
        l = team['score_lost_matches']
        rate = w / (w + l) if (w + l) > 0 else 0
        processed_teams.append({'name': name, 'wins': w, 'losses': l, 'rate': rate})
        if "攻城獅" in name:
            lions_wins = w

    # 依勝率排序
    ranked_teams = sorted(processed_teams, key=lambda x: x['rate'], reverse=True)

    # 4. 顯示目前概況
    st.metric(label="🦁 攻城獅目前勝場", value=f"{lions_wins} 勝")
    st.divider()

    # 5. 計算並建立表格資料
    table_data = []
    playoff_m = "N/A"
    
    for i, team in enumerate(ranked_teams):
        if "攻城獅" in team['name']:
            continue
        
        # 計算魔術數字 (目前預設都有對戰優勢，所以不加1；若要保險可加1)
        m_number = total_games - lions_wins - team['losses'] + 1
        
        # 標記季後賽門檻 (第4名)
        status = ""
        if i == 3: 
            status = " ⭐ 晉級關鍵"
            playoff_m = m_number
            
        table_data.append({
            "排名": i + 1,
            "球隊名稱": team['name'] + status,
            "勝/敗": f"{team['wins']}W - {team['losses']}L",
            "魔術數字": f"M{max(0, m_number)}"
        })

    st.subheader(f"🔥 晉級季後賽魔術數字：M{max(0, playoff_m)}")
    st.table(table_data)

except Exception as e:
    st.error(f"偵錯訊息：{e}")
    # 這行會把 API 抓到的內容印出來，幫我們判斷是哪裡出錯
    if 'response' in locals():
        st.write("API 回應內容：", response.text[:500])
