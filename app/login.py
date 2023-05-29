import boto3
from botocore.exceptions import ClientError
from typing import Union

import os.path as path
import traceback
import json

import constants

cognito_user_client = boto3.client('cognito-idp', constants.AWS_REGION)
cognito_identity_client = boto3.client('cognito-identity', constants.AWS_REGION)


def obtain_user_credentials():
    if path.isfile('credentials.json'):
        print('Reading your credentials from file')
        with open('credentials.json', 'r') as credentials_file:
            credentials = json.load(credentials_file)
            return credentials['username'], credentials['password']
    else:
        print('Your credentials are not on the file, asking for them now')
        username = input('Email: ')
        password = input('Password: ')
        return username, password


class UserData:

    def __init__(self, email, access_token, id_token):
        self.email = email
        self.access_token = access_token
        self.id_token = id_token
        self.user_id = None

    def set_user_id(self, user_id):
        self.user_id = user_id


def log_in(username: str, password: str) -> Union[UserData, None]:
    try:
        sign_in_response = cognito_user_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            },
            ClientId=constants.COGNITO_USER_POOL_CLIENT_ID
        )
    except ClientError:
        print('Failed to login with the given credentials')
        traceback.print_exc()
        return None
    if 'ChallengeName' in sign_in_response:
        challenge = sign_in_response['ChallengeName']
        session = sign_in_response['Session']
        if challenge == 'NEW_PASSWORD_REQUIRED':
            new_password = input('Your password is temporary and must be changed. Enter you new password:')
            return change_temporary_password(username, new_password, session)
        else:
            print('Error: unknown challenge')
            return None
    else:
        return UserData(
            email=username,
            access_token=sign_in_response['AuthenticationResult']['AccessToken'],
            id_token=sign_in_response['AuthenticationResult']['IdToken']
        )


def change_temporary_password(username: str, new_password: str, session: str) -> UserData:
    change_password_response = cognito_user_client.respond_to_auth_challenge(
        ClientId=constants.COGNITO_USER_POOL_CLIENT_ID,
        Session=session,
        ChallengeName='NEW_PASSWORD_REQUIRED',
        ChallengeResponses={
            'USERNAME': username,
            'NEW_PASSWORD': new_password
        }
    )
    return UserData(
        email=username,
        access_token=change_password_response['AuthenticationResult']['AccessToken'],
        id_token=change_password_response['AuthenticationResult']['IdToken']
    )


def get_cognito_identity_id(token: str) -> str:
    response = cognito_identity_client.get_id(
        AccountId=constants.AWS_ACCOUNT_ID,
        IdentityPoolId=constants.COGNITO_IDENTITY_POOL_ID,
        Logins={
            f'cognito-idp.{constants.AWS_REGION}.amazonaws.com/{constants.COGNITO_USER_POOL_ID}': token
        }
    )
    return response['IdentityId']


def exchange_token_for_aws_credentials(cognito_identity_id: str, token: str):
    response = cognito_identity_client.get_credentials_for_identity(
        IdentityId=cognito_identity_id,
        Logins={
            f'cognito-idp.{constants.AWS_REGION}.amazonaws.com/{constants.COGNITO_USER_POOL_ID}': token
        }
    )
    return response['Credentials']['AccessKeyId'],\
        response['Credentials']['SecretKey'], \
        response['Credentials']['SessionToken']


def get_user_id(access_token: str) -> str:
    response = cognito_user_client.get_user(AccessToken=access_token)
    for attribute in response['UserAttributes']:
        if attribute['Name'] == 'sub':
            return attribute['Value']
    raise Exception('Unable to find user ID (sub) in response')




