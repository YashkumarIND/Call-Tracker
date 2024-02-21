from espressoApi.espressoConnect import EspressoConnect

def get_access_token(api_key, request_token, secret_key):
    espressoApi = EspressoConnect(api_key)
    session = espressoApi.generate_session(request_token, secret_key)
    access_token = espressoApi.get_access_token(api_key, session)
    return access_token

# Example usage:
api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
request_token = "acXVRMyfOmqkSMdOraRuXd3Q-8SsFngL9Ky-UYB_xVfhRyXItfkZj9rROcs_tL5TovxGLriM_f3W"
secret_key = "BiR30xFE5S4XC9rT0aQcz1ZdAg3CyyBz"

access_token = get_access_token(api_key, request_token, secret_key)
print(access_token)
