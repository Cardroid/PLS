#include <LiquidCrystal.h>
#include <Wire.h> // I2C 라이브러리

// 핀 번호 (RS, E, DB4, DB5, DB6, DB7)
LiquidCrystal lcd(44, 45, 46, 47, 48, 49); // LCD 연결

String cmd;

void setup() {
    lcd.begin(16, 2);
    lcd.clear();
    Serial.begin(115200);
    Wire.begin();
}

void loop() {
    if (Serial.available()) {
        cmd = Serial.readStringUntil('\n');
        Serial.read();

        Serial.println("Received data: " + cmd);

        int lineNum = cmd.substring(0, 1).toInt();
        cmd = cmd.substring(1, cmd.length());

        for (int j = 0; j < 17; ++j) {
            lcd.setCursor(j, lineNum);
            if (j < cmd.length())
                lcd.write(cmd[j]);
            else
                lcd.write(' ');
        }
        delay(10);
    }
}
