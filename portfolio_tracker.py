# portfolio_tracker.py
import streamlit as st
import pandas as pd
import yfinance as yf
from pathlib import Path

st.set_page_config(page_title="Portfolio Tracker", layout="wide")
st.title("📈 Portfolio Tracker (Streamlit)")

DATA_DIR = Path("sample_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "portfolio.csv"

# Load existing portfolio if available
if CSV_PATH.exists():
    try:
        portfolio_df = pd.read_csv(CSV_PATH)
    except Exception:
        portfolio_df = pd.DataFrame(columns=["Ticker","Quantity","BuyPrice"])
else:
    portfolio_df = pd.DataFrame(columns=["Ticker","Quantity","BuyPrice"])

# Sidebar: add or upload
st.sidebar.header("Add / Upload Portfolio")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_ticker = st.text_input("Ticker (e.g. AAPL or RELIANCE.NS)").upper().strip()
    new_qty = st.number_input("Quantity", min_value=1, step=1)
    new_buy = st.number_input("Buy Price", min_value=0.0, format="%.2f")
    add_btn = st.form_submit_button("Add to Portfolio")
if add_btn and new_ticker:
    portfolio_df = portfolio_df.append({"Ticker": new_ticker, "Quantity": new_qty, "BuyPrice": new_buy}, ignore_index=True)
    st.success(f"Added {new_ticker}")

uploaded = st.sidebar.file_uploader("Upload portfolio CSV", type="csv")
if uploaded:
    try:
        uploaded_df = pd.read_csv(uploaded)
        portfolio_df = uploaded_df
        st.sidebar.success("CSV loaded")
    except Exception as e:
        st.sidebar.error("Failed to read CSV: " + str(e))

# Save button (persist locally)
if st.sidebar.button("Save portfolio to sample_data/portfolio.csv"):
    portfolio_df.to_csv(CSV_PATH, index=False)
    st.sidebar.success("Saved")

st.sidebar.markdown("---")
st.sidebar.write("Sample CSV format: `Ticker,Quantity,BuyPrice`")
st.sidebar.write("Example: `RELIANCE.NS,8,2500`")

# Main area: show portfolio table and metrics
st.subheader("📊 Portfolio")
if portfolio_df.empty:
    st.info("No holdings yet. Add in the sidebar or upload a CSV with columns Ticker,Quantity,BuyPrice.")
else:
    # Ensure proper types
    portfolio_df["Quantity"] = pd.to_numeric(portfolio_df["Quantity"], errors="coerce").fillna(0).astype(int)
    portfolio_df["BuyPrice"] = pd.to_numeric(portfolio_df["BuyPrice"], errors="coerce").fillna(0.0)

    # Fetch latest prices
    tickers = portfolio_df["Ticker"].tolist()
    latest_prices = {}
    for t in tickers:
        try:
            data = yf.Ticker(t).history(period="1d")
            if not data.empty:
                latest_prices[t] = data["Close"].iloc[-1]
            else:
                latest_prices[t] = None
        except Exception:
            latest_prices[t] = None

    portfolio_df["CurrentPrice"] = portfolio_df["Ticker"].map(latest_prices)
    portfolio_df["CurrentValue"] = portfolio_df["Quantity"] * portfolio_df["CurrentPrice"]
    portfolio_df["Investment"] = portfolio_df["Quantity"] * portfolio_df["BuyPrice"]
    portfolio_df["P/L"] = portfolio_df["CurrentValue"] - portfolio_df["Investment"]
    portfolio_df["%Change"] = (portfolio_df["P/L"] / portfolio_df["Investment"]) * 100

    # Display nicely
    display_df = portfolio_df.fillna("-")
    st.dataframe(display_df.style.format({
        "BuyPrice":"{:.2f}",
        "CurrentPrice":"{:.2f}",
        "CurrentValue":"{:.2f}",
        "Investment":"{:.2f}",
        "P/L":"{:.2f}",
        "%Change":"{:.2f}%"
    }))

    # Totals
    total_investment = portfolio_df["Investment"].sum()
    total_value = portfolio_df["CurrentValue"].sum()
    total_pl = portfolio_df["P/L"].sum()
    total_change = (total_pl / total_investment) * 100 if total_investment else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Investment", f"{total_investment:,.2f}")
    col2.metric("📈 Total Value", f"{total_value:,.2f}")
    col3.metric("📊 Total P/L", f"{total_pl:,.2f} ({total_change:.2f}%)")

    # Simple bar chart
    st.subheader("Allocation: Investment vs Current Value")
    chart_df = portfolio_df.set_index("Ticker")[["Investment","CurrentValue"]].fillna(0)
    st.bar_chart(chart_df)

