"""
=============================================================
  RETAIL FOOTWEAR SHOP — ML INTELLIGENCE SYSTEM  v2.0
  ─────────────────────────────────────────────────────
  ML logic extracted from notebook for Flask integration.
  Returns structured data instead of printing to console.
=============================================================
"""

import pandas as pd
import numpy as np
import warnings, calendar
from datetime import datetime, timedelta
import io
import sys

warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Required columns for validation
_SALES_REQUIRED   = ["date", "product_name", "unit_price", "quantity_sold"]
_STOCK_REQUIRED   = ["date", "product_name", "stock_remaining"]
_PRODUCT_REQUIRED = ["product_name", "cost_price"]


def validate_columns(df, required_columns, file_name):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in {file_name}: {', '.join(missing)}. "
            f"Required: {', '.join(required_columns)}"
        )


class ExternalContextLoader:

    TEMP_HIGH_THRESHOLD  = 35
    TEMP_LOW_THRESHOLD   = 18
    KNOWN_FESTIVAL_DATES = {
        "01-26","08-15","10-02",
        "11-01","11-02","11-03",
        "10-24","10-25",
        "12-25","01-01",
        "04-14",
        "04-21","04-22",
        "03-25","03-26",
    }

    def load(self, context_path):
        if context_path is None:
            return None
        try:
            df = pd.read_excel(context_path)
            df.columns = df.columns.str.strip().str.lower().str.replace(" ","_")
            df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["date"])
            return df
        except FileNotFoundError:
            return None

    def _build_synthetic(self, dates):
        MONTH_WEATHER = {1:"sunny",2:"sunny",3:"sunny",4:"sunny",
                         5:"sunny",6:"rainy",7:"rainy",8:"rainy",
                         9:"cloudy",10:"cloudy",11:"sunny",12:"sunny"}
        MONTH_TEMP    = {1:22,2:24,3:28,4:32,5:36,6:32,
                         7:29,8:29,9:30,10:28,11:25,12:22}
        rows = []
        for d in dates:
            month = d.month
            rows.append({
                "date"        : d,
                "weather"     : MONTH_WEATHER.get(month, "sunny"),
                "temperature" : MONTH_TEMP.get(month, 28) + np.random.uniform(-2, 2),
                "is_festival" : 1 if d.strftime("%m-%d") in self.KNOWN_FESTIVAL_DATES else 0,
            })
        return pd.DataFrame(rows)

    def engineer(self, context_df, all_dates):
        unique_dates = all_dates.drop_duplicates()
        if context_df is None:
            ctx = self._build_synthetic(unique_dates)
        else:
            missing = unique_dates[~unique_dates.isin(context_df["date"])]
            if len(missing):
                ctx = pd.concat([context_df, self._build_synthetic(missing)], ignore_index=True)
            else:
                ctx = context_df.copy()

        ctx = ctx.rename(columns={"weather":"ctx_weather",
                                  "temperature":"ctx_temperature",
                                  "is_festival":"ctx_is_festival"})
        ctx["ctx_is_rainy_day"]     = (ctx["ctx_weather"] == "rainy").astype(int)
        ctx["ctx_is_sunny_day"]     = (ctx["ctx_weather"] == "sunny").astype(int)
        ctx["ctx_is_stormy_day"]    = (ctx["ctx_weather"] == "stormy").astype(int)
        ctx["ctx_high_temp_flag"]   = (ctx["ctx_temperature"] > self.TEMP_HIGH_THRESHOLD).astype(int)
        ctx["ctx_low_temp_flag"]    = (ctx["ctx_temperature"] < self.TEMP_LOW_THRESHOLD).astype(int)
        ctx["ctx_is_salary_window"] = (ctx["date"].dt.day <= 5).astype(int)
        if "ctx_is_festival" not in ctx.columns:
            ctx["ctx_is_festival"] = ctx["date"].apply(
                lambda d: 1 if d.strftime("%m-%d") in self.KNOWN_FESTIVAL_DATES else 0)
        return ctx[["date","ctx_weather","ctx_temperature","ctx_is_festival",
                    "ctx_is_rainy_day","ctx_is_sunny_day","ctx_is_stormy_day",
                    "ctx_high_temp_flag","ctx_low_temp_flag","ctx_is_salary_window"]]


class SalesDataPipeline:

    PRODUCT_WEATHER = {
        "adidas flip-flop" : ["rainy","summer"],
        "crocs clog"       : ["rainy","summer"],
        "puma slip-on"     : ["rainy","summer"],
        "bata slip-on"     : ["rainy","summer"],
        "relaxo sandal"    : ["rainy","summer"],
        "woodland slip-on" : ["rainy","winter"],
        "bata sandal"      : ["summer","rainy"],
        "puma sandal"      : ["summer"],
        "adidas sandal"    : ["summer"],
        "liberty sandal"   : ["summer"],
        "nike shoes"       : ["winter","autumn"],
        "bata formal"      : ["winter","autumn"],
        "nike sneakers"    : ["winter","autumn"],
        "bata comfort shoe": ["all season"],
        "reebok shoes"     : ["winter","autumn"],
    }
    MONTH_SEASON = {
        1:"winter",2:"winter",3:"spring",4:"spring",
        5:"summer",6:"rainy",7:"rainy",8:"rainy",
        9:"autumn",10:"autumn",11:"winter",12:"winter"
    }

    def load(self, sales_path, stock_path, product_path, context_path=None):
        self.sales_raw   = pd.read_excel(sales_path)
        self.stock_raw   = pd.read_excel(stock_path)
        self.product_raw = pd.read_excel(product_path)
        self._ctx_loader = ExternalContextLoader()
        self._ctx_raw    = self._ctx_loader.load(context_path)
        self._sales_file   = sales_path
        self._stock_file   = stock_path
        self._product_file = product_path
        return self

    def _clean_sales(self):
        df = self.sales_raw.copy()
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df = df.rename(columns={
            "product_name_" : "product_name",
            "seiling_price" : "unit_price",
            "selling_price" : "unit_price",
            "price"         : "unit_price",
            "no_ofproducts" : "quantity_sold",
            "no_of_products": "quantity_sold",
            "qty"           : "quantity_sold",
            "quantity"      : "quantity_sold",
        })
        validate_columns(df, _SALES_REQUIRED, self._sales_file)
        df["date"]         = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df["product_name"] = df["product_name"].str.strip().str.lower()
        df["product_name"] = df["product_name"].str.replace(r"\s+\d+$", "", regex=True)
        df["sales"] = df["unit_price"] * df["quantity_sold"]
        return df.dropna(subset=["date", "product_name"])

    def _clean_stock(self):
        df = self.stock_raw.copy()
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df = df.rename(columns={
            "stock_level"     : "stock_remaining",
            "stock_loaded"    : "stock_remaining",
            "stock"           : "stock_remaining",
            "stock_available" : "stock_remaining",
            "product_name"    : "product_name",
            "sales_id_"       : "sales_id",
        })
        validate_columns(df, _STOCK_REQUIRED, self._stock_file)
        df["date"]         = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df["product_name"] = df["product_name"].str.strip().str.lower()
        df["product_name"] = df["product_name"].str.replace(r"\s+\d+$", "", regex=True)
        return df.dropna(subset=["date", "product_name"])

    def _clean_product(self):
        df = self.product_raw.copy()
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df = df.rename(columns={
            "cost"       : "cost_price",
            "price"      : "cost_price",
            "cogs"       : "cost_price",
            "costprice"  : "cost_price",
        })
        validate_columns(df, _PRODUCT_REQUIRED, self._product_file)
        df["product_name"] = df["product_name"].str.strip().str.lower()
        df = df.dropna(subset=["product_name"]).drop_duplicates(subset=["product_name"])
        return df[["product_name", "cost_price"]]

    def build(self):
        sales, stock, product = (self._clean_sales(),
                                 self._clean_stock(),
                                 self._clean_product())

        daily = sales.groupby(["date","product_name"], as_index=False).agg(
            quantity_sold=("quantity_sold","sum"),
            sales=("sales","sum"),
            unit_price=("unit_price","mean"))

        latest_stock = (stock.sort_values("date")
                             .groupby("product_name", as_index=False)
                             .last()[["product_name","stock_remaining"]])

        df = daily.merge(latest_stock, on="product_name", how="left")
        df = df.merge(product, on="product_name", how="left")
        df["stock_remaining"] = df["stock_remaining"].fillna(0)
        df["cost_price"]      = df["cost_price"].fillna(df["unit_price"] * 0.65)

        df = df.sort_values(["product_name","date"]).reset_index(drop=True)
        df["day_of_week"]    = df["date"].dt.dayofweek
        df["is_weekend"]     = (df["day_of_week"] >= 5).astype(int)
        df["month"]          = df["date"].dt.month
        df["is_month_start"] = df["date"].dt.is_month_start.astype(int)
        df["is_month_end"]   = df["date"].dt.is_month_end.astype(int)
        df["season"]         = df["month"].map(self.MONTH_SEASON)

        def season_match(row):
            tags = self.PRODUCT_WEATHER.get(row["product_name"], ["all season"])
            return 1 if (row["season"] in tags or "all season" in tags) else 0
        df["season_match"] = df.apply(season_match, axis=1)

        df["lag_1"]  = df.groupby("product_name")["sales"].shift(1)
        df["lag_7"]  = df.groupby("product_name")["sales"].shift(7)
        df["avg_3d"] = df.groupby("product_name")["sales"].transform(
            lambda x: x.rolling(3, min_periods=1).mean())
        df["avg_7d"] = df.groupby("product_name")["sales"].transform(
            lambda x: x.rolling(7, min_periods=1).mean())
        df["growth"]          = (df["sales"] - df["lag_1"]) / df["lag_1"].replace(0, np.nan)
        df["profit_per_unit"] = df["unit_price"] - df["cost_price"]
        df["profit"]          = df["profit_per_unit"] * df["quantity_sold"]

        ctx_df = self._ctx_loader.engineer(self._ctx_raw, df["date"])
        df = df.merge(ctx_df, on="date", how="left")

        ctx_num_cols = ["ctx_temperature","ctx_is_festival","ctx_is_rainy_day",
                        "ctx_is_sunny_day","ctx_is_stormy_day","ctx_high_temp_flag",
                        "ctx_low_temp_flag","ctx_is_salary_window"]
        for col in ctx_num_cols:
            df[col] = df[col].fillna(0)
        df["ctx_weather"]           = df["ctx_weather"].fillna("sunny")
        df["ctx_rain_season_boost"] = (df["ctx_is_rainy_day"] * df["season_match"]).astype(int)
        df["ctx_festival_weekend"]  = (df["ctx_is_festival"]  * df["is_weekend"]).astype(int)

        self.df = df
        return df


class SalesFactorAnalysis:

    FEATURES = [
        "is_weekend","is_month_start","is_month_end","day_of_week","month",
        "season_match","avg_3d","avg_7d","lag_1","lag_7",
        "ctx_is_rainy_day","ctx_is_sunny_day","ctx_is_stormy_day",
        "ctx_high_temp_flag","ctx_low_temp_flag","ctx_is_festival",
        "ctx_is_salary_window","ctx_rain_season_boost","ctx_festival_weekend",
    ]

    def __init__(self):
        self.model    = RandomForestRegressor(n_estimators=150, random_state=42)
        self.trained_ = False

    def fit(self, df):
        clean = df.dropna(subset=self.FEATURES + ["sales"])
        if len(clean) < 5:
            return self
        X = clean[self.FEATURES]
        y = clean["sales"]
        self.model.fit(X, y)
        self.trained_ = True
        importances = dict(zip(self.FEATURES, self.model.feature_importances_))
        self.top_drivers_ = sorted(importances.items(), key=lambda x: -x[1])[:3]
        return self

    def get_summary(self, df):
        """Returns a dict with today's sales summary data"""
        today       = df["date"].max()
        today_df    = df[df["date"] == today]
        total_sales = today_df["sales"].sum()
        units_sold  = today_df["quantity_sold"].sum()
        avg_daily   = df.groupby("date")["sales"].sum().mean()
        delta_pct   = (total_sales - avg_daily) / avg_daily * 100 if avg_daily else 0

        top_products = (today_df.groupby("product_name")["sales"]
                        .sum().sort_values(ascending=False).head(3).index.tolist())

        season = df[df["date"] == today]["season"].iloc[0] if len(today_df) else "unknown"
        weather = df[df["date"] == today]["ctx_weather"].iloc[0] if len(today_df) else "sunny"
        temp = df[df["date"] == today]["ctx_temperature"].iloc[0] if len(today_df) else 28.0

        drivers = []
        if self.trained_:
            drivers = [f"{k.replace('_',' ')} {v*100:.0f}%" for k,v in self.top_drivers_]

        return {
            "date": today.strftime("%d %b %Y"),
            "day_name": calendar.day_name[today.weekday()],
            "season": season.title(),
            "weather": weather.title(),
            "temperature": round(float(temp), 1),
            "total_sales": round(float(total_sales), 2),
            "units_sold": int(units_sold),
            "delta_pct": round(float(delta_pct), 1),
            "top_products": [p.title() for p in top_products],
            "ml_drivers": drivers,
        }


class ProductTrendAnalysis:

    def fit(self, df):
        results = {}
        for product, grp in df.groupby("product_name"):
            daily = grp.groupby("date")["quantity_sold"].sum().reset_index()
            daily = daily.sort_values("date")
            if len(daily) < 3:
                results[product] = {"direction": "➡️ Stable", "slope": 0.0}
                continue
            x = np.arange(len(daily))
            y = daily["quantity_sold"].values
            slope = np.polyfit(x, y, 1)[0]
            if slope > 0.1:
                direction = "📈 Rising"
            elif slope < -0.1:
                direction = "📉 Falling"
            else:
                direction = "➡️ Stable"
            results[product] = {"direction": direction, "slope": round(slope, 2)}
        self.results_ = results
        return self

    def get_top_trends(self, pipeline, n=3):
        """Return top N trending products with their info"""
        items = []
        for p, r in self.results_.items():
            items.append({
                "product": p.title(),
                "direction": r["direction"],
                "slope": r["slope"]
            })
        # sort by absolute slope descending
        items.sort(key=lambda x: abs(x["slope"]), reverse=True)
        return items[:n]


class StockRecommendationEngine:

    def __init__(self, lead_time=3, z=1.65, forecast_days=7):
        self.lead_time     = lead_time
        self.z             = z
        self.forecast_days = forecast_days

    def fit(self, df, pipeline):
        recs = {}
        for product, grp in df.groupby("product_name"):
            daily_qty  = grp.groupby("date")["quantity_sold"].sum()
            avg_daily  = daily_qty.mean()
            std_daily  = daily_qty.std() if len(daily_qty) > 1 else avg_daily * 0.2
            stock      = grp["stock_remaining"].iloc[-1]

            safety   = self.z * (std_daily or 0) * np.sqrt(self.lead_time)
            reorder  = avg_daily * self.lead_time + safety
            days_left = stock / avg_daily if avg_daily > 0 else 999

            if days_left <= 2:
                risk = "🔴 CRITICAL"
            elif days_left <= 5:
                risk = "🟡 LOW"
            else:
                risk = "🟢 OK"

            recs[product] = {
                "product"   : product,
                "stock"     : int(stock),
                "days_left" : round(days_left, 1),
                "order_qty" : max(0, int(reorder - stock)),
                "risk"      : risk,
            }
        self.recs_ = recs
        return self

    def get_alerts(self):
        """Returns critical and low stock items"""
        critical = [r for r in self.recs_.values() if r["risk"] == "🔴 CRITICAL"]
        low      = [r for r in self.recs_.values() if r["risk"] == "🟡 LOW"]
        critical.sort(key=lambda x: x["days_left"])
        low.sort(key=lambda x: x["days_left"])
        return {"critical": critical, "low": low}


class SalesForecaster:

    FEATURES = [
        "is_weekend","is_month_start","is_month_end","day_of_week","month",
        "season_match","avg_3d","avg_7d","lag_1","lag_7",
        "ctx_is_rainy_day","ctx_is_sunny_day","ctx_is_stormy_day",
        "ctx_high_temp_flag","ctx_low_temp_flag","ctx_is_festival",
        "ctx_is_salary_window","ctx_rain_season_boost","ctx_festival_weekend",
    ]

    def __init__(self):
        self.model   = GradientBoostingRegressor(n_estimators=200, random_state=42)
        self.scaler  = StandardScaler()
        self.trained = False

    def fit(self, df):
        clean = df.dropna(subset=self.FEATURES + ["sales"])
        if len(clean) < 10:
            self.fallback_avg = df.groupby("date")["sales"].sum().mean()
            return self
        daily_total = df.groupby("date")[self.FEATURES + ["sales"]].mean().reset_index()
        clean2 = daily_total.dropna(subset=self.FEATURES + ["sales"])
        if len(clean2) < 5:
            self.fallback_avg = clean2["sales"].mean()
            return self
        X = clean2[self.FEATURES]
        y = clean2["sales"]
        X_sc = self.scaler.fit_transform(X)
        self.model.fit(X_sc, y)
        self.trained = True
        return self

    def predict_tomorrow(self, df, pipeline, tomorrow_ctx=None):
        """Returns forecast dict for tomorrow"""
        today    = df["date"].max()
        tomorrow = today + timedelta(days=1)
        dow      = tomorrow.weekday()
        month    = tomorrow.month

        daily_sum = df.groupby("date")["sales"].sum()
        lag_1     = float(daily_sum.iloc[-1]) if len(daily_sum) >= 1 else 0.0

        avg_season_match = df[df["month"] == month]["season_match"].mean()

        def _ctx(col):
            if tomorrow_ctx and col in tomorrow_ctx:
                return tomorrow_ctx[col]
            return float(df[col].iloc[-1]) if col in df.columns else 0

        row = pd.DataFrame([{
            "is_weekend"          : 1 if dow >= 5 else 0,
            "is_month_start"      : 1 if tomorrow.day == 1 else 0,
            "is_month_end"        : 1 if tomorrow.day == calendar.monthrange(tomorrow.year, month)[1] else 0,
            "day_of_week"         : dow,
            "month"               : month,
            "season_match"        : 0 if np.isnan(avg_season_match) else avg_season_match,
            "avg_3d"              : daily_sum.iloc[-3:].mean() if len(daily_sum) >= 3 else lag_1,
            "avg_7d"              : daily_sum.iloc[-7:].mean() if len(daily_sum) >= 7 else lag_1,
            "lag_1"               : lag_1,
            "lag_7"               : float(daily_sum.iloc[-7]) if len(daily_sum) >= 7 else lag_1,
            "ctx_is_rainy_day"    : _ctx("ctx_is_rainy_day"),
            "ctx_is_sunny_day"    : _ctx("ctx_is_sunny_day"),
            "ctx_is_stormy_day"   : _ctx("ctx_is_stormy_day"),
            "ctx_high_temp_flag"  : _ctx("ctx_high_temp_flag"),
            "ctx_low_temp_flag"   : _ctx("ctx_low_temp_flag"),
            "ctx_is_festival"     : _ctx("ctx_is_festival"),
            "ctx_is_salary_window": 1 if tomorrow.day <= 5 else 0,
            "ctx_rain_season_boost": _ctx("ctx_is_rainy_day") * int(not np.isnan(avg_season_match)),
            "ctx_festival_weekend" : _ctx("ctx_is_festival") * (1 if dow >= 5 else 0),
        }])

        if self.trained:
            X_sc = self.scaler.transform(row[self.FEATURES].values)
            pred = float(self.model.predict(X_sc)[0])
        else:
            pred = getattr(self, "fallback_avg", lag_1)

        recent_std = df.groupby("date")["sales"].sum().std()
        lower = max(0, pred - recent_std * 0.5)
        upper = pred + recent_std * 0.5
        chg   = (pred - lag_1) / lag_1 * 100 if lag_1 else 0

        return {
            "forecast_date"    : tomorrow.strftime("%d %b %Y"),
            "day_name"         : calendar.day_name[dow],
            "predicted_sales"  : round(pred, 2),
            "lower_bound"      : round(lower, 2),
            "upper_bound"      : round(upper, 2),
            "change_pct"       : round(chg, 1),
            "today_sales"      : round(lag_1, 2),
        }


class RetailMLSystem:

    def __init__(self):
        self.pipeline   = SalesDataPipeline()
        self.factor     = SalesFactorAnalysis()
        self.trend      = ProductTrendAnalysis()
        self.stock      = StockRecommendationEngine(lead_time=3, z=1.65, forecast_days=7)
        self.forecaster = SalesForecaster()

    def run(self, sales_path, stock_path, product_path, context_path=None, tomorrow_ctx=None):
        """
        Main entry point. Returns a structured dict with all prediction results.
        Raises ValueError if Excel files have missing columns.
        """
        # Load and validate files (validation fires inside _clean_* methods)
        self.pipeline.load(sales_path, stock_path, product_path, context_path=context_path)
        df = self.pipeline.build()

        # Run all ML modules
        self.factor.fit(df)
        self.trend.fit(df)
        self.stock.fit(df, self.pipeline)
        self.forecaster.fit(df)

        # Collect all results as structured data
        summary  = self.factor.get_summary(df)
        forecast = self.forecaster.predict_tomorrow(df, self.pipeline, tomorrow_ctx=tomorrow_ctx)
        trends   = self.trend.get_top_trends(self.pipeline, n=5)
        stock_alerts = self.stock.get_alerts()

        # Build business insights list
        insights = self._build_insights(df)

        return {
            "summary"      : summary,
            "forecast"     : forecast,
            "trends"       : trends,
            "stock_alerts" : stock_alerts,
            "insights"     : insights,
        }

    def _build_insights(self, df):
        today       = df["date"].max()
        total_sales = df[df["date"] == today]["sales"].sum()
        avg_daily   = df.groupby("date")["sales"].sum().mean()
        delta_pct   = (total_sales - avg_daily) / avg_daily * 100 if avg_daily else 0

        recs     = list(self.stock.recs_.values())
        critical = [r for r in recs if r["risk"] == "🔴 CRITICAL"]
        rising   = [p for p, r in self.trend.results_.items() if r["direction"] == "📈 Rising"]
        falling  = [p for p, r in self.trend.results_.items() if r["direction"] == "📉 Falling"]

        insights = []
        tag = "above average ▲" if delta_pct > 0 else "below average ▼"
        insights.append({
            "type": "sales_performance",
            "icon": "📊",
            "message": f"Sales {delta_pct:+.1f}% {tag} — {'strong' if delta_pct > 0 else 'slow'} trading day."
        })
        if critical:
            names = ", ".join(r["product"].title() for r in critical[:3])
            extra = f" (+{len(critical)-3} more)" if len(critical) > 3 else ""
            insights.append({
                "type": "stock_alert",
                "icon": "🚨",
                "message": f"{len(critical)} product(s) critically low — order NOW: {names}{extra}."
            })
        if rising:
            insights.append({
                "type": "rising_demand",
                "icon": "🔥",
                "message": f"Rising demand: {', '.join(p.title() for p in rising[:3])} — increase reorder quantities."
            })
        if falling:
            insights.append({
                "type": "declining",
                "icon": "⚠️",
                "message": f"Declining: {', '.join(p.title() for p in falling[:3])} — reduce reorders to avoid overstock."
            })
        if not critical and not rising and not falling:
            insights.append({
                "type": "all_clear",
                "icon": "✅",
                "message": "All products stable — no urgent action required."
            })

        return insights
