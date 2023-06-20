from typing import Union
import serial
import time


def write(arduino: serial.Serial, data: str):
    arduino.write(bytes(data.strip() + "\n", "utf-8"))
    arduino.flush()


def readline(arduino: serial.Serial, timeout: float = -1):
    wait_time = 0
    while True:
        data = arduino.readline().decode()
        if 0 < len(data):
            return data.strip()
        if 0 <= timeout:
            if timeout <= wait_time:
                return ""
            time.sleep(0.05)
            wait_time += 0.05


def clear_buffer(arduino: serial.Serial):
    arduino.reset_input_buffer()
    arduino.reset_output_buffer()


class ArduinoManager:
    def __init__(self, port="COM3", baudrate=115200, timeout=2) -> None:
        self.timeout = timeout
        self.port = port
        self.arduino = serial.Serial(baudrate=baudrate, timeout=self.timeout)

        self.arduino.port = self.port

        try:
            self.arduino.open()
        except:
            pass

        if self.arduino.is_open:
            time.sleep(1)  # 시리얼 통신이 열릴 때까지 약간의 딜레이가 필요한 것 같음
            clear_buffer(self.arduino)

    def clear(self):
        if self.arduino.is_open:
            clear_buffer(self.arduino)

    def write(self, line_num: int, data: str):
        if self.arduino.is_open:
            write(self.arduino, data=f"{line_num}{data}")

    def readline(self, timeout: Union[None, float] = None):
        if self.arduino.is_open:
            if timeout is None:
                timeout = self.timeout
            return readline(self.arduino, timeout=timeout)


if __name__ == "__main__":
    # clear_buffer()

    # while True:
    #     send_data = input("Data to send: ")
    #     write(send_data)
    #     received_value = readline()
    #     print(received_value)

    am = ArduinoManager()

    am.write(0, "Hello")
    am.write(1, "World!")
