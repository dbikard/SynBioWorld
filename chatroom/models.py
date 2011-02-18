from django.contrib.auth.models import User
from django.db import models
from django.db.models import permalink


class chatRoom(models.Model):
	name=models.CharField(max_length=200)
	chat=models.TextField(null=True)
	
	