from django.db import models
import uuid

# Create your models here.
class TimeStampedModel(models.Model):
    # Modelo Abstracto agrega time stamp a los modelos.
    # Todos los modelos deben heredar de este modelo.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta: 
        abstract = True
        ordering = ["-created_at"]
        
class UUIDModel(models.Model):
    # Modelo Abstracto que usa UUID como primary key.
    # Más seguro que IDs incrementables para APIs Publicas.
    id = models.UUIDField(
        primary_key = True,
        default=uuid.uuid4,
        editable=False 
    )
    
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    # Modelo Abstracto para soft deletes.
    # los registros no se eliminan, solo se marcan como deleted.
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
        
    def soft_delete(self):
        # Marca el registro como eliminado.
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()