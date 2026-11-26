# Project 1 study notes: questions, my answers, model answers

All questions asked while working through Project 1, with my own answer first
and the model answer after it. Use this file to revise before interviews.

## Earlier questions (Step 0)

**Q: What's the difference between `prices.shift(1)` and `prices.shift(-1)`?**
- My answer: shift(1) moves data forward, shift(-1) moves it backward and introduces look-ahead bias.
- Model answer: `shift(1)` puts yesterday's value on today's row, so today only sees the past. `shift(-1)` puts tomorrow's value on today's row, so a signal built from it uses information you couldn't have had: look-ahead bias.

**Q: Why must we never backward-fill (`bfill`) missing prices?**
- My answer: it introduces look-ahead bias and data leakage, invalidating the backtest and leading to unrealistic strategies.
- Model answer: `bfill` copies a *later* price into an earlier gap, so the past "knows" the future. The backtest then looks better than any real strategy could.

**Q: What is 5 bps, and what does a 5 bps cost take off a strategy with 200% annual turnover?**
- Model answer: 1 bp = 0.01%, so 5 bps = 0.05% of the amount traded. Annual cost drag ≈ turnover × cost = 2 × 0.05% = 0.10% a year. Our MA strategy (turnover ~1.3) loses only ~0.065% a year to costs.

## Step 1: Hypothesis
- Lesson: a hypothesis has a claim, an economic reason, a measurable test and a rejection rule, written before seeing results.
- Final version: see README section 1.

## Steps 2–3: Data fetching and cleaning (`src/qfp/data.py`)

**Q1. Why adjusted prices? What goes wrong with raw prices on a 2-for-1 split or a dividend?**
- My answer (researched, with sources): split -> the raw price halves overnight, so returns show ~-50% instead of 0%, wrecking cumulative return and volatility, and triggering false stop-loss / momentum / "buy the dip" signals. Dividend -> the price drops by the dividend on the ex-date, which looks like a loss although you received the cash; ignoring dividends understates total return, a big share of long-run equity returns.
- Model answer (say it in 20 seconds): "Raw prices contain jumps that are not real gains or losses. A 2-for-1 split halves the price, so the backtest books a fake -50% day and may fire false signals. A dividend lowers the price by the payout, so the backtest books a loss and misses the income. Adjusted prices rescale history so returns reflect what a shareholder actually earned: total return."
- Watch out: adjusted prices are back-adjusted, so old adjusted prices are not prices that actually traded. Fine for returns, not for things like "price below $5" rules.

**Q2. Why cache the download as CSV instead of downloading fresh every time?**
- My answer: to be able to test the results later on the same values.
- Model answer: "Reproducibility. Yahoo silently revises history: each new dividend or split re-scales all past adjusted prices, and bad ticks get corrected. Without a frozen copy, the same code can give a different Sharpe next month, and nobody can tell whether a change came from my code or from the data. Caching also makes runs fast, works offline, and avoids rate limits."
- Follow-up: to make the snapshot trustworthy, record the download date (or a file hash) next to the results.

**Q3. Why drop tickers with under 95% coverage instead of filling the gaps?**
- My answer: to avoid inflating the prices.
- Model answer: "Filling a big gap invents data. Forward-filling 6 months gives a flat price, i.e. fake 0% returns, which understates volatility and makes Sharpe look better than reality. If the ticker simply didn't exist yet (listed late), there's nothing honest to fill with: back-filling would use future prices. And because we later drop any incomplete row, one sparse ticker would cut those dates for every other asset too, shrinking the whole sample. Better to drop the one ticker."
- Key idea: filling doesn't change price *levels* much; it fakes *returns* (zero) and therefore *risk*.

**Q4. Why is forward-filling OK but backward-filling isn't? Why limit it to 5 days?**
- My answer: the values don't exist; backward-filling would fabricate data that isn't there.
- Model answer: "Both fill in a value that wasn't observed, so the difference isn't fabrication, it's *timing*. Forward-fill uses the last price you could actually have seen on that day: no future information. Backward-fill copies a later price into the past: look-ahead bias. The 5-day limit keeps forward-fill for short, harmless gaps (a holiday on one exchange, a missing tick). A longer gap means something real is wrong (halt, delisting, bad data), and filling it would create a long run of fake 0% returns, as in Q3."
- Key idea: ask "could I have known this value on that date?" Yes -> ffill is OK. No -> look-ahead.

**Q5. Why flag but keep one-day moves over 30%? Give one real reason a price could jump 30%.**
- My answer: someone manipulating the market, or the stock's first days of trading (IPO).
- Model answer: "A 30% day is either a real event or a data error, and the code can't tell which, so a human checks. Real causes: takeover bid, earnings shock, drug trial result, bankruptcy, IPO first-day pop, a crash. Data errors: a split missing from the adjustment, a bad tick, a wrong decimal. If it's real, it must stay: deleting your worst days hides exactly the risk you're trying to measure, so drawdown and volatility look too good. If it's an error, fix it at the source. For broad ETFs like SPY, a 30% day is almost certainly an error (SPY's worst day since 2005 was about -11%, in March 2020)."
- Key idea: never delete outliers automatically. Extreme days are where the risk lives.

## Step 4: 12-1 momentum (`strategy.momentum_12_1`)

**Q1. Why skip the most recent month? What happens to last month's biggest winners over the next few weeks?**
- My answer: for the recent months, the stocks with the biggest wins will have a bigger impact.
- Model answer: "Because of short-term reversal. Over 1 month, returns tend to *reverse*: last month's big winners often give some of it back next month (overreaction, liquidity-driven buying fading, bid-ask bounce). Over 3-12 months, returns tend to *continue* (momentum). Including the last month would mix the reversal effect into the momentum signal and weaken it, so we measure from 12 months ago to 1 month ago."
- Key idea: 1 month = reversal, 3-12 months = momentum, 3-5 years = reversal again (long-term value effect).

## Sharpe ratio: what it is and how to judge it

**Definition.** Sharpe = (average return − risk-free rate) / volatility, both annualised. "Return per unit of risk." Our code (`qfp.metrics.sharpe_ratio`): mean daily excess return / std of daily returns × √252, with risk-free = 0 by default.

**Rules of thumb (annual, after costs).** < 0.5 weak; 0.5–1 typical for stock indices and simple strategies; 1–2 good; > 2 rare for long-horizon strategies (check for a bug or look-ahead first!).

**Is it real or luck?** Standard error of a Sharpe ratio ≈ √((1 + SR²/2) / T) ≈ 1/√T, with T in years.
- t-stat ≈ SR × √T. Our 12-1 out of sample: 0.742 × √8 ≈ 2.1 -> the strategy probably does make money.
- But SE ≈ 1/√8 ≈ 0.36, so the 95% range is roughly 0.03 to 1.45. A difference of 0.004 vs buy and hold is pure noise.
- To prove a Sharpe edge of 0.1 you would need decades of data. That is why quants care about economic reasons and robustness, not tiny Sharpe gaps.

**Blind spots.** Treats upside and downside volatility the same (Sortino fixes this); assumes roughly normal returns, so it misses crash risk (short options can show a great Sharpe until they blow up); inflated by multiple testing (try 100 variants, the best looks great by luck).
