from espressoApi.espressoConnect import EspressoConnect
import json

api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
request_token="JMXVe8O_W1-2VolE7bkGf_Hy3-KxXn8i2oHsPdJS0mLhRyXItfkZj9pyiDOyQia7wnGqHqdr03hl"
secret_key="BiR30xFE5S4XC9rT0aQcz1ZdAg3CyyBz"
    
espressoApi = EspressoConnect(api_key)
session = espressoApi.generate_session(request_token,secret_key)
    
    
access_token=espressoApi.get_access_token(api_key,session)
access_token = json.loads(access_token)
print((access_token["data"]["token"]))

    
