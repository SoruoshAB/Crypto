import os
from random import randint
from dotenv import load_dotenv

from zeep import Client


class soapapi:
    basePath = "https://raygansms.com/FastSend.asmx?WSDL"

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def SendMessageWithCode(self, ReciptionNumber, Code):
        client = Client(self.basePath)
        result = client.service.SendMessageWithCode(self.username, self.password, ReciptionNumber, Code)
        return result

    @staticmethod
    def send_otp(phone_number: str = '09136025944'):
        code = randint(100000, 999999)
        msa = str("کد اعتبار سنجی شما در ????? : " + "\n " + str(code))
        load_dotenv()
        env = os.environ.get
        user_name_OTP = env("USER_NAME_OTP")
        password_OTP = env("PASSWORD_OTP")
        # OTP = soapapi(user_name_OTP, password_OTP).SendMessageWithCode(phone_number, msa)
        print("code: ", code)
        return code
