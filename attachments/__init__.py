from london.conf import AppSettings

app_settings = AppSettings()

app_settings.declare('ATTACHABLE_MODELS', default=None)
app_settings.declare('LOCAL_ROOT', default='attachments', global_name='ATTACHMENTS_LOCAL_ROOT')
app_settings.declare('DEFAULT_ENGINE', default='attachments.engines.FileSystem',
        global_name='ATTACHMENTS_ENGINE')

# Google Drive settings
app_settings.declare('GOOGLE_DRIVE_CLIENT_ID', default='')
app_settings.declare('GOOGLE_DRIVE_CLIENT_SECRET', default='')
app_settings.declare('GOOGLE_DRIVE_ROOT_URL', default='https://www.googleapis.com/drive/v2/')
app_settings.declare('GOOGLE_DRIVE_ROOT_COLLECTION', default='TDispatch')
app_settings.declare('GOOGLE_DRIVE_REDIRECT_URL', default='http://tdispatch/preferences/files-drive/')
app_settings.declare('GOOGLE_DRIVE_SCOPES', default=(
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.email',
        #'https://www.googleapis.com/auth/userinfo.profile',
        'https://docs.google.com/feeds/',
        'https://spreadsheets.google.com/feeds/',
        'https://docs.googleusercontent.com/',
        ))

