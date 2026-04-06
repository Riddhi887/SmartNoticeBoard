#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <RTClib.h>

// ── Hardware ──────────────────────────────────────
LiquidCrystal_I2C lcd(0x27, 16, 2);
RTC_DS3231 rtc;

// ── Config ────────────────────────────────────────
const char* LAB      = "312";   

// ── Timing ────────────────────────────────────────
bool TEST_MODE = false;                  // change to true for test mode
const unsigned long FETCH_MS  = TEST_MODE ? 10000 : 30000;
const unsigned long TOGGLE_MS = 5000;

// ── Data ──────────────────────────────────────────
String subjectName  = "Loading...";
String teacherName  = "Please wait";
String batchName    = "";
String labNo        = "312";
String slotType     = "free";
String mlPredicted  = "";
String mlConfidence = "";

unsigned long lastFetch  = 0;
unsigned long lastToggle = 0;
int toggleState = 0;

// ════════════════════════════════════════════════
// Send command to PC via Serial2, wait for response
// ESP32 TX2=GPIO17, RX2=GPIO16  →  connect to USB-Serial adapter to PC
// OR use Serial (USB) if PC bridge reads from same port
// ════════════════════════════════════════════════
String askPC(String command) {
    while (Serial.available()) Serial.read();
    Serial.println(command);

    unsigned long start = millis();
    String response = "";

    while (millis() - start < 6000) {
        if (Serial.available()) {
            response = Serial.readStringUntil('\n');
            response.trim();
            if (response.length() > 0) break;
        }
        delay(10);
    }
    return response;
}

// ════════════════════════════════════════════════
// Parse CSV response:  subject,teacher,batch,lab,slottype
// ════════════════════════════════════════════════
void parseCurrentResponse(String resp) {
    if (resp == "" || resp.startsWith("ERR")) {
        subjectName = "API Err";
        return;
    }
    int i0 = resp.indexOf(',');
    int i1 = resp.indexOf(',', i0 + 1);
    int i2 = resp.indexOf(',', i1 + 1);
    int i3 = resp.indexOf(',', i2 + 1);

    subjectName = resp.substring(0, i0);
    teacherName = resp.substring(i0 + 1, i1);
    batchName   = resp.substring(i1 + 1, i2);
    labNo       = resp.substring(i2 + 1, i3);
    slotType    = resp.substring(i3 + 1);
}

// ════════════════════════════════════════════════
// Parse ML response:  predicted_subject,confidence
// ════════════════════════════════════════════════
void parseMLResponse(String resp) {
    if (resp == "" || resp.startsWith("ERR")) return;
    int i0 = resp.indexOf(',');
    mlPredicted  = resp.substring(0, i0);
    mlConfidence = resp.substring(i0 + 1);
}

void fetchData() {
    String cmd  = TEST_MODE ? "GET_TEST:" : "GET_CURRENT:";
    String resp = askPC(cmd + String(LAB));
    parseCurrentResponse(resp);
}

void fetchML() {
    String resp = askPC("GET_ML:" + String(LAB));
    parseMLResponse(resp);
}

// ════════════════════════════════════════════════
// Row 1 — Time + Date
// ════════════════════════════════════════════════
void printRow1(DateTime &now) {
    lcd.setCursor(0, 0);
    if (now.hour()   < 10) lcd.print("0");
    lcd.print(now.hour());   lcd.print(":");
    if (now.minute() < 10) lcd.print("0");
    lcd.print(now.minute()); lcd.print(":");
    if (now.second() < 10) lcd.print("0");
    lcd.print(now.second()); lcd.print(" ");
    if (now.day()    < 10) lcd.print("0");
    lcd.print(now.day());    lcd.print("/");
    if (now.month()  < 10) lcd.print("0");
    lcd.print(now.month());
}

// ════════════════════════════════════════════════
// Row 2 — Cycles: Subject+Lab → Batch+Teacher → ML vs DB
// ════════════════════════════════════════════════
void printRow2() {
    lcd.setCursor(0, 1);
    lcd.print("                ");
    lcd.setCursor(0, 1);

    if (slotType == "break") { lcd.print("--Short Break---"); return; }
    if (slotType == "lunch") { lcd.print("--Lunch Break---"); return; }
    if (slotType == "free")  { lcd.print("  No Lab Now    "); return; }

    if (toggleState == 0) {
        String disp = subjectName;
        if (disp.length() > 7) disp = disp.substring(0, 7);
        while (disp.length() < 8) disp += " ";
        disp += "L" + labNo;
        lcd.print(disp.substring(0, 16));

    }else if (toggleState == 1) {
    String disp = "Bat:" + batchName + " Pr:" + teacherName;
    if (disp.length() > 16) disp = disp.substring(0, 16);
    lcd.print(disp);

    } else {
    String db_s = subjectName.substring(0, min((int)subjectName.length(), 5));
    String ml_s = mlPredicted.length() > 0
                  ? mlPredicted.substring(0, min((int)mlPredicted.length(), 5))
                  : "N/A";
    String disp = "TT:" + db_s + " Pred:" + ml_s;
    if (disp.length() > 16) disp = disp.substring(0, 16);
    lcd.print(disp);
}
}

// ════════════════════════════════════════════════
// SETUP
// ════════════════════════════════════════════════
void setup() {
    Serial.begin(115200);
    Wire.begin();

    lcd.init();
    lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print("Lab E-312 Board ");
    lcd.setCursor(0, 1);
    lcd.print("Starting...     ");

    if (!rtc.begin()) {
        lcd.setCursor(0, 1);
        lcd.print("RTC FAILED!     ");
        while (1);
    }
    // Comment out after first upload:
   // rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));

    delay(5000);  // give PC time to release port after upload

    fetchData();
    fetchML();

    lcd.clear();
    lastFetch  = millis();
    lastToggle = millis();
}

// ════════════════════════════════════════════════
// LOOP
// ════════════════════════════════════════════════
void loop() {
    unsigned long now_ms = millis();

    if (now_ms - lastFetch >= FETCH_MS) {
        fetchData();
        fetchML();
        lastFetch = now_ms;
        lcd.clear();
    }

    if (now_ms - lastToggle >= TOGGLE_MS) {
        toggleState = (toggleState + 1) % 3;
        lastToggle  = now_ms;
    }

    DateTime now = rtc.now();
    printRow1(now);
    printRow2();

    delay(1000);
}