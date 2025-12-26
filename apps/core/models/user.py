from django.db import models
from django.forms import CharField
from .business import Business

class User(models.Model):
    name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    emergency_phone = models.CharField(max_length=20)
    
    # Ubicación
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
class BusinessMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)

    def __str__(self):
        return self.user.name

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Miembro del Negocio"
        verbose_name_plural = "Miembros del Negocio"
        
class Customer(models.Model):
    # Aqui tampoco se que poner
    pass
    