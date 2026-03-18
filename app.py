import streamlit as st
import requests

# 1. 網頁標題與外觀設定
st.set_page_config(page_title="攻城獅預測觀測站", page_icon="🦁", layout="wide")
st.title("🦁 攻城獅晉級預測戰情室")

# 2. 定義 API 路徑
STANDINGS_API = "https://api.tpbl.basketball/api/divisions/9/games/standings"
SCHEDULE_API = "https://api.tpbl.basketball/api/divisions/9/games" # 假設的賽程路徑
headers = {"User-Agent": "Mozilla/5.0"}

def fetch_data():
    try:
        # 抓取戰績
        standings_resp = requests.get(STANDINGS_API, headers=headers)
        standings_data = standings_resp.json()
        
        # 抓取賽程 (這裡先模擬抓取接下來的比賽)
        # 註：若 API 不同，此處邏輯需微調
        schedule_resp = requests.get(SCHEDULE_API, headers=headers)
        schedule_data = schedule_resp.json()
        
        return standings_data, schedule_data
    except:
        return None, None

standings, schedule = fetch_data()

if standings:
    # --- A. 側邊欄：預測模式控制 ---
    st.sidebar.header("🛠️ 預測模式")
    prediction_mode = st.sidebar.toggle("開啟預測模式")
    
    # 建立一個紀錄預測勝場的字典
    extra_wins = {team['team']['name']: 0 for team in standings}
    extra_losses = {team['team']['name']: 0 for team in standings}

    if prediction_mode:
        st.sidebar.info("請在下方選擇未來場次的勝方：")
        
        # 篩選出尚未開始的比賽 (範例：狀態為 upcoming 或比分皆為 0)
        upcoming_games = [g for g in schedule if g.get('status') == 'upcoming' or g.get('score_home') == 0][:10] # 取前10場
        
        for idx, game in enumerate(upcoming_games):
            home = game['team_home']['name']
            away = game['team_away']['name']
            date = game.get('start_time', '未知時間')[:10]
            
            # 讓使用者選勝方
            winner = st.sidebar.radio(
                f"📅 {date}：{home} vs {away}",
                ["尚未決定", home, away],
                key=f"game_{idx}"
            )
            
            if winner == home:
                extra_wins[home] += 1
                extra_losses[away] += 1
            elif winner == away:
                extra_wins[away] += 1
                extra_losses[home] += 1

    # --- B. 核心邏輯計算 ---
    total_games = 36
    lions_wins = 0
    lions_raw_data = None
    processed_teams = []

    # 將原始戰績加上預測戰績
    for team in standings:
        name = team['team']['name']
        w = team['score_won_matches'] + extra_wins[name]
        l = team['score_lost_matches'] + extra_losses[name]
        rate = w / (w + l) if (w + l) > 0 else 0
        
        processed_teams.append({
            'name': name, 
            'wins': w, 
            'losses': l, 
            'rate': rate,
            'original_data': team # 保留原始資料供對戰優勢判斷
        })
        
        if "攻城獅" in name:
            lions_wins = w
            lions_raw_data = team

    # 重新排序排名
    ranked_teams = sorted(processed_teams, key=lambda x: x['rate'], reverse=True)

    # --- C. 網頁顯示 ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🦁 攻城獅預計勝場", value=f"{lions_wins} 勝", delta=extra_wins.get("新竹御頂攻城獅", 0))
    with col2:
        mode_text = "🔮 預測模式已開啟" if prediction_mode else "📊 目前真實戰績"
        st.write(f"### 狀態：{mode_text}")

    st.divider()

    table_data = []
    playoff_m = "N/A"
    
    for i, team_info in enumerate(ranked_teams):
        name = team_info['name']
        if "攻城獅" in name:
            continue
        
        # 對戰優勢判斷 (使用原始 API 資料)
        tie_breaker_bonus = 1
        tie_note = ""
        if lions_raw_data:
            for record in lions_raw_data.get('against_result', []):
                if record['team']['name'] == name:
                    if record.get('score_won_matches', 0) > record.get('score_lost_matches', 0):
                        tie_breaker_bonus = 0
                        tie_note = " ⚖️"
        
        # 計算魔術數字
        m_number = total_games - lions_wins - team_info['losses'] + tie_breaker_bonus
        
        status = " ⭐" if i == 3 else ""
        if i == 3: playoff_m = m_number
            
        table_data.append({
            "排名": i + 1,
            "球隊": name + status + tie_note,
            "勝-敗": f"{team_info['wins']}W - {team_info['losses']}L",
            "魔術數字": f"M{max(0, m_number)}"
        })

    st.subheader(f"🔥 晉級季後賽門檻：M{max(0, playoff_m)}")
    st.table(table_data)

else:
    st.error("無法連線至 TPBL API，請檢查網路或 API 位址。")
