#!/usr/bin/env python3
"""Generate a reproducible synthetic e-commerce dataset for product analytics."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import json

import numpy as np
import pandas as pd


SEED = 42
START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 6, 30)
N_USERS = 10_000
N_PRODUCTS = 150

CHANNELS = ["organic", "paid_search", "social", "referral", "email"]
CHANNEL_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]
COUNTRIES = ["Finland", "Germany", "United Kingdom", "France", "Spain", "Netherlands", "Sweden"]
COUNTRY_WEIGHTS = [0.20, 0.19, 0.17, 0.14, 0.12, 0.10, 0.08]
DEVICES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.66, 0.29, 0.05]

CATALOG = {
    "Home & Kitchen": {
        "names": ["Ceramic Mug", "Cotton Towel Set", "Storage Basket", "Desk Lamp", "Water Bottle",
                  "Linen Cushion Cover", "Glass Food Container", "Wool Throw", "Cutting Board", "Table Organizer"],
        "price": (8, 95), "weight": 0.20,
    },
    "Electronics": {
        "names": ["Wireless Earbuds", "USB-C Hub", "Bluetooth Speaker", "Mechanical Keyboard", "Wireless Mouse",
                  "Portable Charger", "Webcam", "Smart Plug", "Monitor Light", "Noise-Cancelling Headphones"],
        "price": (18, 260), "weight": 0.16,
    },
    "Clothing": {
        "names": ["Cotton T-Shirt", "Everyday Hoodie", "Relaxed Jeans", "Knit Cardigan", "Running Shorts",
                  "Linen Shirt", "Wool Socks", "Rain Jacket", "Canvas Cap", "Everyday Sneakers"],
        "price": (12, 180), "weight": 0.19,
    },
    "Beauty & Personal Care": {
        "names": ["Face Moisturizer", "Gentle Cleanser", "Shampoo", "Hand Cream", "SPF Face Lotion",
                  "Body Wash", "Lip Balm Set", "Hair Brush", "Bath Salts", "Facial Serum"],
        "price": (5, 85), "weight": 0.15,
    },
    "Sports & Outdoors": {
        "names": ["Yoga Mat", "Insulated Bottle", "Resistance Bands", "Daypack", "Running Belt",
                  "Camping Lantern", "Training Gloves", "Foam Roller", "Travel Towel", "Hiking Poles"],
        "price": (10, 210), "weight": 0.14,
    },
    "Books & Stationery": {
        "names": ["Dot Grid Notebook", "Weekly Planner", "Gel Pen Set", "Desk Notebook", "Watercolour Pad",
                  "Hardcover Journal", "Sticky Notes Set", "Fountain Pen", "Reading Light", "Sketchbook"],
        "price": (4, 70), "weight": 0.16,
    },
}

# Channel-level behavioral tendencies are deliberately moderate, not deterministic.
CHANNEL_CONVERSION = {
    "organic": 1.00, "paid_search": 1.10, "social": 0.78,
    "referral": 1.18, "email": 1.12,
}
CHANNEL_RETURNING = {
    "organic": 1.00, "paid_search": 0.92, "social": 0.82,
    "referral": 1.12, "email": 1.25,
}


def iso_utc(value: datetime) -> str:
    """Serialize a timezone-aware datetime as ISO 8601 UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def weighted_choice(rng: np.random.Generator, values, weights):
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    return values[int(rng.choice(len(values), p=weights))]


def generate_users(rng: np.random.Generator, n_users: int) -> pd.DataFrame:
    # Weekly demand varies, with a few moderate campaign/seasonality pulses.
    all_days = pd.date_range(START_DATE, END_DATE, freq="D")
    daily_weights = []
    for ts in all_days:
        week = int((ts.date() - START_DATE).days // 7)
        weekday_factor = [0.92, 0.96, 1.00, 1.03, 1.08, 1.18, 1.12][ts.weekday()]
        monthly_factor = {1: 0.88, 2: 0.94, 3: 1.02, 4: 1.10, 5: 1.04, 6: 1.16}[ts.month]
        campaign_factor = 1.0
        if 35 <= week <= 38:
            campaign_factor *= 1.22
        if 19 <= week <= 21:
            campaign_factor *= 1.13
        daily_weights.append(weekday_factor * monthly_factor * campaign_factor)
    daily_weights = np.asarray(daily_weights, dtype=float)
    daily_weights /= daily_weights.sum()
    reg_days = rng.choice(all_days.to_numpy(), size=n_users, p=daily_weights)
    reg_days = pd.to_datetime(reg_days).date

    users = pd.DataFrame({
        "user_id": [f"U{i:06d}" for i in range(1, n_users + 1)],
        "registration_date": [d.isoformat() for d in reg_days],
        "acquisition_channel": rng.choice(CHANNELS, n_users, p=CHANNEL_WEIGHTS),
        "country": rng.choice(COUNTRIES, n_users, p=COUNTRY_WEIGHTS),
        "device_type": rng.choice(DEVICES, n_users, p=DEVICE_WEIGHTS),
    })
    # Latent traits create meaningful heterogeneity in engagement and repeat behavior.
    users["_engagement"] = rng.beta(2.0, 5.0, size=n_users)
    users["_purchase_affinity"] = rng.beta(1.8, 5.2, size=n_users)
    users["_repeat_affinity"] = rng.beta(2.0, 4.5, size=n_users)
    return users


def generate_products(rng: np.random.Generator, n_products: int) -> pd.DataFrame:
    categories = list(CATALOG)
    cat_weights = np.array([CATALOG[c]["weight"] for c in categories], dtype=float)
    assigned = rng.choice(categories, size=n_products, p=cat_weights / cat_weights.sum())
    rows = []
    category_counters = Counter()
    for idx, category in enumerate(assigned, start=1):
        spec = CATALOG[category]
        category_counters[category] += 1
        base = spec["names"][(category_counters[category] - 1) % len(spec["names"])]
        suffix = category_counters[category]
        name = base if suffix == 1 else f"{base} {suffix}"
        low, high = spec["price"]
        # Log-normal spread within category, clipped to plausible category bounds.
        midpoint = np.sqrt(low * high)
        price = float(np.clip(rng.lognormal(np.log(midpoint), 0.42), low, high))
        rows.append({
            "product_id": f"P{idx:04d}",
            "product_name": name,
            "category": category,
            "price": round(price, 2),
        })
    return pd.DataFrame(rows)


def time_effect(ts: datetime) -> float:
    """A mild, mixed time effect; not every metric moves in the same direction."""
    day = (ts.date() - START_DATE).days
    factor = 1.0
    # A modest late-February dip followed by a spring recovery.
    if 45 <= day <= 58:
        factor *= 0.86
    if 92 <= day <= 116:
        factor *= 1.10
    # June has more browsing but not a proportionate increase in checkout intent.
    if ts.month == 6:
        factor *= 0.96
    return factor


def generate_dataset(seed: int = SEED, n_users: int = N_USERS, n_products: int = N_PRODUCTS):
    rng = np.random.default_rng(seed)
    users = generate_users(rng, n_users)
    products = generate_products(rng, n_products)

    product_ids = products["product_id"].tolist()
    product_prices = dict(zip(products["product_id"], products["price"]))
    product_categories = dict(zip(products["product_id"], products["category"]))
    category_weights = products["category"].value_counts(normalize=True).to_dict()

    orders = []
    order_items = []
    events = []
    order_counter = 1
    item_counter = 1
    event_counter = 1
    end_dt = datetime.combine(END_DATE, time(23, 50), tzinfo=timezone.utc)

    for user_idx, user in enumerate(users.itertuples(index=False)):
        reg_date = date.fromisoformat(user.registration_date)
        reg_dt = datetime.combine(reg_date, time(0, 0), tzinfo=timezone.utc)
        if reg_dt >= end_dt:
            continue

        # Read latent traits by row index; pandas renames namedtuple fields beginning with underscores.
        row = users.iloc[user_idx]
        engagement = float(row["_engagement"])
        affinity = float(row["_purchase_affinity"])
        repeat_affinity = float(row["_repeat_affinity"])
        channel = user.acquisition_channel

        days_active = max(1, (END_DATE - reg_date).days + 1)
        tenure_scale = min(1.0, days_active / 75.0)
        base_sessions = 1.15 + 7.0 * engagement * tenure_scale
        if channel == "email":
            base_sessions *= 1.12
        if channel == "social":
            base_sessions *= 0.92
        n_sessions = int(np.clip(rng.poisson(base_sessions) + (1 if rng.random() < 0.14 else 0), 1, 12))

        # Pick distinct calendar days when possible; this creates realistic repeat visits.
        max_day_offset = max(0, (END_DATE - reg_date).days)
        if max_day_offset == 0:
            offsets = [0] * n_sessions
        else:
            offsets = rng.integers(0, max_day_offset + 1, size=n_sessions).tolist()
        offsets.sort()

        user_has_purchased = False
        for session_idx, offset in enumerate(offsets, start=1):
            session_date = reg_date + timedelta(days=int(offset))
            # Keep all generated actions safely within the dataset window.
            session_start = datetime.combine(session_date, time(8, 0), tzinfo=timezone.utc)
            session_start += timedelta(minutes=int(rng.integers(0, 14 * 60)))
            if session_start > end_dt - timedelta(minutes=20):
                session_start = end_dt - timedelta(minutes=20)

            session_id = f"S_{user.user_id}_{session_idx:02d}"
            timestamp = session_start
            view_count = int(np.clip(rng.poisson(2.4 + 4.0 * engagement) + 1, 1, 9))
            viewed = []
            # Category popularity differs, and product prices/categories influence interest.
            cats = list(category_weights)
            cat_probs = np.array([category_weights[c] for c in cats], dtype=float)
            cat_probs /= cat_probs.sum()
            for _ in range(view_count):
                cat = weighted_choice(rng, cats, cat_probs)
                candidates = products.loc[products["category"].eq(cat), "product_id"].tolist()
                pid = str(rng.choice(candidates))
                viewed.append(pid)
                timestamp += timedelta(seconds=int(rng.integers(8, 75)))
                events.append({
                    "event_id": f"E{event_counter:08d}", "user_id": user.user_id,
                    "event_timestamp": iso_utc(timestamp), "event_type": "view",
                    "product_id": pid, "session_id": session_id, "order_id": None,
                })
                event_counter += 1

            # Add-to-cart probability depends on latent user intent, channel, and time.
            cart_prob = (0.085 + 0.34 * affinity + 0.13 * engagement) * CHANNEL_CONVERSION[channel]
            cart_prob *= time_effect(session_start)
            if rng.random() >= min(0.58, cart_prob):
                continue

            cart_product = str(rng.choice(viewed))
            timestamp += timedelta(seconds=int(rng.integers(10, 100)))
            events.append({
                "event_id": f"E{event_counter:08d}", "user_id": user.user_id,
                "event_timestamp": iso_utc(timestamp), "event_type": "add_to_cart",
                "product_id": cart_product, "session_id": session_id, "order_id": None,
            })
            event_counter += 1

            # Checkout intent is lower than cart intent; repeat-prone users are more likely to return.
            checkout_prob = (0.24 + 0.46 * affinity + 0.12 * repeat_affinity)
            checkout_prob *= CHANNEL_CONVERSION[channel] * time_effect(session_start)
            if rng.random() >= min(0.78, checkout_prob):
                continue

            timestamp += timedelta(seconds=int(rng.integers(20, 150)))
            order_id = f"O{order_counter:07d}"
            order_counter += 1
            events.append({
                "event_id": f"E{event_counter:08d}", "user_id": user.user_id,
                "event_timestamp": iso_utc(timestamp), "event_type": "checkout",
                "product_id": None, "session_id": session_id, "order_id": order_id,
            })
            event_counter += 1

            # First orders are somewhat less likely than later orders to be successful.
            success_prob = 0.77 + 0.13 * affinity + (0.035 if user_has_purchased else 0.0)
            success_prob *= CHANNEL_CONVERSION[channel]
            success_prob = float(np.clip(success_prob, 0.58, 0.94))
            draw = rng.random()
            if draw < success_prob:
                status = "completed"
            elif draw < success_prob + 0.13:
                status = "cancelled"
            else:
                status = "returned"

            orders.append({
                "order_id": order_id, "user_id": user.user_id,
                "order_date": iso_utc(timestamp), "order_status": status,
            })

            # One order contains the cart item and possibly several additional distinct products.
            item_count = int(np.clip(1 + rng.poisson(1.05 + 0.5 * engagement), 1, 5))
            other_pool = [pid for pid in product_ids if pid != cart_product]
            chosen = [cart_product]
            if item_count > 1:
                chosen.extend(rng.choice(other_pool, size=min(item_count - 1, len(other_pool)), replace=False).tolist())
            for pid in chosen:
                quantity = int(rng.choice([1, 2, 3], p=[0.82, 0.15, 0.03]))
                # Snapshot price can differ slightly from current catalogue price.
                current_price = float(product_prices[pid])
                historical_price = round(current_price * float(rng.choice([0.95, 1.0, 1.0, 1.0, 1.05])), 2)
                order_items.append({
                    "order_item_id": f"OI{item_counter:08d}", "order_id": order_id,
                    "product_id": pid, "quantity": quantity, "unit_price": historical_price,
                })
                item_counter += 1

            if status in ("completed", "returned"):
                purchase_ts = timestamp + timedelta(seconds=int(rng.integers(30, 240)))
                events.append({
                    "event_id": f"E{event_counter:08d}", "user_id": user.user_id,
                    "event_timestamp": iso_utc(purchase_ts), "event_type": "purchase",
                    "product_id": None, "session_id": session_id, "order_id": order_id,
                })
                event_counter += 1
                user_has_purchased = True

    users_out = users[["user_id", "registration_date", "acquisition_channel", "country", "device_type"]].copy()
    products_out = products.copy()
    orders_df = pd.DataFrame(orders, columns=["order_id", "user_id", "order_date", "order_status"])
    items_df = pd.DataFrame(order_items, columns=["order_item_id", "order_id", "product_id", "quantity", "unit_price"])
    events_df = pd.DataFrame(events, columns=[
        "event_id", "user_id", "event_timestamp", "event_type", "product_id", "session_id", "order_id"
    ])

    # Stable chronological order improves readability and downstream loading.
    if not events_df.empty:
        events_df["_sort"] = pd.to_datetime(events_df["event_timestamp"], utc=True)
        events_df = events_df.sort_values(["_sort", "event_id"]).drop(columns="_sort").reset_index(drop=True)
    if not orders_df.empty:
        orders_df["_sort"] = pd.to_datetime(orders_df["order_date"], utc=True)
        orders_df = orders_df.sort_values(["_sort", "order_id"]).drop(columns="_sort").reset_index(drop=True)

    return users_out, products_out, orders_df, items_df, events_df


def validate_dataset(users, products, orders, items, events) -> dict:
    errors = []

    def require(condition, message):
        if not bool(condition):
            errors.append(message)

    for name, df, key in [
        ("users", users, "user_id"), ("products", products, "product_id"),
        ("orders", orders, "order_id"), ("order_items", items, "order_item_id"),
        ("events", events, "event_id"),
    ]:
        require(df[key].notna().all(), f"{name}: NULL primary key")
        require(df[key].is_unique, f"{name}: duplicate primary key")

    user_ids = set(users["user_id"])
    product_ids = set(products["product_id"])
    order_ids = set(orders["order_id"])
    require(orders["user_id"].isin(user_ids).all(), "orders: unknown user_id")
    require(items["order_id"].isin(order_ids).all(), "order_items: unknown order_id")
    require(items["product_id"].isin(product_ids).all(), "order_items: unknown product_id")
    require(events["user_id"].isin(user_ids).all(), "events: unknown user_id")
    require(events["product_id"].dropna().isin(product_ids).all(), "events: unknown product_id")
    require(events["order_id"].dropna().isin(order_ids).all(), "events: unknown order_id")

    require((items["quantity"] > 0).all(), "order_items: quantity must be positive")
    require((items["quantity"] % 1 == 0).all(), "order_items: quantity must be integer")
    require((items["unit_price"] > 0).all(), "order_items: unit_price must be positive")
    require((products["price"] > 0).all(), "products: price must be positive")

    user_reg = users.set_index("user_id")["registration_date"].map(pd.Timestamp)
    if not orders.empty:
        order_times = pd.to_datetime(orders["order_date"], utc=True)
        order_regs = orders["user_id"].map(user_reg)
        require((order_times.dt.date >= order_regs.dt.date).all(), "orders: order precedes registration")
        require(order_times.min() >= pd.Timestamp(START_DATE, tz="UTC"), "orders: before dataset start")
        require(order_times.max() <= pd.Timestamp(END_DATE, tz="UTC") + pd.Timedelta(days=1), "orders: after dataset end")

    if not events.empty:
        event_times = pd.to_datetime(events["event_timestamp"], utc=True)
        event_regs = events["user_id"].map(user_reg)
        require((event_times.dt.date >= event_regs.dt.date).all(), "events: event precedes registration")
        require((event_times.dt.date >= START_DATE).all(), "events: before dataset start")
        require((event_times.dt.date <= END_DATE).all(), "events: after dataset end")
        require(events["event_type"].isin(["view", "add_to_cart", "checkout", "purchase"]).all(), "events: unknown event_type")

        # A signature duplicate is more useful to catch than unique event_id alone.
        sig_cols = ["user_id", "event_timestamp", "event_type", "product_id", "session_id", "order_id"]
        require(not events.duplicated(sig_cols).any(), "events: duplicate event signature")

        # Every order must have exactly one checkout; completed/returned orders exactly one purchase.
        checkout_counts = events.loc[events["event_type"].eq("checkout")].groupby("order_id").size()
        purchase_counts = events.loc[events["event_type"].eq("purchase")].groupby("order_id").size()
        require(orders["order_id"].map(checkout_counts).fillna(0).eq(1).all(), "orders: each order must have exactly one checkout event")
        expected_purchase = orders.loc[orders["order_status"].isin(["completed", "returned"]), "order_id"]
        require(expected_purchase.map(purchase_counts).fillna(0).eq(1).all(), "completed/returned orders must have exactly one purchase event")
        cancelled = orders.loc[orders["order_status"].eq("cancelled"), "order_id"]
        require(cancelled.map(purchase_counts).fillna(0).eq(0).all(), "cancelled orders must not have purchase events")

        # Checkout and purchase events must be chronologically consistent with their order.
        order_time_map = orders.set_index("order_id")["order_date"].map(lambda x: pd.Timestamp(x))
        for order_id, group in events.dropna(subset=["order_id"]).groupby("order_id"):
            if "checkout" in set(group["event_type"]):
                checkout_time = group.loc[group["event_type"].eq("checkout"), "event_timestamp"].iloc[0]
                require(pd.Timestamp(checkout_time) == order_time_map.loc[order_id], f"{order_id}: checkout timestamp differs from order_date")
            if "purchase" in set(group["event_type"]):
                purchase_time = group.loc[group["event_type"].eq("purchase"), "event_timestamp"].iloc[0]
                checkout_time = group.loc[group["event_type"].eq("checkout"), "event_timestamp"].iloc[0]
                require(pd.Timestamp(purchase_time) > pd.Timestamp(checkout_time), f"{order_id}: purchase does not follow checkout")

    # No repeated product within one order; order items are a price snapshot.
    require(not items.duplicated(["order_id", "product_id"]).any(), "order_items: duplicate product within order")

    if not orders.empty:
        item_totals = (items.assign(line_total=items["quantity"] * items["unit_price"])
                       .groupby("order_id")["line_total"].sum())
        require(set(orders["order_id"]) == set(items["order_id"]), "orders/order_items: every order must have at least one item")
        require(item_totals.index.isin(order_ids).all(), "order_items: invalid total mapping")

    require(len(users) >= 8_000, "too few users for cohort analysis")
    require(len(events) >= 10_000, "too few events for funnel/retention analysis")
    require(set(orders["order_status"].unique()).issubset({"completed", "cancelled", "returned"}), "orders: invalid status")

    if errors:
        raise ValueError("Data quality validation failed:\n - " + "\n - ".join(errors))

    status_counts = orders["order_status"].value_counts().to_dict() if not orders.empty else {}
    return {
        "users": len(users), "products": len(products), "orders": len(orders),
        "order_items": len(items), "events": len(events),
        "orders_by_status": status_counts,
        "unique_event_users": int(events["user_id"].nunique()) if not events.empty else 0,
        "purchase_events": int(events["event_type"].eq("purchase").sum()) if not events.empty else 0,
    }


def save_dataset(output_dir: Path, frames, report: dict):
    output_dir.mkdir(parents=True, exist_ok=True)
    users, products, orders, items, events = frames
    # UTF-8, ISO dates, empty strings for nullable CSV fields.
    users.to_csv(output_dir / "users.csv", index=False, encoding="utf-8")
    products.to_csv(output_dir / "products.csv", index=False, encoding="utf-8", float_format="%.2f")
    orders.to_csv(output_dir / "orders.csv", index=False, encoding="utf-8")
    items.to_csv(output_dir / "order_items.csv", index=False, encoding="utf-8", float_format="%.2f")
    events.to_csv(output_dir / "events.csv", index=False, encoding="utf-8")
    (output_dir / "generation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce CSVs for Product Analytics.")
    parser.add_argument("--output", default="data", help="Output directory (default: ./data)")
    parser.add_argument("--seed", type=int, default=SEED, help=f"Random seed (default: {SEED})")
    parser.add_argument("--users", type=int, default=N_USERS, help=f"Number of users (default: {N_USERS})")
    parser.add_argument("--products", type=int, default=N_PRODUCTS, help=f"Number of products (default: {N_PRODUCTS})")
    args = parser.parse_args()

    if args.users < 8_000:
        parser.error("--users must be at least 8000 for the intended cohort-analysis scale")
    if not 100 <= args.products <= 200:
        parser.error("--products must be between 100 and 200")

    frames = generate_dataset(seed=args.seed, n_users=args.users, n_products=args.products)
    report = validate_dataset(*frames)
    save_dataset(Path(args.output), frames, report)
    print("Dataset generated and validated.")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"CSV files saved to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
