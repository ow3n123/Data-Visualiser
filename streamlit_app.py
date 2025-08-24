import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from tkinter import Tk, filedialog


def pick_directory():
    """Open a dialog to pick a directory using tkinter."""
    root = Tk()
    root.withdraw()  # hide main window
    folder = filedialog.askdirectory(title="Select Data Directory")
    root.destroy()
    return folder


def list_transformers(data_dir):
    return [f for f in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, f))]


def list_customer_files(data_dir, transformer):
    path = os.path.join(data_dir, transformer)
    return [f for f in os.listdir(path) if f.endswith(".csv")]

def parse_filename(filename):
    """Split into customer ID and category."""
    customer, category = filename.split("_", 1)
    category = category.replace(".csv", "")
    return customer, category

def load_customer_data(data_dir, transformer, filename):
    filepath = os.path.join(data_dir, transformer, filename)
    df = pd.read_csv(filepath, header=None, names=["Datetime", "Value"], parse_dates=["Datetime"])
    df["Datetime"] = pd.to_datetime(df["Datetime"]).dt.tz_localize(None)
    return df


def main():
    st.title("Phase Identification Data Visualiser Streamlit")

    # Pick or input root directory
    if "data_dir" not in st.session_state:
        st.session_state.data_dir = ""

    st.sidebar.subheader("Data Directory")
    if st.sidebar.button("Browse for Folder"):
        folder = pick_directory()
        if folder:
            st.session_state.data_dir = folder

    data_dir = st.sidebar.text_input("Or enter path manually", st.session_state.data_dir)

    if data_dir and os.path.isdir(data_dir):
        transformers = list_transformers(data_dir)
        transformer = st.selectbox("Select Transformer", transformers)

        if transformer:
            files = list_customer_files(data_dir, transformer)
            if files:
                # Build mapping customer -> categories
                file_map = {}
                categories = set()
                for f in files:
                    cust, cat = parse_filename(f)
                    categories.add(cat)
                    file_map.setdefault(cust, {})[cat] = f

                # Step 1: Select categories
                selected_categories = st.multiselect("Select Categories", sorted(categories))

                if selected_categories:
                    # Step 2: Select customers that have all selected categories
                    eligible_customers = sorted(
                        [cust for cust, cats in file_map.items() if all(cat in cats for cat in selected_categories)],
                        key=lambda x: int(x) if x.isdigit() else x
                    )
                    selected_customers = st.multiselect("Select Customers", eligible_customers)

                    if selected_customers:
                        dfs = []
                        min_dates, max_dates = [], []

                        for cust in selected_customers:
                            for cat in selected_categories:
                                file = file_map[cust][cat]
                                df = load_customer_data(data_dir, transformer, file)
                                dfs.append((cust, cat, df))
                                min_dates.append(df["Datetime"].min())
                                max_dates.append(df["Datetime"].max())

                        # overall min/max across all
                        min_date, max_date = min(min_dates), max(max_dates)
                        start_date, end_date = st.date_input(
                            "Select Date Range",
                            [min_date, max_date],
                            min_value=min_date,
                            max_value=max_date
                        )

                        # Plot
                        fig, ax = plt.subplots(figsize=(12, 6))
                        for cust, cat, df in dfs:
                            mask = (df["Datetime"] >= pd.to_datetime(start_date)) & (df["Datetime"] <= pd.to_datetime(end_date))
                            filtered_df = df.loc[mask].sort_values("Datetime")
                            ax.plot(filtered_df["Datetime"], filtered_df["Value"], label=f"{cust}_{cat}")

                        ax.set_title(f"{transformer} Data")
                        ax.set_xlabel("Datetime")
                        ax.set_ylabel("Value")
                        ax.legend()
                        st.pyplot(fig)

    else:
        st.warning("Please select a valid data directory.")

if __name__ == "__main__":
    main()
