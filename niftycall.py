from flask import Flask, render_template, request, jsonify, redirect, url_for
import yfinance as yf
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import numpy as np
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# GLOBAL STATE
FNO_STOCKS = {'NIFTY50': '^NSEI'}
latest_triggers = {}
backtest_results = []
backtest_running = False
email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]
monitoring_active = False

def safe_float(value):
    try:
        if pd.isna(value) or value is None:
            return None
        if hasattr(value, 'iloc'):
            return float(value.iloc[0]) if len(value) > 0 else None
        return float(value)
    except:
        return None

def get_nifty_daily_data():
    """Get LAST 25 TRADING DAYS - TODAY FIRST"""
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="1mo")
        data.index = data.index.tz_localize(None)
        data = data.dropna()
        print(f"✅ LAST {len(data)} DAYS | TODAY: {data.index[-1].strftime('%m/%d/%Y')}")
        return data.tail(25)
    except:
        return pd.DataFrame()

def send_email(recipients, symbol, signals):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["app_password"]

        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        subject = f"🚨 NIFTY50 FIBONACCI: {symbol}"
        
        if symbol == "BACKTEST-REPORT":
            global backtest_results
            triggers = [r for r in backtest_results if r['trigger'] == 'TRIGGER']
            total_days = len(backtest_results)
            hit_rate = (len(triggers) / total_days * 100) if total_days > 0 else 0
            
            body = f"""🔥 NIFTY50 FIBONACCI BACKTEST REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📊 Period: {backtest_results[0]['date']} → {backtest_results[-1]['date']}
🎯 Triggers: {len(triggers)} / {total_days} days
📈 Hit Rate: {hit_rate:.1f}%

🔥 TOP 5 TRIGGERS:
"""
            for trigger in triggers[-5:]:
                body += f"""🔔 {trigger['date']}
   Buy 50%: ₹{trigger['buy_50']}
   SL: ₹{trigger['sl']}
   T1: ₹{trigger['target1'][:7]}

"""
            body += f"🔗 LIVE DASHBOARD: http://192.168.0.45:9000"
        else:
            body = f"""🔥 NIFTY50 LIVE TRADING ALERT
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📈 Buy 50%: ₹{signals.get('buy_50', 0):,.0f}
🛑 SL: ₹{signals.get('sl', 0):,.0f}
🎯 T1: ₹{signals.get('target1', 0):,.0f}

🔗 DASHBOARD: http://192.168.0.45:9000
"""
        
        # FIXED: NEW message for EACH recipient
        for recipient in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient  # SINGLE To header only
            
            server.send_message(msg)
            print(f"✅ EMAIL SENT → {recipient}")
        
        server.quit()
        print(f"📧 SUCCESS: {symbol} → {len(recipients)} emails")
        return True
        
    except Exception as e:
        print(f"❌ EMAIL ERROR: {str(e)}")
        return False

def run_historical_backtest():
    """LAST 20 TRADING DAYS - Feb 10 TODAY at TOP"""
    global backtest_results, backtest_running
    if backtest_running: 
        print("⏳ Backtest already running...")
        return
    
    backtest_running = True
    backtest_results.clear()
    
    print("🔥 RUNNING NIFTY50 BACKTEST...")
    data = get_nifty_daily_data()
    
    if len(data) < 10:
        print("❌ Insufficient data")
        backtest_running = False
        return
    
    signals_found = 0
    for i in range(len(data)-1, 0, -1):  # Today → Backwards
        today_date = data.index[i].strftime('%m/%d/%Y')
        today_open = safe_float(data['Open'].iloc[i])
        yest_low = safe_float(data['Low'].iloc[i-1])
        yest_high = safe_float(data['High'].iloc[i-1])
        
        print(f"📅 {today_date}: Open={today_open:.0f}")
        
        if today_open is None or yest_low is None or yest_high is None:
            continue
        
        case1 = "YES" if today_open > yest_low else "NO"
        range_size = today_open - yest_low
        
        if range_size <= 0:
            backtest_results.append({
                'date': today_date, 'today_open': f"{today_open:.0f}",
                'yest_low': f"{yest_low:.0f}", 'yest_high': f"{yest_high:.0f}",
                'case1': case1, 'acceptance': 'NO', 'trigger': 'NO TRADE',
                'buy_618': '0.00', 'buy_50': '0.00', 'buy_382': '0.00',
                'sl': f"{yest_low:.0f}", 'target1': '0.00', 'target2': '0.00', 'target3': '0.00'
            })
            continue
        
        buy_618 = yest_low + 0.618 * range_size
        buy_50 = yest_low + 0.5 * range_size
        buy_382 = yest_low + 0.382 * range_size
        
        acceptance = "YES" if (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high) else "NO"
        trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
        
        target1 = today_open + 0.382 * range_size
        target2 = today_open + 0.5 * range_size
        target3 = today_open + 1.0 * range_size
        
        result = {
            'date': today_date,
            'today_open': f"{today_open:.2f}",
            'yest_low': f"{yest_low:.1f}",
            'yest_high': f"{yest_high:.1f}",
            'case1': case1,
            'acceptance': acceptance,
            'trigger': trigger,
            'buy_618': f"{buy_618:.4f}",
            'buy_50': f"{buy_50:.3f}",
            'buy_382': f"{buy_382:.4f}",
            'sl': f"{yest_low:.1f}",
            'target1': f"{target1:.4f}",
            'target2': f"{target2:.4f}",
            'target3': f"{target3:.4f}"
        }
        
        backtest_results.append(result)
        if trigger == "TRIGGER":
            signals_found += 1
            print(f"  🎯 TRIGGER #{signals_found}: {today_date}")
    
    print(f"✅ BACKTEST COMPLETE: {signals_found} TRIGGERS | {backtest_results[0]['date']} → {backtest_results[-1]['date']}")
    backtest_running = False

# ROUTES
@app.route('/test_trigger')
def test_trigger():
    signals = {'buy_50': 25850, 'sl': 25750, 'target1': 25950}
    threading.Thread(target=send_email, args=(email_recipients, 'LIVE-TEST', signals), daemon=True).start()
    return redirect(url_for('dashboard'))

@app.route('/send_backtest_report')
def send_backtest_report():
    global backtest_results
    if not backtest_results:
        print("❌ No backtest data!")
        return redirect(url_for('dashboard'))
    
    print("📧 SENDING BACKTEST REPORT...")
    threading.Thread(target=send_email, args=(email_recipients, "BACKTEST-REPORT", {}), daemon=True).start()
    return redirect(url_for('dashboard'))

@app.route('/api/backtest')
def api_backtest():
    return jsonify(backtest_results[-20:])  # Last 20 days

@app.route('/run_backtest')
def run_backtest():
    threading.Thread(target=run_historical_backtest, daemon=True).start()
    return redirect(url_for('dashboard'))

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/start_monitoring')
def start_monitoring():
    global monitoring_active
    monitoring_active = True
    print("▶️ Live monitoring started")
    return redirect(url_for('dashboard'))

@app.route('/stop_monitoring')
def stop_monitoring():
    global monitoring_active
    monitoring_active = False
    print("⏹️ Live monitoring stopped")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("🚀 NIFTY50 FIBONACCI SCANNER - ALL FIXED!")
    app.run(debug=True, host='0.0.0.0', port=9000)
