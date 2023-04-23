from django.shortcuts import redirect
from django.http import HttpResponse

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os

#for local http InsecureTransportError
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']
REDIRECT_URL = "http://127.0.0.1:8000/rest/v1/calendar/redirect/"



def GoogleCalendarInitView(request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    
    flow.redirect_uri = REDIRECT_URL
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    
    # Store the state so the callback can verify the auth server response.
    request.session['state'] = state
    return redirect(authorization_url)


def GoogleCalendarRedirectView(request):
    
    state = request.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state)
    
    flow.redirect_uri = REDIRECT_URL

    authorization_response = request.get_full_path()
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.
    credentials = flow.credentials
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    
    # Check if credentials are in session
    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')
    
    
    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials'])
    
    service = googleapiclient.discovery.build(
        'calendar', 'v3', credentials=credentials)
    
    
    calendar_list = service.calendarList().list().execute()
    calendar_id = calendar_list['items'][0]['id']
        
    events  = service.events().list(calendarId=calendar_id).execute()
    
    events_list = []
    if not events['items']:
        print('No data found.')
        return HttpResponse("No data found or user credentials invalid.")
        
    else:
        for event in events['items']:
            events_list.append(event)
            return HttpResponse(events_list)
            
    return HttpResponse("calendar event aren't here")
    