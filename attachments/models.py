from london.db import models

from attachments import app_settings

class DocumentQuerySet(models.QuerySet):
    def attached_to(self, obj):
        # TODO: this code is duplicating requests to the database and must be improved to do it only once
        attacheds_pks = [doc['pk'] for doc in DocumentAttachment.query().filter(attached_to=obj).values_list('document',flat=True)]
        return self.filter(pk__in=attacheds_pks)


class Document(models.Model):
    class Meta:
        query = 'attachments.models.DocumentQuerySet'

    title = models.CharField(max_length=100, db_index=True)
    tags = models.ListField(blank=True, null=True, db_index=True)
    file = models.FileField()
    mime_type = models.CharField(max_length=100, db_index=True)

    def __unicode__(self):
        return self['title']

    def attach_to(self, to):
        """Creates an attachment from this document to the given object."""
        self['attachments'].get_or_create(attached_to=to)


class DocumentAttachment(models.Model):
    document = models.ForeignKey('Document', related_name='attachments')
    attached_to = models.ForeignKey(delete_cascade=True, db_index=True)

