import os
from google_auth_oauthlib.flow import InstalledAppFlow
d=os.path.dirname(os.path.abspath(__file__))
flow=InstalledAppFlow.from_client_secrets_file(os.path.join(d,'client_secret.json'),
  ['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube'])
creds=flow.run_local_server(port=8765,open_browser=False,access_type='offline',prompt='consent',
  authorization_prompt_message='AUTH_URL {url}')
p=os.path.join(d,'token.json'); open(p,'w').write(creds.to_json()); os.chmod(p,0o600); print('TOKEN_SAVED')
