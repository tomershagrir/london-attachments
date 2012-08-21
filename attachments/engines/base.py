import os
from attachments.models import Document, DocumentAttachment

class BaseEngine(object):
    def save_form(self, form, obj):
        # Attachment deletion
        if 'current_attachments' in form.request.POST:
            for pk in form.request.POST.getlist('current_attachments'):
                try:
                    doc = Document.query().get(pk=pk)
                except Document.DoesNotExist:
                    continue

                # Remove the attachment first
                doc['attachments'].filter(attached_to=obj).delete(force_if_has_dependents=True)

                # Removes the file only if this is the unique attachment the doc has
                if doc['attachments'].count() == 0:
                    self.remove_file(form, obj, doc)
                    doc.delete()

        # New attachments
        if 'new_attachments' in form.request.FILES:
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

    def remove_file(self, form, obj, doc):
        raise NotImplementedError

