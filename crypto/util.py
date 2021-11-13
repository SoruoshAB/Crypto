from rest_framework.response import Response


class Util:
    @staticmethod
    def response_generator(msg: str, status_code: int, data):
        js = {'message': msg, 'data': data}
        response = Response(js, status=status_code)
        return response
