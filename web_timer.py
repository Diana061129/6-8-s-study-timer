import streamlit as st
import pandas as pd
import datetime
import time
import os
import csv
import plotly.express as px
import plotly.graph_objects as go # 引入更底层的绘图库以实现复杂日历视图

# ==========================================
# 1. 页面配置与 iOS 风格 CSS + 精美壁纸
# ==========================================
st.set_page_config(page_title="iStudy OS", page_icon="🍎", layout="centered")

# --- 配置区 ---
DATA_FILE = "study_log.csv"
SUBJECT_FILE = "subjects.txt"
POMODORO_MINUTES = 25

# 定义 iOS 风格配色
IOS_COLORS = {
    "概率论与数理统计": "#FF3B30", "物理化学": "#007AFF", "材料科学基础": "#34C759",
    "英语": "#FF9500", "有机化学": "#AF52DE", "纳米材料学": "#5856D6",
    "文献阅读": "#5AC8FA", "其他": "#8E8E93"
}
DEFAULT_SUBJECTS = list(IOS_COLORS.keys())[:-1]

# 注入 CSS (壁纸 + iOS字体)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500&display=swap');
    
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1497633762265-9d179a990aa6?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    [data-testid="stMainBlockContainer"] {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-top: 20px;
        margin-bottom: 20px;
    }

    html, body, [class*="css"] {
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
        background: transparent;
    }
    
    .timer-text {
        font-family: 'Roboto', sans-serif; font-weight: 100; font-size: 90px;
        color: #333; text-align: center; line-height: 1; margin-top: 20px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .subject-badge {
        background-color: #f2f2f7; color: #8e8e93; padding: 5px 15px;
        border-radius: 20px; font-size: 14px; text-align: center;
        margin-bottom: 10px; display: inline-block;
    }
    .stButton>button {
        border-radius: 12px; height: 50px; font-weight: 500; border: none;
        transition: transform 0.1s;
    }
    .stButton>button:active { transform: scale(0.98); }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 辅助函数
# ==========================================
def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Subject", "Duration_Minutes", "Start_Time", "End_Time"])
    if not os.path.exists(SUBJECT_FILE): save_subjects(DEFAULT_SUBJECTS)

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

# --- PAGE 1: 专注计时 ---
if page == "专注计时":
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown(f"### {datetime.datetime.now().strftime('%A, %B %d')}")
    with col2:
        total_hrs = df['Duration_Minutes'].sum()/60 if not df.empty else 0.0
        st.caption(f"本周累计: {total_hrs:.1f}h")
    st.markdown("---")

    if not st.session_state.is_running:
        subject_list = get_subjects()
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2:
            subject = st.selectbox("选择当前专注内容", subject_list)
            mode = st.radio("计时模式", ["普通计时", "番茄钟 (25min)"], horizontal=True)
            st.session_state.timer_mode = mode
            st.write(""); st.write("")
            if st.button("开始专注", use_container_width=True, type="primary"):
                st.session_state.is_running = True
                st.session_state.start_time = datetime.datetime.now()
                st.session_state.selected_subject = subject
                st.rerun()
            with st.expander("自定义学科"):
                new_sub = st.text_input("输入名称")
                if st.button("添加"):
                    add_new_subject(new_sub)
                    st.rerun()
    else:
        now = datetime.datetime.now()
        start = st.session_state.start_time
        elapsed_seconds = int((now - start).total_seconds())
        is_pomodoro = "番茄" in st.session_state.timer_mode
        current_sub = st.session_state.selected_subject
        
        if is_pomodoro:
            total_seconds = POMODORO_MINUTES * 60
            remaining = total_seconds - elapsed_seconds
            progress = max(0, min(1.0, elapsed_seconds / total_seconds))
            if remaining <= 0:
                st.session_state.is_running = False
                save_record(current_sub, POMODORO_MINUTES, start)
                st.balloons(); st.success("🎉 番茄钟完成！"); time.sleep(3); st.rerun()
            display_seconds = max(0, remaining)
            time_color = "#FF3B30"
        else:
            progress = min(1.0, (elapsed_seconds % 3600) / 3600) 
            display_seconds = elapsed_seconds
            time_color = "#333333"

        m, s = divmod(display_seconds, 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

        st.progress(progress)
        st.markdown(f"<div style='text-align:center'><span class='subject-badge'>{current_sub}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='timer-text' style='color:{time_color}'>{time_str}</div>", unsafe_allow_html=True)
        if is_pomodoro: st.markdown("<p style='text-align:center; color:#888'>保持专注，不要切屏</p>", unsafe_allow_html=True)
        
        st.write("")
        if st.button("停止 / 结束", use_container_width=True):
            st.session_state.is_running = False
            duration = elapsed_seconds / 60
            save_record(current_sub, duration, start)
            st.toast(f"已记录: {duration:.1f} 分钟"); time.sleep(1); st.rerun()
        time.sleep(1); st.rerun()

# --- PAGE 2: 数据日历 ---
elif page == "数据日历":
    st.title("📊 学习日历")
    
    tab_viz, tab_manage = st.tabs(["📅 可视化报表", "🛠️ 记录管理 (补录/修改)"])
    
    # === Tab 1: 可视化 (核心修改区域) ===
    with tab_viz:
        if df.empty:
            st.info("暂无数据，快去开始你的第一次专注吧！")
        else:
            # 数据预处理
            df['Date_Obj'] = pd.to_datetime(df['Date'])
            if 'Start_Time' in df.columns:
                df['Start_Full'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Start_Time'])
                df['End_Full'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['End_Time'])
            
            st.subheader("投入分布")
            pie_data = df.groupby('Subject')['Duration_Minutes'].sum().reset_index()
            fig_pie = px.pie(pie_data, values='Duration_Minutes', names='Subject', 
                             color='Subject', color_discrete_map=IOS_COLORS, hole=0.6)
            fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

            st.subheader("时间轴视图 (近7天)")
            
            # 1. 数据筛选与准备
            end = datetime.datetime.now().date()
            start = end - datetime.timedelta(days=6) # 显示一周
            mask = (df['Date_Obj'].dt.date >= start) & (df['Date_Obj'].dt.date <= end)
            rec_df = df.loc[mask].copy()
            
            if not rec_df.empty and 'Start_Full' in rec_df.columns:
                # 关键步骤：计算距离午夜的分钟数，作为Y轴定位
                rec_df['Start_Minute'] = rec_df['Start_Full'].dt.hour * 60 + rec_df['Start_Full'].dt.minute
                # 格式化日期显示
                rec_df['Date_Str'] = rec_df['Date_Obj'].dt.strftime('%m-%d %a')
                
                # 2. 使用 Graph Objects 构建自定义图表
                fig = go.Figure()

                # 为每个科目添加一个柱状图层 (Bar Trace)
                for subject in rec_df['Subject'].unique():
                    subject_data = rec_df[rec_df['Subject'] == subject]
                    color = IOS_COLORS.get(subject, "#8E8E93")
                    
                    fig.add_trace(go.Bar(
                        x=subject_data['Date_Str'], # X轴：日期
                        y=subject_data['Duration_Minutes'], # Y轴高度：持续时长
                        base=subject_data['Start_Minute'], # Y轴起始位置：开始时间(分钟)
                        name=subject,
                        marker_color=color,
                        hoverinfo="x+y+name",
                        hovertemplate=
                        "<b>%{x}</b><br>" +
                        "科目: %{data.name}<br>" +
                        "时长: %{y} 分钟<br>" +
                        "<extra></extra>" # 隐藏额外的trace信息
                    ))

                # 3. 配置 Y 轴刻度 (显示为 HH:MM 格式)
                tick_vals = list(range(0, 24 * 60 + 1, 60)) # 每小时一个刻度 (0, 60, 120...)
                tick_text = [f"{h:02d}:00" for h in range(25)] # 对应文本 (00:00, 01:00...)

                # 4. 配置整体布局，模仿 iOS 日历
                fig.update_layout(
                    barmode='stack', # 虽然是stack，但配合base使用变成了悬浮条形图
                    yaxis=dict(
                        title="",
                        range=[24*60, 0], # 关键：倒序显示，0点在最上面，24点在最下面
                        tickmode='array',
                        tickvals=tick_vals,
                        ticktext=tick_text,
                        showgrid=True,
                        gridcolor='#f0f0f0',
                        zeroline=False
                    ),
                    xaxis=dict(
                        title="",
                        type='category', # 保证日期按顺序排列
                        categoryorder='array',
                        categoryarray=sorted(rec_df['Date_Str'].unique()),
                        showgrid=False
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=600, # 增加高度让时间轴更清晰
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=60, r=20, t=40, b=40) # 调整边距以显示完整的Y轴标签
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                 st.info("近7天无详细记录")

    # === Tab 2: 记录管理 ===
    with tab_manage:
        st.subheader("✍️ 手动补录")
        with st.form("manual_add"):
            c1, c2 = st.columns(2)
            with c1:
                add_date = st.date_input("日期", datetime.date.today())
                add_subject = st.selectbox("科目", get_subjects())
            with c2:
                add_start = st.time_input("开始时间", datetime.time(9, 00))
                add_end = st.time_input("结束时间", datetime.time(10, 00))
            if st.form_submit_button("确认补录"):
                start_dt = datetime.datetime.combine(add_date, add_start)
                end_dt = datetime.datetime.combine(add_date, add_end)
                if end_dt <= start_dt: st.error("结束时间需晚于开始时间")
                else:
                    dur = (end_dt - start_dt).total_seconds() / 60
                    save_record(add_subject, dur, start_dt, end_dt)
                    st.success(f"已补录: {dur:.1f}分钟"); time.sleep(1); st.rerun()
        
        st.divider()
        st.subheader("📝 修改/删除已有记录")
        if df.empty: st.info("暂无数据可编辑")
        else:
            st.caption("提示：直接双击单元格修改，勾选行左侧并按 Delete 键删除。完成后务必点击下方保存按钮。")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor_v6")
            if st.button("💾 保存所有变动", type="primary"):
                edited_df.to_csv(DATA_FILE, index=False); st.success("已保存！"); time.sleep(1); st.rerun()

# --- PAGE 3: 备份 ---
elif page == "云端备份":
    st.title("☁️ 数据同步")
    st.info("提示：请定期下载备份，以免服务器重启导致数据丢失。")
    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f: st.download_button("📥 导出数据 (CSV)", f, "study_backup.csv", "text/csv", type="primary", use_container_width=True)
    with col2:
        uploaded_file = st.file_uploader("恢复数据", type="csv", label_visibility="collapsed")
        if uploaded_file and st.button("覆盖恢复"):
            pd.read_csv(uploaded_file).to_csv(DATA_FILE, index=False); st.success("成功！"); time.sleep(1); st.rerun()
