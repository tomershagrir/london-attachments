from london.apps import admin
from london import forms
from london.apps.admin.modules import BaseModuleForm

from models import Document

class ModuleDocument(admin.CrudModule):
    model = Document

class AppAttachments(admin.AdminApplication):
    title = 'Attachments'
    modules = (ModuleDocument,)

