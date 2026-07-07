from rest_framework.response import Response


class StandardResponse(Response):
    def __init__(self, data=None, message='操作成功', code=200, status=None, **kwargs):
        response_data = {
            'code': code,
            'message': message,
            'data': data
        }
        super().__init__(data=response_data, status=status or code, **kwargs)
