#  #package import statement
from espressoApi.espressoConnect import EspressoConnect
# # Rest of your code using the cryptography library

# # Make a object call

api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
# #vendor_key = "HVRSIHGGnHDDFURcjdZChvnclipT8ITE"  # Include your Vendor Key here
    
espressoApi = EspressoConnect(api_key)
    
# # Print the login url
    
# """ Pass vendor_key if it is needed """
    
login_url = espressoApi.login_url()
print("Login URL:", login_url)

    

