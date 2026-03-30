import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="안정성 테스트 대시보드", layout="wide")
st.title("화장품 시제품 안정성 테스트 대시보드")

# --- 파일 업로드 ---
uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("왼쪽 사이드바에서 엑셀 파일을 업로드해주세요.")
    st.stop()

# --- 데이터 로드 ---
xl = pd.ExcelFile(uploaded_file)
df_product = pd.read_excel(xl, sheet_name=xl.sheet_names[0])
df_test = pd.read_excel(xl, sheet_name=xl.sheet_names[1])

# 시제품코드 기준 병합
df_merged = df_test.merge(df_product, on="시제품코드", how="left")

# --- 사이드바 필터 ---
st.sidebar.markdown("---")
st.sidebar.header("필터")

product_types = st.sidebar.multiselect(
    "제품유형", df_product["제품유형"].unique(), default=df_product["제품유형"].unique()
)
test_conditions = st.sidebar.multiselect(
    "테스트조건", df_test["테스트조건"].unique(), default=df_test["테스트조건"].unique()
)
results_filter = st.sidebar.multiselect(
    "판정결과", df_test["판정결과"].unique(), default=df_test["판정결과"].unique()
)

# 필터 적용
selected_products = df_product[df_product["제품유형"].isin(product_types)]["시제품코드"]
df_filtered = df_merged[
    (df_merged["시제품코드"].isin(selected_products))
    & (df_merged["테스트조건"].isin(test_conditions))
    & (df_merged["판정결과"].isin(results_filter))
]

# --- KPI 카드 ---
st.markdown("### 주요 지표")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("시제품 수", f"{df_product[df_product['제품유형'].isin(product_types)].shape[0]}건")
col2.metric("테스트 건수", f"{len(df_filtered)}건")
col3.metric("적합 비율", f"{(df_filtered['판정결과'] == '적합').mean() * 100:.1f}%")
col4.metric("평균 pH", f"{df_filtered['pH'].mean():.2f}")
col5.metric("평균 점도", f"{df_filtered['점도_cP'].mean():,.0f} cP")

st.markdown("---")

# --- 1행: 판정결과 & 테스트조건 ---
row1_left, row1_right = st.columns(2)

with row1_left:
    st.subheader("판정결과 분포")
    result_counts = df_filtered["판정결과"].value_counts().reset_index()
    result_counts.columns = ["판정결과", "건수"]
    color_map = {"적합": "#2ecc71", "경미변화": "#f39c12", "재검토": "#e74c3c"}
    fig = px.pie(result_counts, names="판정결과", values="건수", color="판정결과",
                 color_discrete_map=color_map, hole=0.4)
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with row1_right:
    st.subheader("테스트조건별 판정결과")
    ct = pd.crosstab(df_filtered["테스트조건"], df_filtered["판정결과"])
    fig = px.bar(ct, barmode="stack", color_discrete_map=color_map)
    fig.update_layout(xaxis_title="테스트조건", yaxis_title="건수", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- 2행: pH & 점도 ---
row2_left, row2_right = st.columns(2)

with row2_left:
    st.subheader("시제품별 pH 분포")
    fig = px.box(df_filtered, x="시제품코드", y="pH", color="테스트조건",
                 points="all")
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with row2_right:
    st.subheader("시제품별 점도 분포")
    fig = px.box(df_filtered, x="시제품코드", y="점도_cP", color="테스트조건",
                 points="all")
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- 3행: 보관기간별 추이 & 이상항목 ---
row3_left, row3_right = st.columns(2)

with row3_left:
    st.subheader("보관기간별 pH 변화 추이")
    fig = px.line(
        df_filtered.sort_values("보관기간_주"),
        x="보관기간_주", y="pH", color="시제품코드",
        markers=True,
    )
    fig.update_layout(xaxis_title="보관기간(주)", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with row3_right:
    st.subheader("보관기간별 점도 변화 추이")
    fig = px.line(
        df_filtered.sort_values("보관기간_주"),
        x="보관기간_주", y="점도_cP", color="시제품코드",
        markers=True,
    )
    fig.update_layout(xaxis_title="보관기간(주)", yaxis_title="점도(cP)", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- 4행: 향변화/분리현상 히트맵 & 담당팀별 ---
row4_left, row4_right = st.columns(2)

with row4_left:
    st.subheader("시제품별 이상 항목 현황")
    anomaly = df_filtered.groupby("시제품코드").agg(
        향변화=("향변화여부", lambda x: (x == "Y").sum()),
        분리현상=("분리현상여부", lambda x: (x == "Y").sum()),
        색상변화_평균등급=("색상변화등급", "mean"),
    ).reset_index()
    fig = px.bar(anomaly.melt(id_vars="시제품코드", value_vars=["향변화", "분리현상"]),
                 x="시제품코드", y="value", color="variable", barmode="group",
                 labels={"value": "발생 건수", "variable": "이상 항목"})
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with row4_right:
    st.subheader("담당팀별 판정결과")
    team_result = pd.crosstab(df_filtered["담당팀"], df_filtered["판정결과"])
    fig = px.bar(team_result, barmode="stack", color_discrete_map=color_map)
    fig.update_layout(xaxis_title="담당팀", yaxis_title="건수", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- 상세 데이터 테이블 ---
st.markdown("---")
st.subheader("상세 데이터")

tab1, tab2 = st.tabs(["안정성 테스트 결과", "시제품 정보"])

with tab1:
    st.dataframe(df_filtered.drop(columns=df_product.columns.difference(["시제품코드"]), errors="ignore"),
                 use_container_width=True, hide_index=True)

with tab2:
    st.dataframe(df_product[df_product["제품유형"].isin(product_types)],
                 use_container_width=True, hide_index=True)
