from uuid import uuid4
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.core.cache import cache


class SingletonMixin:
    """An abstract base class that provides a Singleton pattern for models.
    
    This mixin will use for models that we want to have only one record of them in database, like any setting model.
    Deleting an instance of this model will raise `AttributeError`. Adding any instance will just overwrite the first
    and only instance of the model. This singleton is based on db models primary key, so the python instances will is
    not exactly the same as each other (their `id` is different), but it's garantee that it's always the same model
    in database.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonMixin, self).save(*args, **kwargs)
        self._set_cache()

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj._set_cache()
        return cache.get(cls.__name__)

    def delete(self, *args, **kwargs):
        raise AttributeError("You cannot delete an instance of {} model".format(self.__class__.__name__))

    def _set_cache(self):
        cache.set(self.__class__.__name__, self)


class Timestampable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LogicalDeletableQuerySet:
    def non_deleted(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)



        
class LogicalDeletable(models.Model):
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    def restore(self):
        self.is_deleted = False
        self.save(update_fields=['is_deleted'])


class Activable(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def activate(self):
        self.is_active = True
        self.save(update_fields=['is_active'])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active'])


class Permalinkable(models.Model):
    slug = models.SlugField(unique=True, max_length=255)

    class Meta:
        abstract = True

    def get_url_kwargs(self, **kwargs):
        kwargs.update(getattr(self, 'url_kwargs', {}))
        return kwargs

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = self._create_slug()
        return super().save(force_insert, force_update, using, update_fields)

    def _create_slug(self):
            index = 0
            model = self._meta.model
            slug = slugify(self.slug_source, allow_unicode=True)
            while model.objects.filter(slug=slug).exists():
                index += 1
                slug = slugify(f"{self.slug_source}_{index}", allow_unicode=True)
            return slug

    @property
    def slug_source(self):
        assert hasattr(self, "title"), (
            "Your model doesn't have a 'title' attribute. Either create a title attribute"
            "of type char or override `self.slug_source()` function"
        )
        return self.title


class Authorable(models.Model):
    created_by = models.ForeignKey('user.User', on_delete=models.PROTECT)

    class Meta:
        abstract = True


class NonSequentialIdentifierMixin(models.Model):
    uuid = models.UUIDField(db_index=True, default=uuid4, editable=False)

    class Meta:
        abstract = True

class MultipleFieldLookupMixin:
    """Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:
                filter[field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj
    
