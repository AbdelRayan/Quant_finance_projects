# Project 4: Doughnut surface for trading-volume forecasts

Forecast 15-minute trading volume from two repeating clocks: **time of day**
(wraps at midnight UTC) and **position in the calendar month** (wraps at the
month boundary). Each cycle is encoded with sine and cosine so 23:45 sits next
to 00:00 and the 31st next to the 1st. Together the two phases form a torus.

Same idea as Project 2's calendar phase, now with two clocks and their interaction.

## Status

- [x] Simulation proof of concept (`torus_volume.py`)
- [ ] Real intraday volume data
- [ ] Stronger baselines and features (see plan below)
- [ ] Results and limitations write-up

## Simulation results

Ordinary least squares, fitted on 2024 (35,136 intervals), tested on Jan–Jun
2025 (17,376 intervals). Volume is simulated with a fixed seed.

| Model | Features | Test RMSE (volume units) |
|---|---|---|
| Additive | Intercept + daily (cos, sin) + monthly (cos, sin) | 14.43 |
| With interactions | Additive + 4 products of daily × monthly sine/cosine | 8.00 |

The interaction model cuts test RMSE by 44.6%. The simulation builds in a
reversal at 16:00 UTC: volume is higher at that hour near the turn of the month
and lower mid-month. Only the interaction terms can represent that, and their
error matches the simulated noise standard deviation (8 units), the best
any model can do.

![Forecast heatmaps and torus](torus_volume.png)

Left: additive model. Middle: model with interactions. Right: the middle
heatmap wrapped onto a doughnut (time of day around the ring, position in the
month around the tube).

**Caveat:** the simulated volume is generated from exactly the interaction
model's functional form, so this shows the method *can* recover such a pattern,
not that real markets have one. That is what the real-data step tests.

## Run

    python projects/04_torus_volume/torus_volume.py

Prints the results and saves `torus_volume.png` next to the script.

## Plan for real data

1. **Data.** Crypto (e.g. BTC-USDT spot) has years of free 15-minute bars and
   trades 24/7, so the UTC time-of-day clock covers the full circle. For
   equities, yfinance gives 15-minute bars for only ~60 days (hourly for ~2
   years); use the exchange's local time, not UTC, because daylight saving
   moves the US open between 13:30 and 14:30 UTC.
2. **Target.** Model log volume: volume is skewed and multiplicative, and
   errors are then in percent.
3. **Baselines to beat.** (a) Same slot's average over the last 20 days, the
   standard "volume curve" used by execution desks; (b) yesterday's volume in
   the same slot.
4. **More features.** Higher harmonics (k = 2, 3) for the sharp open/close
   spikes; day of week; recent volume level (volume is persistent);
   event flags: month-end and index rebalances, options expiry (3rd Friday),
   FOMC and CPI days.
5. **Evaluation.** Walk-forward (refit monthly, predict the next month), RMSE
   and MAPE on log volume, compared with the baselines.

Why it matters: execution algorithms (VWAP) split large orders in proportion
to forecast volume, so better intraday volume curves mean lower trading costs.
