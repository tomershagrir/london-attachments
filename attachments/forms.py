from london import forms
from london.forms.models import BaseModelForm, ModelFormMetaclass


class AttachmentsModelFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        attrs['attachment'] = forms.FileField(required=False) # FIXME make this to support multiple files instead of only one
        return ModelFormMetaclass.__new__(cls, name, bases, attrs)


class AttachmentsModelForm(BaseModelForm):
    __metaclass__ = AttachmentsModelFormMetaclass


