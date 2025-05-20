from typing import Dict, Any, Type, TypeVar, Optional, Tuple, List
import boto3
import logging
import inspect
import os
from urllib.parse import quote
import requests

from pydantic import BaseModel, Field, ValidationError, Extra, parse_obj_as
import streamlit as st

## Create Logger 
logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)

logger.setLevel(os.getenv("LOG_LEVEL","INFO"))

### Create Cognito Client 
app_client_id = os.getenv("COGNITO_CLIENT_ID",None)
user_pool_id=os.getenv("COGNITO_POOL_ID",None)
cognito_client = boto3.client("cognito-idp", 
                              region_name=user_pool_id.split("_")[0] if user_pool_id else boto3.Session().region_name)

cognito_domain = cognito_client.describe_user_pool(UserPoolId=user_pool_id)['UserPool']['Domain']
redirect_uri = cognito_client.describe_user_pool_client(
                UserPoolId=user_pool_id,
                ClientId=app_client_id)['UserPoolClient']['CallbackURLs'][0]


CR = TypeVar('CR', bound='UserInfo')

class UserInfo(BaseModel, extra=Extra.allow):
    IsLoggedIn: bool = Field(False, description="User login state")
    Email: Optional[str] = Field(None, min_length=0)
    UserName: Optional[str] = Field(None, min_length=0)
    Group: Optional[str] = Field(None, min_length=0)
    Groups: Optional[List[str]] = Field(None, min_length=0)

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(IsLoggedIn={self.IsLoggedIn}, "
            f"Email={self.Email}, "
            f"UserName={self.UserName}, "
            f"Group={self.Group})"
            f"(Groups={self.Groups})"
        )

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_cognito_response(cls, cognito_response: Dict) -> 'UserInfo':
        """Convert Cognito response to UserInfo object"""
        # Initialize default values
        email = None
        username = cognito_response.get('Username')

        # Extract email from UserAttributes
        user_attributes = cognito_response.get('UserAttributes', [])
        for attr in user_attributes:
            if attr.get('Name') == 'email':
                email = attr.get('Value')
                break
        
        # Get user groups
        groups = UserInfo.get_user_groups(username)
        
        # Set primary group if any groups exist
        primary_group = groups[0] if groups else None

        # Create UserInfo instance
        return cls(
            IsLoggedIn=True,  # Since we have user data, they must be logged in
            Email=email,
            UserName=username,
            Group=primary_group,
            Groups=groups
        )
    
    @classmethod
    def get_user_groups(cls,username: str) -> List[str]:
        """Get user's groups from Cognito"""
        try:
            response = cognito_client.admin_list_groups_for_user(
                Username=username,
                UserPoolId=user_pool_id
            )
            return [group['GroupName'] for group in response.get('Groups', [])]
        except Exception as e:
            logger.error(f"Error getting user groups: {str(e)}")
            return []

class CognitoAuthenticator(): 
    def __init__(
        self
    ):
        if 'UserInfo' not in st.session_state:
            self.User = UserInfo(IsLoggedIn=False)
            st.session_state['UserInfo'] = UserInfo(IsLoggedIn=False)
        else :
            self.User = st.session_state['UserInfo']

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(pool_id={self.pool_id}, "
            f"app_client_id={self.app_client_id})"
            f"(User={self.User})"
        )
    
    def __repr__(self):
        return self.__str__()
    

    def _authenticate(self,username,password):
        logger.info(f"Execution Started : {self.__class__.__name__} - {inspect.currentframe().f_code.co_name}")
        try:
            response = cognito_client.initiate_auth(

                ClientId= app_client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            #Get the token if user is authenticated 
            token = response['AuthenticationResult']['AccessToken']
            self._get_user_info(token)
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            st.error(f"Authentication failed: {str(e)}")


    def _get_user_info(self,token):
        logger.info(f"Execution Started : {self.__class__.__name__} - {inspect.currentframe().f_code.co_name}")

        try:
            # Verify the token and get user information
            user_info = cognito_client.get_user(AccessToken=token)

            # Log information
            logger.info(f"User Info from Cognito:\n {user_info}")

            self.User = UserInfo.from_cognito_response(user_info)
            st.session_state['UserInfo'] = self.User

        except Exception as e:
            logger.error(f"Authentication failed:  {self.__class__.__name__} - {inspect.currentframe().f_code.co_name} {str(e)}")
            st.error(f"Authentication failed: {str(e)}")

    def login_from_code(self,auth_code):
        logger.info(f"Execution Started : {self.__class__.__name__} - {inspect.currentframe().f_code.co_name}")

        token_url = f"https://{cognito_domain}.auth.{cognito_client.meta.region_name}.amazoncognito.com/oauth2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": app_client_id,
            "client_secret": None,
            "code": auth_code,
            "redirect_uri": redirect_uri
        }
        try:
            # Get the tokens in the exchange of auth code 
            response = requests.post(token_url, data=data)
            access_token = response.json()['access_token']
            self._get_user_info(access_token)
            st.rerun()

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            st.error(f"Authentication failed: {str(e)}")
    
        

    def login(self):
        logger.info(f"Execution Started : {self.__class__.__name__} - {inspect.currentframe().f_code.co_name}")

        forgot_password_url=(  
            f"https://{cognito_domain}.auth.{cognito_client.meta.region_name}.amazoncognito.com/forgotPassword?"
            f"client_id={app_client_id}&response_type=code&scope=email+openid+profile&"
            f"redirect_uri={redirect_uri}" 
        )
        signup_url = ( 
            f"https://{cognito_domain}.auth.{cognito_client.meta.region_name}.amazoncognito.com/signup?client_id="
            f"{app_client_id}&response_type=code&scope=email+openid+profile&"
            f"redirect_uri={redirect_uri}"
        )
                        
        st.empty()
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            col = st.columns((1, 1, 1))
            with col[0]:
                if st.form_submit_button("Login",type="primary"):
                    self._authenticate(username, password)
                    st.rerun()

            with col[1]:
                st.link_button("Forgot Password",forgot_password_url,type="secondary")
            with col[2]:
                st.link_button("SignUp", signup_url,type="secondary")
   
    def logout(self):
        st.empty()
        st.session_state.clear()
        st.rerun()



    



