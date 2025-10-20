# Enhanced Stock Market Depth Analysis System

A sophisticated real-time stock monitoring system that analyzes market depth data, calculates multi-factor signals, and provides intelligent trading recommendations.

## 🚀 Features

### Enhanced Decision Making System
- **Multi-factor composite scoring (0-100 points)** with weighted analysis
- **Historical trend analysis** using rolling buffers
- **Advanced order book imbalance detection** across multiple price levels
- **Price momentum tracking** and velocity calculations
- **Smart notification system** with cooldown periods
- **Risk-aware spread analysis** and liquidity assessment

### Key Decision Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| **Basic Ratio Strength** | 0-25 pts | Bid/Ask volume ratio above 1.0 |
| **Ratio Velocity** | 0-20 pts | Rate of change in ratio over recent snapshots |
| **Weighted Imbalance** | 0-20 pts | Multi-level order book imbalance (price-weighted) |
| **Price Momentum** | 0-15 pts | Short-term price movement acceleration |
| **Activity/Depth Bonus** | 0-10 pts | Market depth and liquidity assessment |
| **Consistency Bonus** | 0-10 pts | Sustained upward trend confirmation |
| **Spread Penalty** | 0 to -10 pts | Wide spread execution cost penalty |

### Alert Thresholds

- 🚀 **STRONG RECOMMEND**: Score ≥ 60 + Ratio > 1
- 📊 **MEDIUM SIGNAL**: Score ≥ 40 + Ratio > 1  
- ⚠️ **TAKE CARE**: Ratio drops below 1 (from above 1)
- 🔄 **Cooldown**: 5-minute minimum between alerts per stock

## 📋 Configuration

### System Parameters
```python
REQUEST_TIMEOUT = 5          # seconds per HTTP request
MAX_WORKERS = 12             # thread pool size
INTERVAL_SECONDS = 10        # loop interval seconds
START_TIME = dtime(10, 0)    # trading start time
END_TIME = dtime(14, 15)     # trading end time
HISTORY_SIZE = 10            # rolling buffer size
cooldown_minutes = 5         # alert cooldown period
```

### Database Schema
The system uses Oracle DB with three main tables:

#### STOCK_PRICE_DEPTH
- `ID` (Primary Key)
- `STOCK_CODE` (VARCHAR2)
- `SNAPSHOT_TIMESTAMP` (TIMESTAMP)
- `TOTAL_BIDS` (NUMBER)
- `TOTAL_ASKS` (NUMBER)

#### BIDS_PER_PRICE / ASKS_PER_PRICE
- `DEPTH_ID` (Foreign Key)
- `ORDER_PRICE` (NUMBER)
- `VOLUME_TRADED` (NUMBER)
- `SPLIT` (NUMBER)
- `VOLUME_TRADED_CUM_SUM` (NUMBER)

## 📁 File Structure

```
Stock Analysis/
├── price_depth.py          # Main monitoring script
├── STOCKS.csv             # Stock list with API endpoints
├── notification_log.txt   # Alert history log
├── building_visuals.ipynb # Analysis notebook
└── README.md              # This documentation
```

### STOCKS.csv Format
```csv
# This is a comment line (ignored)
STOCK_CODE,API_ENDPOINT_ID
AMER,a0da702c-a24d-400c-b21f-9800c6e9a901
ARCC,58338a21-6a90-482f-a6b0-0f7fb3ee8a6a
# TEMP_DISABLED,temp-id-here
```

**Comment Support**: Lines starting with `#` are automatically ignored, allowing you to temporarily disable stocks without deleting entries.

## 🎯 Signal Quality Improvements

### Multi-Level Analysis
- **Order Book Depth**: Analyzes beyond just best bid/ask
- **Weighted Imbalance**: Price-level weighted volume analysis
- **Trend Confirmation**: Requires consistent signals across multiple snapshots
- **Execution Cost Awareness**: Penalizes wide spreads that impact trade execution

### False Positive Reduction
- **Composite Scoring**: Multiple independent factors must align
- **Historical Context**: Considers recent price and ratio trends
- **Market Conditions**: Adapts to liquidity and volatility
- **Cooldown Periods**: Prevents alert spam for same stock

## 🔧 Usage

### Running the System
```bash
cd "Stock Analysis"
python price_depth.py
```

### System Startup Display
```
============================================================
📊 ENHANCED STOCK MONITORING SYSTEM
============================================================
📋 Configuration:
  • Monitored stocks: 42
  • Trading hours: 10:00:00 - 14:15:00
  • Fetch interval: 10s
  • Max workers: 12
  • History buffer: 10 snapshots
  • Recommendation cooldown: 5 minutes

🎯 Enhanced Decision Factors:
  • Basic ratio strength (0-25 pts)
  • Ratio velocity/momentum (0-20 pts)
  • Multi-level order imbalance (0-20 pts)
  • Price momentum (0-15 pts)
  • Depth/activity bonus (0-10 pts)
  • Consistency bonus (0-10 pts)
  • Spread penalty (0 to -10 pts)

🚨 Alert Thresholds:
  • STRONG RECOMMEND: Score ≥ 60 + Ratio > 1
  • MEDIUM SIGNAL: Score ≥ 40 + Ratio > 1
  • TAKE CARE: Ratio drops below 1
============================================================
```

### Sample Output
```
=== Summary of Tracked Stocks (42 total) ===
🚀 STRONG RECOMMENDATIONS (2): AMER, ARCC
⚠️  TAKE CARE ALERTS (1): SUGR
📊 Top 5 Scoring Stocks:
  AMER: Score=73.2, Ratio=1.45, Change=+12.3%
  ARCC: Score=61.8, Ratio=1.32, Change=+8.7%
  ENGC: Score=45.1, Ratio=1.28, Change=+5.2%
  LCSW: Score=38.9, Ratio=1.15, Change=+2.1%
  ZMID: Score=32.4, Ratio=1.08, Change=+1.8%
📈 Market Overview: 15/42 stocks with ratio > 1, Avg Score: 24.3
============================================================
```

## 📊 Monitoring & Logs

### Log Files
- **notification_log.txt**: Timestamped alerts and analysis
- **Detailed scoring**: Factor breakdown for high-scoring stocks
- **System events**: Errors, retries, and status updates

### Log Format Examples
```
2025-10-18 10:27:45: STRONG RECOMMEND: AMER: Score=73.2, Ratio=1.45, Change=+12.3%
2025-10-18 10:27:45: AMER Score=73.2: Ratio=1.45 (+11.2), Velocity=0.045 (+9.0), Imbalance=1.31 (+6.2), PriceMomentum=2.34% (+11.7), Consistency (+10), Depth=18 (+4.0)
2025-10-18 10:27:47: TAKE CARE: SUGR: Ratio dropped below 1! Previous=1.23, Now=0.89, Score=15.4
```

## ⚙️ Customization

### Adjusting Thresholds
Modify these values in `process_notifications()`:
```python
# STRONG RECOMMEND threshold
if score >= 60 and ratio > 1:

# MEDIUM SIGNAL threshold  
elif score >= 40 and ratio > 1:

# Cooldown period
cooldown_minutes = 5
```

### Scoring Weights
Adjust factor weights in `calculate_signal_score()`:
```python
ratio_score = min(25, (ratio - 1) * 25)        # Max 25 points
velocity_score = min(20, velocity * 50)        # Max 20 points
imbalance_score = min(20, (imbalance - 1) * 20) # Max 20 points
# ... etc
```

## 🔐 Security & Authentication

- **Bearer Token**: Update `TOKEN` variable with valid API credentials
- **Database Connection**: Configure Oracle DB credentials in connection string
- **API Rate Limits**: Built-in exponential backoff and retry logic

## 🚨 Error Handling

### Robust Retry Logic
- **Infinite retries** with exponential backoff
- **Token expiry detection** and graceful shutdown
- **Network timeout handling** with configurable limits
- **Database transaction rollback** on errors

### Fallback Mechanisms
- **Scoring fallback**: Basic ratio scoring if advanced calculation fails
- **Data validation**: `to_number()` function handles malformed data
- **Connection resilience**: Per-request database connections

## 📈 Performance Optimizations

### Concurrency
- **ThreadPoolExecutor**: Parallel stock data fetching
- **Thread-safe operations**: Protected shared state with locks
- **Resource management**: Bounded thread pool and connection limits

### Memory Management
- **Rolling buffers**: Fixed-size deques prevent memory growth
- **Data cleanup**: Regular clearing of temporary state
- **Efficient storage**: Minimal historical data retention

## 🔧 Dependencies

```python
import oracledb          # Oracle database connectivity
import requests          # HTTP API calls
import win10toast        # Windows notifications
import concurrent.futures # Threading
import collections       # deque for rolling buffers
import statistics        # Mathematical operations
```

## 📝 Changelog

### Version 2.0 (Latest)
- ✅ Multi-factor composite scoring system
- ✅ Historical trend analysis with rolling buffers
- ✅ Advanced order book imbalance detection
- ✅ Price momentum and velocity calculations
- ✅ Smart cooldown and notification management
- ✅ CSV comment support for stock management
- ✅ Enhanced error handling and fallback mechanisms
- ✅ Comprehensive logging and system status display

### Version 1.0 (Previous)
- Basic bid/ask ratio monitoring
- Simple threshold-based alerts
- Oracle database persistence
- Threading for parallel execution

## 🎯 Future Enhancements

- [ ] Machine learning model integration
- [ ] Cross-stock correlation analysis
- [ ] Intraday volatility adjustment
- [ ] Real-time trade confirmation integration
- [ ] Web dashboard for monitoring
- [ ] Backtesting framework
- [ ] Performance analytics and reporting

---

*For questions or issues, check the notification logs for detailed error information and system behavior analysis.*