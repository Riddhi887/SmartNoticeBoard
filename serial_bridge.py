try:
    import serial # pyright: ignore[reportMissingModuleSource]
except ImportError:
    raise SystemExit(
        "Missing dependency: pyserial. Install it with: python -m pip install pyserial"
    )

import importlib
import pickle
import os
from datetime import datetime

try:
    import pandas as pd  # pyright: ignore[reportMissingModuleSource]
except ImportError:
    raise SystemExit(
        "Missing dependency: pandas. Install it with: python -m pip install pandas"
    )

try:
    mysql_connector = importlib.import_module("mysql.connector")
except ImportError:
    raise SystemExit(
        "Missing dependency: mysql-connector-python. Install it with: python -m pip install mysql-connector-python"
    )

PORT       = "COM5"        # Change to your ESP32's COM port
BAUD       = 115200
MODEL_PATH = r"C:\Users\riddhi\OneDrive\Desktop\noticeboard_api\knn_model.pkl"

# ── Load ML Model
knn_model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        knn_model = pickle.load(f)
    print("ML model loaded OK")
else:
    print("WARNING: knn_model.pkl not found — ML prediction disabled")

# ── Database Connection ───────────────────────────
def get_db():
    return mysql_connector.connect(
        host="localhost",
        user="root",
        password="",                  # blank by default in XAMPP
        database="smart_notice_board"
    )

# CURRENT — real time slot from DB

def get_current(lab):
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        now      = datetime.now()
        day      = now.strftime('%A')
        time_now = now.strftime('%H:%M:%S')

        # Try practical slot first
        cur.execute("""
            SELECT subject_name, teacher_name, lab_no,
                   slot_type, batch
            FROM   timetable
            WHERE  lab_no      = %s
              AND  day_of_week = %s
              AND  start_time  <= %s
              AND  end_time    >  %s
              AND  slot_type   IN ('practical', 'class')
            LIMIT 1
        """, (lab, day, time_now, time_now))
        row = cur.fetchone()

        # If no practical, check break/free/lunch
        if not row:
            cur.execute("""
    SELECT subject_name, teacher_name, lab_no,
           slot_type, batch
    FROM   timetable
    WHERE  lab_no      = %s
      AND  day_of_week = %s
      AND  start_time  <= %s
      AND  end_time    >  %s
      AND  slot_type   IN ('practical', 'class')
    LIMIT 1
""", (lab, day, time_now, time_now))
            row = cur.fetchone()

        db.close()

        if row:
            return "{},{},{},{},{}".format(
                row['subject_name'],
                row['teacher_name'],
                row['batch'],
                row['lab_no'],
                row['slot_type']
            )
        else:
            return "College Closed,-,-,{},free".format(lab)

    except Exception as e:
        print(f"get_current error: {e}")
        return "DB Error,-,-,{},free".format(lab)

# TEST — cycles through all practical slots every 10 sec

def get_test(lab):
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT subject_name, teacher_name, lab_no,
                   slot_type, batch
            FROM   timetable
            WHERE  lab_no    = %s
              AND  slot_type = 'practical'
            ORDER  BY id
        """, (lab,))
        rows = cur.fetchall()
        db.close()

        if not rows:
            return "No Data,-,-,{},free".format(lab)

        # Cycle through slots every 10 seconds
        index = (int(datetime.now().timestamp()) // 30) % len(rows)
        row   = rows[index]

        return "{},{},{},{},{}".format(
            row['subject_name'],
            row['teacher_name'],
            row['batch'],
            row['lab_no'],
            row['slot_type']   # always 'practical' here
        )

    except Exception as e:
        print(f"get_test error: {e}")
        return "DB Error,-,-,{},free".format(lab)

# ML PREDICTION

def get_ml(lab):
    try:
        if knn_model is None:
            return "No Model,0%"

        now       = datetime.now()
        day_num   = now.weekday()
        time_mins = now.hour * 60 + now.minute

        features = pd.DataFrame([[time_mins, day_num]], columns=["time_mins", "day"])

        predicted = knn_model.predict(features)[0]
        proba     = knn_model.predict_proba(features).max() * 100

        return "{},{:.0f}%".format(predicted, proba)

    except Exception as e:
        print(f"get_ml error: {e}")
        return "ML Error,0%"


# MAIN SERIAL LOOP

def main():
    print(f"Starting serial bridge on {PORT} at {BAUD} baud...")

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"Serial port {PORT} opened successfully")
    except Exception as e:
        print(f"FATAL: Could not open serial port {PORT} — {e}")
        print("Check your COM port in Device Manager and update PORT in this script")
        return

    print("Waiting for ESP32 commands...\n")

    while True:
        try:
            # Read command from ESP32
            line = ser.readline().decode('utf-8').strip()

            if not line:
                continue

            print(f"[ESP32 -> PC] {line}")

            # Route command
            if line.startswith("GET_CURRENT:"):
                lab  = line.split(":")[1].strip()
                resp = get_current(lab)

            elif line.startswith("GET_TEST:"):
                lab  = line.split(":")[1].strip()
                resp = get_test(lab)

            elif line.startswith("GET_ML:"):
                lab  = line.split(":")[1].strip()
                resp = get_ml(lab)

            else:
                resp = "ERR,unknown command"

            # Send response back to ESP32
            print(f"[PC -> ESP32] {resp}\n")
            ser.write((resp + "\n").encode('utf-8'))

        except UnicodeDecodeError:
            # Ignore garbage bytes during ESP32 boot
            continue

        except serial.SerialException as e:
            print(f"Serial error: {e}")
            print("ESP32 disconnected. Reconnect and restart this script.")
            break

        except KeyboardInterrupt:
            print("\nStopped by user.")
            break

        except Exception as e:
            print(f"Unexpected error: {e}")
            continue

    ser.close()
    print("Serial port closed.")

if __name__ == "__main__":
    main()