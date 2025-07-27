import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import pycountry
import re

# -------------------
# PAGE CONFIGURATION
# -------------------
st.set_page_config(page_title="AI Job Dataset Explorer", layout="wide")
st.title("📊 AI Job Dataset Interactive Explorer")

# -------------------
# DATA UPLOAD
# -------------------
uploaded_file = st.file_uploader("Upload your ai_job_dataset.csv", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Data Loaded Successfully")

    # Clean & Tokenize required_skills
    df['required_skills'] = df['required_skills'].fillna('')
    df['skill_list'] = df['required_skills'].apply(lambda x: [s.strip().lower() for s in re.sub(r'[^\w,\s]', '', x).split(',') if s.strip()])
    df['posting_date'] = pd.to_datetime(df['posting_date'])
    df['month'] = df['posting_date'].dt.to_period('M').astype(str)
    df_exploded = df.explode('skill_list')

    st.sidebar.header("Filter Options")
    top_skills = df_exploded['skill_list'].value_counts().head(10).index.tolist()
    tracked_skills = st.sidebar.multiselect("Select skills to track:", options=top_skills, default=top_skills[:5])

    st.header("1️⃣ Top 20 Most Common Skills")
    all_skills = [skill for skills in df['skill_list'] for skill in skills]
    skill_freq = Counter(all_skills)
    top_20 = skill_freq.most_common(20)
    skills, counts = zip(*top_20)
    fig_bar = px.bar(x=counts, y=skills, orientation='h', labels={'x':'Frequency','y':'Skill'}, title="Top 20 Most Common Skills")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.header("2️⃣ Word Cloud of Skills")
    wordcloud = WordCloud(width=1000, height=500, background_color='white').generate_from_frequencies(skill_freq)
    fig_wc, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig_wc)

    st.header("3️⃣ Skill Demand Trends Over Time")
    monthly_skill_counts = df_exploded[df_exploded['skill_list'].isin(tracked_skills)]\
        .groupby(['month','skill_list']).size().reset_index(name='count')
    fig_trend = px.line(monthly_skill_counts, x='month', y='count', color='skill_list', markers=True,
                        labels={'month':'Month', 'count':'Mentions'},
                        title='Skill Demand Over Time')
    st.plotly_chart(fig_trend, use_container_width=True)

    st.header("4️⃣ Salary Distribution by Top Skills")
    df_salary = df_exploded[df_exploded['skill_list'].isin(tracked_skills)]
    fig_box = px.box(df_salary, x='skill_list', y='salary_usd', points='all', color='skill_list',
                     title='Salary Distribution by Skill', labels={'skill_list':'Skill','salary_usd':'Salary (USD)'})
    st.plotly_chart(fig_box, use_container_width=True)

    st.header("5️⃣ Skill Frequency by Country")
    def get_alpha3(name):
        try:
            return pycountry.countries.search_fuzzy(name)[0].alpha_3
        except:
            return None
    country_skill = df_exploded[df_exploded['skill_list'].isin(tracked_skills)]\
        .groupby(['employee_residence','skill_list']).size().reset_index(name='count')
    country_skill['iso_alpha'] = country_skill['employee_residence'].apply(get_alpha3)
    for skill in tracked_skills:
        data_skill = country_skill[country_skill['skill_list']==skill].dropna(subset=['iso_alpha'])
        fig_map = px.choropleth(data_skill, locations='iso_alpha', color='count', hover_name='employee_residence',
                                 title=f"Global Demand for '{skill.title()}' Skill", color_continuous_scale='Viridis')
        st.plotly_chart(fig_map, use_container_width=True)

    st.success("✅ Dashboard Ready. Use sidebar to adjust tracked skills.")

else:
    st.info("👈 Upload your ai_job_dataset.csv file to begin exploring interactively.")


