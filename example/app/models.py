from django.db import models
from django.db.models.manager import Manager


from model_migrations.query import MigrateQuerySet


class ParentManager(Manager):
    def get_query_set(self):
        """Return a MigrateQuerySet allowing to migrate our
        data to a another database"""
        return MigrateQuerySet(self.model, using=self._db)


class Car(models.Model):
    """A Car class"""
    model = models.CharField(max_length=32)


class House(models.Model):
    """A House class"""
    address = models.CharField(max_length=1024)


class Parent(models.Model):
    """A Parent class"""
    name   = models.CharField(max_length=32)
    gender = models.CharField(max_length=1, choices=(('m', 'Male'),
                                                     ('f', 'Female')))
    cars   = models.ManyToManyField(Car)
    house  = models.ForeignKey(House)

    objects = ParentManager()


class Child(models.Model):
    """A Child class"""
    name = models.CharField(max_length=32)
    dad  = models.ForeignKey(Parent, related_name='dad')
    mom  = models.ForeignKey(Parent, related_name='mom')
