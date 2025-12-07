import streamlit as st
import pandas as pd
import datetime
import time
import os
import csv
import plotly.express as px
from io import StringIO

# --- 页面设置 ---
st.set_page_config(page_title="材料人学习助手", page_icon="🧪", layout="centered")

# --- 配置 ---
# 云端版我们主要依靠内存和上传/下载来管理数据
DATA_FILE = "study_log.csv"
SUBJECT_FILE = "subjects.txt"
POMODORO_MINUTES = 25

# --- 预设学科 ---
DEFAULT_SUBJECTS = [
    "概率论与数理统计", "物理化学", "材料科学基础", 
    "英语", "有机化学", "纳米材料学", "文献阅读"
]

# --- 辅助函数 ---
def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Subject", "Duration_Minutes", "Start_Time", "End_Time"])
    
    if not os.path.exists(SUBJECT_FILE):
        save_subjects(DEFAULT_SUBJECTS)

def get_subjects():
    if os.path.exists(SUBJECT_FILE):
        try:
            with open(SUBJECT_FILE, 'r', encoding='utf-8') as f:
                subjects = [line.strip() for line in f.readlines()]
            if not subjects: return DEFAULT_SUBJECTS
            return subjects
        except:
            return DEFAULT_SUBJECTS
    return DEFAULT_SUBJECTS

def save_subjects(subject_list):
    with open(SUBJECT_FILE, 'w', encoding='utf-8') as f:
        for sub in subject_list:
            f.write(sub + "\n")

def add_new_subject(new_sub):
    current_subs = get_subjects()
    if new_sub and new_sub not in current_subs:
        current_subs.append(new_sub)
        save_subjects(current_subs)
        return True
    return False

def save_record(subject, duration, start_dt, end_dt=None):
    if end_dt is None:
        end_dt = datetime.datetime.now()
    if not os.path.exists(DATA_FILE):
        init_files()
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            start_dt.strftime("%Y-%m-%d"), subject, round(duration, 2),
            start_dt.strftime("%H:%M:%S"), end_dt.strftime("%H:%M:%S")
        ])

def get_level(total_minutes):
    hours = total_minutes / 60
    if hours < 5: return "Lv.1 实验室萌新", hours
    if hours < 20: return "Lv.2 试管清洗员", hours
    if hours < 50: return "Lv.3 文献搬运工", hours
    if hours < 100: return "Lv.4 核心发刊人", hours
    return "Lv.MAX 院士候选人", hours

# --- 初始化 ---
init_files()
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = DEFAULT_SUBJECTS[0]

# --- 侧边栏 ---
st.sidebar.title("🧪 科研计时器")
page = st.sidebar.radio("前往", ["⏱️ 专注打卡", "📊 数据看板", "☁️ 数据备份与管理"]) 

# 读取数据
df = pd.DataFrame()
if os.path.exists(DATA_FILE):
    try: df = pd.read_csv(DATA_FILE)
    except: pass

total_mins = df['Duration_Minutes'].sum() if not df.empty else 0
level_name, total_hrs = get_level(total_mins)

st.sidebar.markdown("---")
st.sidebar.metric("当前头衔", level_name)
st.sidebar.metric("累计科研时长", f"{total_hrs:.1f} h")

# --- 页面 1: 专注打卡 ---
if page == "⏱️ 专注打卡":
    st.title(":stopwatch: 沉浸式学习")
    subject_list = get_subjects()
    col1, col2 = st.columns(2)
    with col1: subject = st.selectbox("选择科目", subject_list)
    with col2: mode = st.radio("模式", ["普通计时", "番茄钟 (25min)"])
    
    with st.expander("➕ 添加新学科"):
        new_sub = st.text_input("输入新学科:")
        if st.button("添加"):
            if add_new_subject(new_sub):
                st.success(f"已添加: {new_sub}")
                time.sleep(1)
                st.rerun()

    st.divider()
    is_pomodoro = "番茄" in mode
    placeholder = st.empty()
    btn_placeholder = st.empty()

    if not st.session_state.is_running:
        placeholder.markdown(f"<h1 style='text-align: center; color: #ddd; font-size: 80px;'>00:00</h1>", unsafe_allow_html=True)
        if btn_placeholder.button("开始专注", icon="🚀", use_container_width=True, type="primary"):
            st.session_state.is_running = True
            st.session_state.start_time = datetime.datetime.now()
            st.session_state.selected_subject = subject
            st.rerun()
    else:
        now = datetime.datetime.now()
        elapsed = int((now - st.session_state.start_time).total_seconds())
        if is_pomodoro:
            remaining = (POMODORO_MINUTES * 60) - elapsed
            if remaining <= 0:
                st.session_state.is_running = False
                save_record(st.session_state.selected_subject, POMODORO_MINUTES, st.session_state.start_time)
                st.balloons()
                st.success("番茄钟完成！")
                time.sleep(3)
                st.rerun()
            display_sec = max(0, remaining)
            color = "#ff4b4b"
        else:
            display_sec = elapsed
            color = "#333"
        
        m, s = divmod(display_sec, 60)
        h, m = divmod(m, 60)
        placeholder.markdown(f"<h1 style='text-align: center; color: {color}; font-size: 80px;'>{h:02}:{m:02}:{s:02}</h1>", unsafe_allow_html=True)
        placeholder.markdown(f"<p style='text-align:center'>正在学习: {st.session_state.selected_subject}</p>", unsafe_allow_html=True)
        
        if btn_placeholder.button("结束 / 放弃", icon="🛑", use_container_width=True):
            st.session_state.is_running = False
            dur = elapsed / 60
            save_record(st.session_state.selected_subject, dur, st.session_state.start_time)
            st.success(f"已记录: {dur:.1f} min")
            time.sleep(1)
            st.rerun()
        time.sleep(1)
        st.rerun()

# --- 页面 2: 数据看板 ---
elif page == "📊 数据看板":
    st.title(":bar_chart: 学习数据分析")
    if df.empty:
        st.info("暂无数据")
    else:
        df['Date'] = pd.to_datetime(df['Date'])
        if 'Start_Time' in df.columns:
            df['Start_Full'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Start_Time'])
            df['End_Full'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['End_Time'])
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_mins = df[df['Date'].dt.strftime("%Y-%m-%d") == today]['Duration_Minutes'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("今日投入", f"{today_mins:.0f} min")
        c2.metric("累计专注", f"{df['Duration_Minutes'].sum()/60:.1f} h")
        c3.metric("记录次数", f"{len(df)}")
        
        st.subheader("学科投入占比")
        pie_data = df.groupby('Subject')['Duration_Minutes'].sum().reset_index()
        fig = px.pie(pie_data, values='Duration_Minutes', names='Subject', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("近7天日程表")
        end = datetime.datetime.now().date()
        start = end - datetime.timedelta(days=6)
        mask = (df['Date'].dt.date >= start) & (df['Date'].dt.date <= end)
        rec_df = df.loc[mask].copy()
        if not rec_df.empty and 'Start_Full' in rec_df.columns:
            fig2 = px.timeline(rec_df, x_start="Start_Full", x_end="End_Full", y="Date", color="Subject", height=400)
            fig2.update_yaxes(categoryorder="category descending")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("近7天无记录")

# --- 页面 3: 备份与管理 (关键修改) ---
elif page == "☁️ 数据备份与管理":
    st.title("☁️ 云端数据管理")
    st.info("⚠️ 重要：云端服务器重启后数据会重置。请定期点击下方按钮下载备份 CSV 文件！")
    
    tab1, tab2 = st.tabs(["📤 备份与恢复", "🛠️ 数据修正"])
    
    with tab1:
        st.subheader("1. 下载备份 (推荐每天结束时点一下)")
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                st.download_button("📥 点击下载 study_log.csv", f, file_name="study_log.csv", mime="text/csv", type="primary")
        else:
            st.warning("暂无数据可下载")
            
        st.subheader("2. 恢复数据 (上传之前的备份)")
        uploaded_file = st.file_uploader("将你之前下载的 CSV 拖到这里", type="csv")
        if uploaded_file is not None:
            if st.button("确认覆盖当前数据"):
                # 读取上传的文件并保存到服务器本地
                df_upload = pd.read_csv(uploaded_file)
                df_upload.to_csv(DATA_FILE, index=False)
                st.success("数据恢复成功！")
                time.sleep(1)
                st.rerun()

    with tab2:
        st.subheader("编辑当前数据")
        if not df.empty:
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("💾 保存修改"):
                edited_df.to_csv(DATA_FILE, index=False)
                st.success("已保存")
                time.sleep(1)
                st.rerun()