import os
from london.conf import settings
from base import BaseEngine

from attachments import app_settings

class FileSystem(BaseEngine):
    def get_absolute_file_path(self, filename):
        up_to = app_settings.LOCAL_ROOT
        if not up_to.startswith('/'):
            up_to = os.path.join(settings.UPLOADS_ROOT, up_to)
        return os.path.join(up_to, filename)

    def save_file(self, form, obj, doc, attfile):
        file_path = self.get_absolute_file_path(form.generate_attachment_filename(obj, attfile.name))

        # Creating directory
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        # Saving file
        fp = file(file_path, 'wb')
        fp.write(attfile.read())
        fp.close()

        # Local file path
        doc['local_file'] = file_path
        doc.save()

