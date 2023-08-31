from django.db import models


# Create your models here.
class Counter(models.Model):
    name = models.TextField(default='')
    count = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
