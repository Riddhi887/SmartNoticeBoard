from flask import Flask, jsonify
import mysql.connector
from datetime import datetime
import pickle
import pandas as pd
import os

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",                  # blank by default in XAMPP
        database="smart_notice_board"
    )

def fmt_time(td):
    if td is None:
        return "-"
    total = int(td.total_seconds())
    h, m  = divmod(total // 60, 60)
    return f"{h:02d}:{m:02d}"

MODEL_PATH = "knn_model.pkl"
knn_model  = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        knn_model = pickle.load(f)


# ROUTE 1 — Real time (uses actual clock)
# Arduino calls: GET /current/E312

@app.route('/current/<lab>')
def current_subject(lab):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    now      = datetime.now()
    day      = now.strftime('%A')
    time_now = now.strftime('%H:%M:%S')

    # First try to find a class slot for any batch in this lab
    cur.execute("""
        SELECT subject_name, teacher_name, lab_no,
               slot_type, batch, start_time, end_time
        FROM   timetable
        WHERE  lab_no      = %s
          AND  day_of_week = %s
          AND  start_time  <= %s
          AND  end_time    >  %s
          AND  slot_type   = 'practical'
        LIMIT 1
    """, (lab, day, time_now, time_now))
    row = cur.fetchone()

    # If no practical, check break/free using batch='E312'
    if not row:
        cur.execute("""
            SELECT subject_name, teacher_name, lab_no,
                   slot_type, batch, start_time, end_time
            FROM   timetable
            WHERE  batch       = %s
              AND  day_of_week = %s
              AND  start_time  <= %s
              AND  end_time    >  %s
        """, ('E' + str(lab), day, time_now, time_now))
        row = cur.fetchone()

    db.close()

    if row:
        row['start_time'] = fmt_time(row['start_time'])
        row['end_time']   = fmt_time(row['end_time'])
        row['mode']       = 'real'
        return jsonify(row)
    else:
        return jsonify({
            "subject_name": "College Closed",
            "teacher_name": "-",
            "batch": "-",
            "lab_no": lab,
            "slot_type": "free",
            "start_time": "-",
            "end_time": "-",
            "mode": "real"
        })


# ROUTE 2 — Test mode (cycles every 10s)
# Arduino calls: GET /test/E312

@app.route('/test/<lab>')
def test_mode(lab):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT subject_name, teacher_name, lab_no,
               slot_type, batch, start_time, end_time
        FROM   timetable
        WHERE  lab_no    = %s
          AND  slot_type = 'practical'
        ORDER  BY day_of_week, start_time
    """, (lab,))
    rows = cur.fetchall()
    db.close()

    if not rows:
        return jsonify({"subject_name": "No Data",
                        "teacher_name": "-", "batch": "-",
                        "lab_no": lab, "slot_type": "free"})

    index = (int(datetime.now().timestamp()) // 10) % len(rows)
    row   = rows[index]
    row['start_time'] = fmt_time(row['start_time'])
    row['end_time']   = fmt_time(row['end_time'])
    row['mode']       = 'test'
    return jsonify(row)

# ROUTE 3 — ML prediction
# Arduino calls: GET /predict/312

@app.route('/predict/<lab>')
def predict(lab):
    if knn_model is None:
        return jsonify({"predicted_subject": "No Model",
                        "confidence": "0%", "mode": "ml"})
    now       = datetime.now()
    day_num   = now.weekday()
    time_mins = now.hour * 60 + now.minute
    features  = pd.DataFrame([[time_mins, day_num]],
                              columns=["time_mins", "day"])
    predicted = knn_model.predict(features)[0]
    proba     = knn_model.predict_proba(features).max() * 100
    return jsonify({
        "predicted_subject": predicted,
        "confidence": f"{proba:.0f}%",
        "mode": "ml"
    })


# ROUTE 4 — Health check
# Open in browser: http://localhost:5000/

@app.route('/')
def health():
    return jsonify({
        "status": "running",
        "time": datetime.now().strftime('%H:%M:%S'),
        "ml_loaded": knn_model is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)