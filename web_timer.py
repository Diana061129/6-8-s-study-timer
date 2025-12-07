import streamlit as st
import pandas as pd
import datetime
import time
import os
import csv
import plotly.express as px

# ==========================================
# 1. 页面配置与 iOS 风格 CSS
# ==========================================
st.set_page_config(page_title="iStudy OS", page_icon="🍎", layout="centered")

# 定义 iOS 风格配色字典
IOS_COLORS = {
    "概率论与数理统计": "#FF3B30", # Red
    "物理化学": "#007AFF",       # Blue
    "材料科学基础": "#34C759",   # Green
    "英语": "#FF9500",           # Orange
    "有机化学": "#AF52DE",       # Purple
    "纳米材料学": "#5856D6",     # Indigo
    "文献阅读": "#5AC8FA",       # Teal
    "其他": "#8E8E93"           # Gray
}

# 注入 CSS (实现 iOS 锁屏字体和毛玻璃效果)
st.markdown("""
    <style>
    /* 引入类似 San Francisco 的字体 */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 计时器大数字样式 */
    .timer-text {
        font-family: 'Roboto', sans-serif;
        font-weight: 100;
        font-size: 90px;
        color: #333;
        text-align: center;
        line-height: 1;
        margin-top: 20px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* 科目胶囊样式 */
    .subject-badge {
        background-color: #f2f2f7;
        color: #8e8e93;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        text-align: center;
        margin-bottom: 10px;
        display: inline-block;
    }
    
    /* 按钮美化 */
    .stButton>button {
        border-radius: 12px;
        height: 50px;
        font-weight: 500;
        border: none;
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }
    
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 数据管理 (云端兼容)
# ==========================================
DATA_FILE = "study_log.csv"
SUBJECT_FILE = "subjects.txt"
POMODORO_MINUTES = 25

# 预设学科
DEFAULT_SUBJECTS = list(IOS_COLORS.keys())[:-1] # 去掉"其他"

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
            return subjects if subjects else DEFAULT_SUBJECTS
        except: return DEFAULT_SUBJECTS
    return DEFAULT_SUBJECTS

def save_subjects(subject_list):
    with open(SUBJECT_FILE, 'w', encoding='utf-8') as f:
        for sub in subject_list: f.write(sub + "\n")

def add_new_subject(new_sub):
    current_subs = get_subjects()
    if new_sub and new_sub not in current_subs:
        current_subs.append(new_sub)
        save_subjects(current_subs)
        return True
    return False

def save_record(subject, duration, start_dt, end_dt=None):
    if end_dt is None: end_dt = datetime.datetime.now()
    if not os.path.exists(DATA_FILE): init_files()
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            start_dt.strftime("%Y-%m-%d"), subject, round(duration, 2),
            start_dt.strftime("%H:%M:%S"), end_dt.strftime("%H:%M:%S")
        ])

# ==========================================
# 3. 核心逻辑
# ==========================================
init_files()

# 初始化 Session State
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = DEFAULT_SUBJECTS[0]
if 'timer_mode' not in st.session_state: st.session_state.timer_mode = "普通计时"

# --- 侧边栏 ---
st.sidebar.header("iStudy OS")
page = st.sidebar.radio("Menu", ["专注计时", "数据日历", "云端备份"])

# 读取数据
df = pd.DataFrame()
if os.path.exists(DATA_FILE):
    try: df = pd.read_csv(DATA_FILE)
    except: pass

# --- PAGE 1: 专注计时 (iOS 风格) ---
if page == "专注计时":
    
    # 顶部状态栏
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {datetime.datetime.now().strftime('%A, %B %d')}")
    with col2:
        # 显示累计小时
        total_hrs = df['Duration_Minutes'].sum()/60 if not df.empty else 0.0
        st.caption(f"本周累计: {total_hrs:.1f}h")

    st.markdown("---")

    # 如果未开始，显示设置界面
    if not st.session_state.is_running:
        subject_list = get_subjects()
        
        # 居中布局
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2:
            subject = st.selectbox("选择当前专注内容", subject_list)
            
            # iOS 风格的分段控制器
            mode = st.radio("计时模式", ["普通计时", "番茄钟 (25min)"], horizontal=True)
            st.session_state.timer_mode = mode
            
            st.write("") # Spacer
            st.write("")
            
            # 巨大的圆形开始按钮
            if st.button("开始专注", use_container_width=True, type="primary"):
                st.session_state.is_running = True
                st.session_state.start_time = datetime.datetime.now()
                st.session_state.selected_subject = subject
                st.rerun() # 立即刷新页面进入计时状态
                
            # 添加新学科折叠区
            with st.expander("自定义学科"):
                new_sub = st.text_input("输入名称")
                if st.button("添加"):
                    add_new_subject(new_sub)
                    st.rerun()

    # 如果正在运行 (计时器核心)
    else:
        # 1. 计算时间
        now = datetime.datetime.now()
        start = st.session_state.start_time
        elapsed_seconds = int((now - start).total_seconds())
        
        is_pomodoro = "番茄" in st.session_state.timer_mode
        current_sub = st.session_state.selected_subject
        
        # 2. 倒计时/正计时逻辑
        if is_pomodoro:
            total_seconds = POMODORO_MINUTES * 60
            remaining = total_seconds - elapsed_seconds
            
            # 进度条 (0.0 - 1.0)
            progress = max(0, min(1.0, elapsed_seconds / total_seconds))
            
            if remaining <= 0:
                # 完成逻辑
                st.session_state.is_running = False
                save_record(current_sub, POMODORO_MINUTES, start)
                st.balloons()
                st.success("🎉 番茄钟完成！休息一下。")
                time.sleep(3)
                st.rerun()
            
            display_seconds = max(0, remaining)
            time_color = "#FF3B30" # 红色
        else:
            # 普通计时无进度条上限，设个伪进度
            progress = min(1.0, (elapsed_seconds % 3600) / 3600) 
            display_seconds = elapsed_seconds
            time_color = "#333333"

        # 格式化时间 HH:MM:SS
        m, s = divmod(display_seconds, 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

        # 3. UI 显示 (iOS 锁屏风格)
        
        # 进度条
        st.progress(progress)
        
        # 科目徽章
        st.markdown(f"<div style='text-align:center'><span class='subject-badge'>{current_sub}</span></div>", unsafe_allow_html=True)
        
        # 巨大的时间显示 (自定义 HTML)
        st.markdown(f"<div class='timer-text' style='color:{time_color}'>{time_str}</div>", unsafe_allow_html=True)
        
        if is_pomodoro:
             st.markdown("<p style='text-align:center; color:#888'>保持专注，不要切屏</p>", unsafe_allow_html=True)
        else:
             st.markdown("<p style='text-align:center; color:#888'>沉浸式学习中...</p>", unsafe_allow_html=True)

        st.write("") # Spacer

        # 停止按钮
        if st.button("停止 / 结束", use_container_width=True):
            st.session_state.is_running = False
            duration = elapsed_seconds / 60
            save_record(current_sub, duration, start)
            st.toast(f"已记录: {duration:.1f} 分钟")
            time.sleep(1)
            st.rerun()

        # 4. 关键：自动刷新机制 (Heartbeat)
        # 这里的 sleep(1) + rerun() 是让网页每秒刷新一次的关键
        time.sleep(1)
        st.rerun()

# --- PAGE 2: 数据日历 (Timeline) ---
elif page == "数据日历":
    st.title("📊 学习日历")
    
    if df.empty:
        st.info("暂无数据")
    else:
        df['Date'] = pd.to_datetime(df['Date'])
        if 'Start_Time' in df.columns:
            df['Start_Full'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Start_Time'])
            df['End_Full'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['End_Time'])
        
        # 1. 饼图
        st.subheader("投入分布")
        pie_data = df.groupby('Subject')['Duration_Minutes'].sum().reset_index()
        # 映射颜色
        pie_data['Color'] = pie_data['Subject'].map(lambda x: IOS_COLORS.get(x, "#8E8E93"))
        
        fig_pie = px.pie(pie_data, values='Duration_Minutes', names='Subject', 
                         color='Subject', color_discrete_map=IOS_COLORS,
                         hole=0.6)
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

        # 2. iOS 风格日程表 (Timeline)
        st.subheader("时间轴")
        
        # 筛选近30天
        end = datetime.datetime.now().date()
        start = end - datetime.timedelta(days=7) # 默认看一周
        mask = (df['Date'].dt.date >= start) & (df['Date'].dt.date <= end)
        rec_df = df.loc[mask].copy()
        
        if not rec_df.empty:
            # 倒序排列，让今天的在最上面
            rec_df = rec_df.sort_values('Date', ascending=False)
            
            fig_gantt = px.timeline(
                rec_df, 
                x_start="Start_Full", 
                x_end="End_Full", 
                y="Date", 
                color="Subject",
                color_discrete_map=IOS_COLORS, # 使用 iOS 配色
                hover_data=["Duration_Minutes"],
                height=400
            )
            
            # 美化图表以接近 iOS 日历
            fig_gantt.update_layout(
                xaxis_title="",
                yaxis_title="",
                plot_bgcolor='white',
                paper_bgcolor='white',
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            # 隐藏网格线，只保留日期
            fig_gantt.update_yaxes(categoryorder='category descending', showgrid=False)
            fig_gantt.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
            
            st.plotly_chart(fig_gantt, use_container_width=True)
            
        # 3. 详细列表
        with st.expander("查看详细记录"):
            st.dataframe(df[['Date', 'Subject', 'Duration_Minutes', 'Start_Time', 'End_Time']].sort_values('Date', ascending=False), use_container_width=True)

# --- PAGE 3: 备份 ---
elif page == "云端备份":
    st.title("☁️ 数据同步")
    st.info("提示：请定期下载备份，以免服务器重启导致数据丢失。")
    
    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                st.download_button("📥 导出数据 (CSV)", f, file_name="study_backup.csv", mime="text/csv", type="primary", use_container_width=True)
    
    with col2:
        uploaded_file = st.file_uploader("恢复数据", type="csv", label_visibility="collapsed")
        if uploaded_file:
            if st.button("覆盖恢复"):
                pd.read_csv(uploaded_file).to_csv(DATA_FILE, index=False)
                st.success("成功！")
                time.sleep(1)
                st.rerun()
