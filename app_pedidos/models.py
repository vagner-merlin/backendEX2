from django.db import models
from app_Cliente.models import Cliente , Direccion_Envio
# Create your models here.
from app_Cliente.models import Metodo_Pago

class Pedido(models.Model):
    direccion_envio = models.ForeignKey(Direccion_Envio, on_delete=models.CASCADE)
    fecha_pedido = models.DateField(auto_now_add=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2 , null=True)
    estado = models.CharField(max_length=50)
    numero_pedido = models.CharField(max_length=100, unique=True , null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2 , null=True)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2 , null=True)
    transaccion_id = models.CharField(max_length=100, null=True, blank=True)
    nota = models.TextField(null=True, blank=True)
    metodo_pago = models.ForeignKey(Metodo_Pago, on_delete=models.CASCADE , null=True)

