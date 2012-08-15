from london.db import models


class DocumentQuerySet(models.QuerySet):
    def attached_to(self, obj):
        # TODO
        pass


class Document(models.Model):
    class Meta:
        query = 'faq.models.DocumentQuerySet'

    title = models.CharField(max_length=100, db_index=True)
    tags = models.ListField(blank=True, null=True, db_index=True)
    file = models.FileField()
    mime_type = models.CharField(max_length=100, db_index=True)

    def __unicode__(self):
        return self['title']

    def attach_to(self, to):
        pass # TODO


class DocumentAttachment(models.Model):
    document = models.ForeignKey('Document', related_name='attachments')
    attached_to = models.ForeignKey()

# SIGNALS

from london.db import signals

def post_delete(instance, **kwargs):
    pass # TODO - consider only declared model classes for performance reasons
signals.post_delete.connect(post_delete)

