from london import forms
from london.forms.models import BaseModelForm, ModelFormMetaclass
from london.utils.imports import import_anything
from london.utils.safestring import mark_safe

from attachments.models import Document
from attachments import app_settings


MIME_LABELS = {
    'image/gif':'GIF Image',
    'image/jpg':'JPEG Image',
    'image/jpeg':'JPEG Image',
    'image/png':'PNG Image',
    'application/pdf':'PDF Document',
    }


class CurrentAttachmentsWidget(forms.Widget):
    attachments = None

    def render(self, name, value):
        if not self.attachments or not self.attachments.count():
            return ''

        output = []
        for doc in self.attachments:
            storage_info = doc['storage_info']
            if not storage_info:
                thumb = ''
            elif storage_info.get('thumb_url',None):
                thumb = '<div class="thumb" style="background-image:url(\'%s\')"/>' % storage_info['thumb_url']
            else:
                thumb = '<div class="no-thumb">%s</div>' % MIME_LABELS.get(doc['mime_type'],doc['mime_type'])

            output.append('<li><a href="%(url)s">%(title)s %(thumb)s</a><br/><span><input type="checkbox" value="%(id)s" name="%(name)s"/>Remove</span></li>' % {
                'url': storage_info['download_url'] if storage_info else '',
                'title': doc['title'],
                'thumb': thumb,
                'id': doc['pk'],
                'name': name,
                })

        return mark_safe(u'<ul class="attachments">%s</ul>' % u''.join(output))


class AttachmentsModelFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        # FIXME make this to support multiple files instead of only one
        attrs['new_attachments'] = forms.FileField(required=False, name='new_attachments')
        attrs['current_attachments'] = forms.Field(required=False, name='current_attachments', widget=CurrentAttachmentsWidget)
        return ModelFormMetaclass.__new__(cls, name, bases, attrs)


class AttachmentsModelForm(BaseModelForm):
    __metaclass__ = AttachmentsModelFormMetaclass

    def __new__(cls, *args, **kwargs):
        obj = BaseModelForm.__new__(cls, *args, **kwargs)

        # Changes the fields order
        if hasattr(obj, '_meta'):
            obj._meta.fields.keyOrder.remove('new_attachments')
            obj._meta.fields.keyOrder.remove('current_attachments')
            obj._meta.fields.keyOrder.append('new_attachments')
            obj._meta.fields.keyOrder.append('current_attachments')

        return obj

    def __init__(self, *args, **kwargs):
        super(AttachmentsModelForm, self).__init__(*args, **kwargs)

    def get_initial(self, initial=None):
        initial = super(AttachmentsModelForm, self).get_initial(initial)

        if self.instance and self.can_do_attachments():
            initial['current_attachments'] = Document.query().attached_to(self.instance)
            self.fields['current_attachments'].widget.attachments = initial['current_attachments']
        else:
            self.fields['new_attachments'].widget = forms.HiddenInput()
            self.fields['current_attachments'].widget = forms.HiddenInput()

        return initial

    def save(self, commit=True, force_new=False):
        obj = super(AttachmentsModelForm, self).save(commit=commit, force_new=force_new)

        if self.can_do_attachments():
            self.save_attachments(obj)

        return obj

    def save_attachments(self, obj):
        try:
            engine_str = self.Attachments.engine
        except AttributeError:
            engine_str = app_settings.DEFAULT_ENGINE

        engine_cls = import_anything(engine_str)
        engine_cls().save_form(self, obj)

    def generate_attachment_filename(self, inst, filename):
        return filename

    def can_do_attachments(self):
        return True

