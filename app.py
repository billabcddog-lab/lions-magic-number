import streamlit as st
import requests

# 1. 網頁標題與外觀設定
st.set_page_config(page_title="攻城獅晉級預測戰情室", page_icon="🦁", layout="wide")
st.title("🦁 攻城獅晉級預測戰情室")

# 2. API 設定 - 使用我們找到的正確 Season 2 網址 📡
DEFAULT_STANDINGS_API = "https://api.tpbl.basketball/api/divisions/9/games/standings"
DEFAULT_SCHEDULE_API = "https://api.tpbl.basketball/api/seasons/2/games"

st.sidebar.header("📡 API 連線設定")
standings_url = st.sidebar.text_input("戰績 API 網址", DEFAULT_STANDINGS_API)
schedule_url = st.sidebar.text_input("賽程 API 網址", DEFAULT_SCHEDULE_API)

headers = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=600) # 快取 10 分鐘，避免頻繁請求
def fetch_data(s_url, g_url):
    try:
        s_resp = requests.get(s_url, headers=headers)
        s_resp.raise_for_status()
        g_resp = requests.get(g_url, headers=headers)
        g_resp.raise_for_status()
        return s_resp.json(), g_resp.json()
    except Exception as e:
        st.sidebar.error(f"連線失敗：{e}")
        return None, None

standings, schedule = fetch_data(standings_url, schedule_url)

if standings and schedule:
    # --- A. 側邊欄：預測模式控制 ---
    st.sidebar.divider()
    st.sidebar.header("🔮 預測模式")
    prediction_mode = st.sidebar.toggle("開啟預測功能")
    
    # 建立紀錄預測勝場/敗場的字典
    extra_wins = {team['team']['name']: 0 for team in standings}
    extra_losses = {team['team']['name']: 0 for team in standings}

    if prediction_mode:
        st.sidebar.info("請點選下方未來場次的勝方：")
        # 篩選狀態為 NOT_STARTED 的比賽 (根據 JSON 結構)
        upcoming_games = [g for g in schedule if g.get('status') == 'NOT_STARTED']
        
        if not upcoming_games:
            st.sidebar.warning("目前沒有尚未開始的比賽資料。")
        
        for idx, game in enumerate(upcoming_games[:15]): # 顯示接下來 15 場
            home = game['home_team']['name']
            away = game['away_team']['name']
            date = game.get('game_date', '未知日期')
            
            winner = st.sidebar.radio(
                f"📅 {date}：{home} vs {away}",
                ["尚未預測", home, away],
                key=f"predict_{idx}"
            )
            
            if winner == home:
                extra_wins[home] += 1
                extra_losses[away] += 1
            elif winner == away:
                extra_wins[away] += 1
                extra_losses[home] += 1

    # --- B. 核心邏輯計算 ---
    total_games = 36 # TPBL 賽制
    processed_teams = []
    lions_wins = 0
    lions_raw_data = None

    # 先處理各隊基礎勝率與數據
    for team in standings:
        name = team['team']['name']
        # 原始勝負 + 預測勝負
        w = team['score_won_matches'] + extra_wins.get(name, 0)
        l = team['score_lost_matches'] + extra_losses.get(name, 0)
        rate = w / (w + l) if (w + l) > 0 else 0
        
        processed_teams.append({
            'name': name, 'wins': w, 'losses': l, 'rate': rate, 'orig': team
        })
        
        if "攻城獅" in name:
            lions_wins = w
            lions_raw_data = team

    # 依勝率排序決定目前排名
    ranked_teams = sorted(processed_teams, key=lambda x: x['rate'], reverse=True)

    # --- C. 介面顯示 ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🦁 攻城獅預計勝場", f"{lions_wins} 勝", f"+{extra_wins.get('新竹御頂攻城獅', 0)} (預測)")
    with col2:
        st.write(f"### 目前模式：{'🔮 預測中' if prediction_mode else '📊 真實戰績'}")

    st.divider()

    table_data = []
    playoff_m = 0 # 初始化為數字 0，避免 TypeError
    found_playoff_cutoff = False
    
    for i, team_info in enumerate(ranked_teams):
        name = team_info['name']
        if "攻城獅" in name:
            continue
        
        # 對戰優勢判斷 ⚖️
        tie_breaker = 1
        note = ""
        if lions_raw_data:
            for record in lions_raw_data.get('against_result', []):
                if record['team']['name'] == name:
                    if record.get('score_won_matches', 0) > record.get('score_lost_matches', 0):
                        tie_breaker = 0
                        note = " ⚖️"
        
        # 計算魔術數字 M
        m_number = total_games - lions_wins - team_info['losses'] + tie_breaker
        
        # 標記第 4 名 (季後賽門檻)
        status = ""
        if i == 3: 
            status = " ⭐ 晉級關鍵"
            playoff_m = m_number
            found_playoff_cutoff = True
            
        table_data.append({
            "排名": i + 1,
            "球隊": name + status + note,
            "勝-敗": f"{team_info['wins']}W - {team_info['losses']}L",
            "魔術數字": f"M{max(0, m_number)}"
        })

    # 顯示季後賽關鍵數字
    if found_playoff_cutoff:
        st.subheader(f"🔥 晉級季後賽門檻數字：M{max(0, playoff_m)}")
    else:
        st.subheader("🔥 晉級季後賽門檻：計算中...")

    st.table(table_data)
    st.caption("註：⚖️ 表示攻城獅對該隊具有對戰優勢。⭐ 表示目前排名的季後賽競爭門檻。")

else:
    st.error("⚠️ 無法獲取資料。請檢查 API 網址或網路連線。")
