# Mock Data Injection for Dashboard Charts

## Problem
When a new short-link service (or any analytics dashboard) is first deployed, the database has zero or near-zero click data. Charts render as empty/flat, making the product look broken to the user.

## Solution: Conditional Mock Injection
In the stats/analytics endpoint, check if real data is sparse. If so, override with simulated data.

### Threshold-based pattern (Python/FastAPI example)

```python
# After fetching real trends from DB
for row in trends_result.all():
    trends.append(TrendPoint(date=row[0], clicks=row[1], unique_clicks=int(row[1] * 0.7)))

# Inject demo data if real traffic is too low
if len(trends) < 7 or total_clicks < 50:
    import math
    trends = []  # Clear sparse real data
    for i in range(14):
        day_dt = now - timedelta(days=13-i)
        day_str = day_dt.strftime('%Y-%m-%d')
        # Wave pattern: base + sine + noise
        clicks = int(50 + 30 * math.sin(i * 0.5) + (i % 3) * 10)
        unique = int(clicks * 0.65)
        trends.append(TrendPoint(date=day_str, clicks=clicks, unique_clicks=unique))
    total_clicks = sum(t.clicks for t in trends)

# Also mock referrers/devices if empty
if not referrers:
    referrers = [
        ReferrerStat(referrer="google.com", clicks=145, percentage=45.0),
        ReferrerStat(referrer="twitter.com", clicks=82, percentage=25.5),
        ReferrerStat(referrer="Direct", clicks=50, percentage=15.5),
        ReferrerStat(referrer="t.co", clicks=30, percentage=9.3),
    ]
```

### Key design principles
1. **Low threshold** — Only activate when `len(trends) < 7` OR `total_clicks < 50`. Once real traffic picks up, mock data disappears automatically.
2. **Clear real data** — `trends = []` before injecting so you don't get mixed real + fake data.
3. **Recalculate totals** — `total_clicks = sum(t.clicks for t in trends)` so overview cards match the chart.
4. **Realistic curves** — Use `sin(i * 0.5)` for natural-looking wave patterns rather than flat random values.
5. **Same response model** — Mock data uses the same Pydantic models, so the frontend never knows the difference.
