from espressoApi.espressoConnect import EspressoConnect


api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
request_token="Q5PWaqiQDhuNZuhcqsAvc-bz9NOxUFo7kaPgQtN9glfhRyXItfkZj9rHlkEtRMvXnJMQNURP2r6W"
secret_key="BiR30xFE5S4XC9rT0aQcz1ZdAg3CyyBz"
    
espressoApi = EspressoConnect(api_key)
session = espressoApi.generate_session(request_token,secret_key)
    
    
access_token=espressoApi.get_access_token(api_key,session)
# print(access_token)
    
