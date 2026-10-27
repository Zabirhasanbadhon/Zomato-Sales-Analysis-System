import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


APP_TITLE = "ZaBir | Zomato Sales Analysis"
DEFAULT_FILE = "Zomato Sales.csv"


class ZomatoSalesApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1600x880")
        self.root.minsize(1024, 650)

        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()
        self.file_path = ""

        self._build_style()
        self._build_ui()

        # Automatically load dataset.csv if it exists beside the program.
        if os.path.exists(DEFAULT_FILE):
            self.load_file(DEFAULT_FILE)

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Card.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)

    def _build_ui(self):
        # Header
        header = ttk.Frame(self.root, padding=(18, 14))
        header.pack(fill="x")

        ttk.Label(header, text="ZaBir | Zomato Sales Analysis", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Interactive restaurant & sales dashboard",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(2, 0))

        # Toolbar
        toolbar = ttk.Frame(self.root, padding=(18, 0, 18, 10))
        toolbar.pack(fill="x")

        ttk.Button(
            toolbar, text="📂 Load dataset.csv",
            command=self.choose_file, style="Accent.TButton"
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar, text="📊 Dashboard",
            command=self.show_dashboard
        ).pack(side="left", padx=4)

        ttk.Button(
            toolbar, text="📈 Sales Chart",
            command=self.show_sales_chart
        ).pack(side="left", padx=4)

        ttk.Button(
            toolbar, text="🏆 Top Restaurants",
            command=self.show_top_restaurants
        ).pack(side="left", padx=4)

        ttk.Button(
            toolbar, text="🧹 Reset",
            command=self.reset_view
        ).pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="Load dataset.csv to begin.")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="right")

        # KPI cards
        cards = ttk.Frame(self.root, padding=(18, 0, 18, 10))
        cards.pack(fill="x")

        self.kpi_vars = {
            "rows": tk.StringVar(value="0"),
            "restaurants": tk.StringVar(value="0"),
            "cities": tk.StringVar(value="0"),
            "avg_rating": tk.StringVar(value="0.00"),
            "avg_cost": tk.StringVar(value="0.00"),
        }

        self._kpi_card(cards, "Rows", self.kpi_vars["rows"], 0)
        self._kpi_card(cards, "Restaurants", self.kpi_vars["restaurants"], 1)
        self._kpi_card(cards, "Cities", self.kpi_vars["cities"], 2)
        self._kpi_card(cards, "Avg Rating", self.kpi_vars["avg_rating"], 3)
        self._kpi_card(cards, "Avg Cost", self.kpi_vars["avg_cost"], 4)

        # Main content
        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        left = ttk.Frame(main, padding=8)
        right = ttk.Frame(main, padding=8)
        main.add(left, weight=1)
        main.add(right, weight=3)

        # Filters
        filter_box = ttk.LabelFrame(left, text="Filters", padding=10)
        filter_box.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_box, text="Search:").pack(anchor="w")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_box, textvariable=self.search_var)
        search_entry.pack(fill="x", pady=(3, 8))
        search_entry.bind("<Return>", lambda e: self.apply_filters())

        ttk.Label(filter_box, text="City:").pack(anchor="w")
        self.city_var = tk.StringVar(value="All")
        self.city_combo = ttk.Combobox(
            filter_box, textvariable=self.city_var, state="readonly"
        )
        self.city_combo.pack(fill="x", pady=(3, 8))

        ttk.Button(
            filter_box, text="Apply Filters",
            command=self.apply_filters
        ).pack(fill="x")

        # Analysis actions
        action_box = ttk.LabelFrame(left, text="Analysis", padding=10)
        action_box.pack(fill="x", pady=(0, 10))

        actions = [
            ("Dashboard KPIs", self.show_dashboard),
            ("Sales / Cost Distribution", self.show_sales_chart),
            ("Top 10 Restaurants", self.show_top_restaurants),
            ("City Performance", self.show_city_chart),
            ("Rating Distribution", self.show_rating_chart),
        ]
        for text, command in actions:
            ttk.Button(action_box, text=text, command=command).pack(fill="x", pady=3)

        # File information
        info_box = ttk.LabelFrame(left, text="Dataset Information", padding=10)
        info_box.pack(fill="both", expand=True)
        self.info_text = tk.Text(info_box, height=10, wrap="word", font=("Consolas", 9))
        self.info_text.pack(fill="both", expand=True)

        # Right: table + chart
        table_box = ttk.LabelFrame(right, text="Dataset Preview", padding=8)
        table_box.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_box, show="headings")
        yscroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_box, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree.pack(side="top", fill="both", expand=True)
        xscroll.pack(side="bottom", fill="x")
        yscroll.pack(side="right", fill="y")

        self.chart_frame = ttk.Frame(right)
        self.chart_frame.pack(fill="both", expand=False, pady=(10, 0))

    def _kpi_card(self, parent, title, variable, column):
        card = ttk.LabelFrame(parent, text=title, padding=(15, 7))
        card.grid(row=0, column=column, padx=5, sticky="ew")
        parent.columnconfigure(column, weight=1)
        ttk.Label(card, textvariable=variable, style="Card.TLabel").pack()

    # ---------------- Dataset loading ----------------

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Select dataset.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            df = pd.read_csv(path, encoding="utf-8", low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin1", low_memory=False)
        except Exception as exc:
            messagebox.showerror("Could not load dataset", str(exc))
            return

        if df.empty:
            messagebox.showwarning("Empty dataset", "The selected CSV file contains no rows.")
            return

        self.file_path = path
        self.df = df.copy()
        self.filtered_df = df.copy()

        self._normalize_columns()
        self.update_filters()
        self.update_kpis()
        self.update_table()
        self.update_info()

        self.status_var.set(
            f"Loaded: {os.path.basename(path)} | {len(self.df):,} rows"
        )

    def _normalize_columns(self):
        # Keep original names, but clean whitespace for easier matching.
        self.df.columns = [str(c).strip() for c in self.df.columns]
        self.filtered_df.columns = self.df.columns

    def update_filters(self):
        city_col = self.find_column(["city", "location", "area"])
        values = ["All"]
        if city_col:
            vals = (
                self.df[city_col]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", np.nan)
                .dropna()
                .unique()
                .tolist()
            )
            values += sorted(vals)[:1000]
        self.city_combo["values"] = values
        self.city_var.set("All")

    # ---------------- Column helpers ----------------

    def find_column(self, candidates):
        cols = list(self.filtered_df.columns if not self.filtered_df.empty else self.df.columns)
        normalized = {re.sub(r"[^a-z0-9]", "", str(c).lower()): c for c in cols}

        for candidate in candidates:
            key = re.sub(r"[^a-z0-9]", "", candidate.lower())
            if key in normalized:
                return normalized[key]

        # Fuzzy contains match
        for c in cols:
            key = re.sub(r"[^a-z0-9]", "", str(c).lower())
            for candidate in candidates:
                ck = re.sub(r"[^a-z0-9]", "", candidate.lower())
                if ck in key or key in ck:
                    return c
        return None

    def numeric_series(self, col):
        if not col:
            return pd.Series(dtype=float)
        return pd.to_numeric(
            self.filtered_df[col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True),
            errors="coerce"
        )

    # ---------------- Filtering / table ----------------

    def apply_filters(self):
        if self.df.empty:
            messagebox.showinfo("No dataset", "Please load dataset.csv first.")
            return

        data = self.df.copy()

        search = self.search_var.get().strip().lower()
        if search:
            mask = data.astype(str).apply(
                lambda col: col.str.lower().str.contains(search, na=False)
            ).any(axis=1)
            data = data[mask]

        city_col = self.find_column_from_df(data, ["city", "location", "area"])
        city = self.city_var.get()
        if city != "All" and city_col:
            data = data[data[city_col].astype(str).str.strip() == city]

        self.filtered_df = data
        self.update_kpis()
        self.update_table()
        self.update_info()
        self.status_var.set(f"Showing {len(data):,} of {len(self.df):,} rows")

    @staticmethod
    def find_column_from_df(df, candidates):
        normalized = {
            re.sub(r"[^a-z0-9]", "", str(c).lower()): c
            for c in df.columns
        }
        for candidate in candidates:
            key = re.sub(r"[^a-z0-9]", "", candidate.lower())
            if key in normalized:
                return normalized[key]
        for c in df.columns:
            key = re.sub(r"[^a-z0-9]", "", str(c).lower())
            for candidate in candidates:
                ck = re.sub(r"[^a-z0-9]", "", candidate.lower())
                if ck in key:
                    return c
        return None

    def reset_view(self):
        if self.df.empty:
            return
        self.search_var.set("")
        self.city_var.set("All")
        self.filtered_df = self.df.copy()
        self.update_kpis()
        self.update_table()
        self.update_info()
        self.status_var.set(f"Showing all {len(self.df):,} rows")

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        columns = list(self.filtered_df.columns)
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=130, minwidth=80, anchor="w")

        preview = self.filtered_df.head(300)
        for _, row in preview.iterrows():
            values = []
            for value in row.tolist():
                if pd.isna(value):
                    values.append("")
                else:
                    text = str(value)
                    values.append(text[:100])
            self.tree.insert("", "end", values=values)

    # ---------------- KPIs ----------------

    def update_kpis(self):
        df = self.filtered_df
        self.kpi_vars["rows"].set(f"{len(df):,}")

        restaurant_col = self.find_column(["restaurant name", "restaurant", "name"])
        city_col = self.find_column(["city", "location", "area"])
        rating_col = self.find_column(["aggregate rating", "rating", "rate"])
        cost_col = self.find_column([
            "average cost for two", "average cost", "cost for two",
            "cost", "sales", "amount", "revenue"
        ])

        self.kpi_vars["restaurants"].set(
            f"{df[restaurant_col].nunique():,}" if restaurant_col else "N/A"
        )
        self.kpi_vars["cities"].set(
            f"{df[city_col].nunique():,}" if city_col else "N/A"
        )

        if rating_col:
            rating = pd.to_numeric(
                df[rating_col].astype(str).str.extract(r"([0-9]+(?:\.[0-9]+)?)")[0],
                errors="coerce"
            )
            self.kpi_vars["avg_rating"].set(
                f"{rating.mean():.2f}" if rating.notna().any() else "N/A"
            )
        else:
            self.kpi_vars["avg_rating"].set("N/A")

        if cost_col:
            cost = pd.to_numeric(
                df[cost_col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True),
                errors="coerce"
            )
            self.kpi_vars["avg_cost"].set(
                f"{cost.mean():,.2f}" if cost.notna().any() else "N/A"
            )
        else:
            self.kpi_vars["avg_cost"].set("N/A")

    def update_info(self):
        self.info_text.delete("1.0", "end")
        if self.filtered_df.empty:
            self.info_text.insert("end", "No data available.")
            return

        df = self.filtered_df
        missing = int(df.isna().sum().sum())
        duplicate = int(df.duplicated().sum())

        text = (
            f"File: {os.path.basename(self.file_path) if self.file_path else 'N/A'}\n"
            f"Rows: {len(df):,}\n"
            f"Columns: {len(df.columns):,}\n"
            f"Missing cells: {missing:,}\n"
            f"Duplicate rows: {duplicate:,}\n\n"
            f"Columns:\n"
        )
        text += "\n".join(f"• {c}" for c in df.columns)
        self.info_text.insert("end", text)

    # ---------------- Charts ----------------

    def clear_chart(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

    def embed_figure(self, fig):
        self.clear_chart()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.get_tk_widget().config(height=280)

    def show_dashboard(self):
        if self.filtered_df.empty:
            return

        city_col = self.find_column(["city", "location", "area"])
        rating_col = self.find_column(["aggregate rating", "rating", "rate"])

        fig, ax = plt.subplots(figsize=(8, 3.3))
        if city_col:
            counts = self.filtered_df[city_col].astype(str).value_counts().head(10)
            counts.sort_values().plot(kind="barh", ax=ax)
            ax.set_title("Top Cities by Restaurant Count")
            ax.set_xlabel("Restaurants")
        elif rating_col:
            ratings = pd.to_numeric(
                self.filtered_df[rating_col].astype(str).str.extract(
                    r"([0-9]+(?:\.[0-9]+)?)"
                )[0],
                errors="coerce"
            ).dropna()
            ratings.value_counts().sort_index().plot(kind="bar", ax=ax)
            ax.set_title("Rating Distribution")
            ax.set_xlabel("Rating")
            ax.set_ylabel("Count")
        else:
            ax.text(0.5, 0.5, "No suitable columns found for dashboard.",
                    ha="center", va="center")
            ax.axis("off")

        fig.tight_layout()
        self.embed_figure(fig)
        plt.close(fig)

    def show_sales_chart(self):
        if self.filtered_df.empty:
            return

        cost_col = self.find_column([
            "average cost for two", "average cost", "cost for two",
            "cost", "sales", "amount", "revenue"
        ])
        if not cost_col:
            messagebox.showwarning(
                "Column not found",
                "No cost/sales/revenue column was found in this dataset."
            )
            return

        values = self.numeric_series(cost_col).dropna()
        if values.empty:
            messagebox.showwarning("No numeric data", f"Column '{cost_col}' has no usable numeric values.")
            return

        fig, ax = plt.subplots(figsize=(8, 3.3))
        ax.hist(values.clip(lower=0), bins=20)
        ax.set_title(f"Distribution of {cost_col}")
        ax.set_xlabel(cost_col)
        ax.set_ylabel("Number of records")
        fig.tight_layout()
        self.embed_figure(fig)
        plt.close(fig)

    def show_top_restaurants(self):
        if self.filtered_df.empty:
            return

        name_col = self.find_column(["restaurant name", "restaurant", "name"])
        if not name_col:
            messagebox.showwarning("Column not found", "No restaurant name column was found.")
            return

        # Prefer votes/orders/sales as a performance metric.
        metric_col = self.find_column([
            "votes", "orders", "order count", "sales", "revenue",
            "amount", "bookings", "rating"
        ])

        if metric_col:
            metric = pd.to_numeric(
                self.filtered_df[metric_col].astype(str).str.replace(
                    r"[^0-9.\-]", "", regex=True
                ),
                errors="coerce"
            )
            temp = pd.DataFrame({
                "name": self.filtered_df[name_col].astype(str),
                "metric": metric
            }).dropna()
            top = temp.groupby("name")["metric"].sum().sort_values(ascending=False).head(10)
            title = f"Top Restaurants by {metric_col}"
        else:
            top = self.filtered_df[name_col].astype(str).value_counts().head(10).sort_values()
            title = "Top Restaurants by Record Count"

        fig, ax = plt.subplots(figsize=(8, 3.3))
        top.sort_values().plot(kind="barh", ax=ax)
        ax.set_title(title)
        ax.set_xlabel(metric_col if metric_col else "Records")
        fig.tight_layout()
        self.embed_figure(fig)
        plt.close(fig)

    def show_city_chart(self):
        if self.filtered_df.empty:
            return

        city_col = self.find_column(["city", "location", "area"])
        if not city_col:
            messagebox.showwarning("Column not found", "No city/location column was found.")
            return

        counts = self.filtered_df[city_col].astype(str).value_counts().head(15).sort_values()

        fig, ax = plt.subplots(figsize=(8, 3.3))
        counts.plot(kind="barh", ax=ax)
        ax.set_title("Restaurant Distribution by City")
        ax.set_xlabel("Restaurants")
        fig.tight_layout()
        self.embed_figure(fig)
        plt.close(fig)

    def show_rating_chart(self):
        if self.filtered_df.empty:
            return

        rating_col = self.find_column(["aggregate rating", "rating", "rate"])
        if not rating_col:
            messagebox.showwarning("Column not found", "No rating column was found.")
            return

        rating = pd.to_numeric(
            self.filtered_df[rating_col].astype(str).str.extract(
                r"([0-9]+(?:\.[0-9]+)?)"
            )[0],
            errors="coerce"
        ).dropna()

        if rating.empty:
            messagebox.showwarning("No numeric data", "The rating column has no usable numeric values.")
            return

        fig, ax = plt.subplots(figsize=(8, 3.3))
        ax.hist(rating, bins=min(20, max(5, rating.nunique())))
        ax.set_title("Rating Distribution")
        ax.set_xlabel("Rating")
        ax.set_ylabel("Restaurants / Records")
        fig.tight_layout()
        self.embed_figure(fig)
        plt.close(fig)


def main():
    root = tk.Tk()
    app = ZomatoSalesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
