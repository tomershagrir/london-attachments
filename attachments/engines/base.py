import os
from attachments.models import Document, DocumentAttachment

class BaseEngine(object):
    def save_form(self, form, obj):
        if 'new_attachments' not in form.request.FILES:
            return

        # Supporting multiple files uploaded
        for attfile in form.request.FILES.getlist('new_attachments'):
            doc = Document(
                _save=True,
                title=os.path.splitext(attfile.name)[0],
                mime_type=attfile.content_type,
                )

            self.save_file(form, obj, doc, attfile)

            # Attaching document to the object
            doc.attach_to(obj)

    def save_file(self, form, obj, doc, attfile):
        raise NotImplementedError

