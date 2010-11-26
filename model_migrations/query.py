from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField

# Usage:
#
# from django.db.models.manager import Manager
# from model_migrations.query import MigrateQuerySet
#
# class MyModelManager(Manager):
#     def get_query_set(self):
#         return MigrateQuerySet(self.model, using=self._db)

class MigrateQuerySet(QuerySet):
    def migrate(self, using=None):
        clone = self._clone()
        clone._for_write = True # flag query for write
        clone._db = using
        return [clone._migrate(obj) for obj in self]

    def _migrate(self, obj, exclude_fields=None):
        exclude_fields = exclude_fields or []
        indirect, many, related = [], [], {}

        # migrate any related data
        for name in obj._meta.get_all_field_names():
            if name in exclude_fields:
                continue

            field, model, direct, m2m = obj._meta.get_field_by_name(name)
            if not direct: # reverse related field
                field_name = field.field.name
                instances = field.model.objects.filter(**{field_name: obj})
                indirect.append((field_name, list(instances)))
            elif m2m: # m2m field
                # TODO: support throw
                manager = getattr(obj, name)
                many.append((name, [self._migrate(instance, exclude_fields=exclude_fields + [field.related.var_name])
                                        for instance in manager.all()]))
            elif isinstance(field, RelatedField):
                instance = getattr(obj, name, None)
                if instance:
                    related[name] = self._migrate(instance, exclude_fields=exclude_fields + [field.related.var_name])

        # now that related instances were migrated, we can save obj
        obj.id = None
        obj._state.db = self._db

        if related:
            for name, instance in related.iteritems():
                setattr(obj, name, instance)

        obj.save(using=self._db)

        # save many
        for name, instances in many:
            manager = getattr(obj, name)
            map(manager.add, instances)

        # save reverse related items
        for field_name, instances in indirect:
            for instance in instances:
                old_db = instance._state.db
                instance._state.db = obj._state.db
                setattr(instance, field_name, obj)
                instance._state.db = old_db
                self._migrate(instance, exclude_fields=exclude_fields + [field_name])

        return obj
