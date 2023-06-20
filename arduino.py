from typing import Literal, Optional, Union
import serial
import time


def write(arduino: serial.Serial, data: str):
    """아두이노 시리얼 쓰기 처리

    Args:
        arduino (serial.Serial): 시리얼 포트
        data (str): 데이터
    """
    arduino.write(bytes(data.strip() + "\n", "utf-8"))
    arduino.flush()


def readline(arduino: serial.Serial, timeout: Optional[float] = None) -> str:
    """아두이노 시리얼 값 읽기 처리

    Args:
        arduino (serial.Serial): 시리얼 포트
        timeout (Optional[float], optional): 타임아웃 (None은 무한 대기). Defaults to None.

    Returns:
        str: 읽어온 문자열 데이터
    """

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
    """아두이노 읽기/쓰기 버퍼 초기화 처리

    Args:
        arduino (serial.Serial): 시리얼 포트
    """

    arduino.reset_input_buffer()
    arduino.reset_output_buffer()


class ArduinoManager:
    """아두이노 매니저"""

    def __init__(self, port="COM3", baudrate=115200, timeout=2) -> None:
        """
        Args:
            port (str, optional): 포트. Defaults to "COM3".
            baudrate (int, optional): 속도. Defaults to 115200.
            timeout (int, optional): 타임아웃. Defaults to 2.
        """

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
        """버퍼 초기화"""
        if self.arduino.is_open:
            clear_buffer(self.arduino)

    def write(self, line_num: Literal[0, 1], data: str):
        """데이터 쓰기

        Args:
            line_num (Literal[0, 1]): LCD 라인 넘버
            data (str): 데이터
        """
        if self.arduino.is_open:
            write(self.arduino, data=f"{line_num}{data}")

    def readline(self, timeout: Optional[float] = None) -> str:
        """데이터 읽어오기

        Args:
            timeout (Optional[float], optional): 타임아웃. Defaults to None.

        Returns:
            str: 데이터
        """
        if self.arduino.is_open:
            if timeout is None:
                timeout = self.timeout
            return readline(self.arduino, timeout=timeout)


if __name__ == "__main__":
    # 테스트 코드

    am = ArduinoManager()

    am.write(0, "TEST")
    am.write(1, "CODE")
