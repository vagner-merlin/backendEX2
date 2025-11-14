from django.db import models
from app_Cliente.models import Cliente
from app_compras.models import compra

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    Categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE , null=True)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    id_padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategorias')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Producto_Variantes(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    talla = models.CharField(max_length=50)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    Inventario_id = models.ForeignKey('Inventario', on_delete=models.CASCADE , null=True)


class Comentarios(models.Model):
    calificacion = models.IntegerField()
    comentario = models.TextField()
    fecha_reseña = models.DateTimeField(auto_now_add=True)
    Producto_categoria = models.ForeignKey(Producto_Variantes, on_delete=models.CASCADE)
    Cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

class Imagen_Producto(models.Model):
    imagen = models.ImageField(upload_to='productos/' , null=True, blank=True)
    texto = models.CharField(max_length=200)
    es_principal = models.BooleanField(default=False)
    Producto_categoria = models.ForeignKey(Producto_Variantes, on_delete=models.CASCADE)

class item_pedido(models.Model):
    Producto_variante = models.ForeignKey(Producto_Variantes, on_delete=models.CASCADE)
    pedido = models.ForeignKey(compra, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2 , null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2 , null=True)


class item_compras(models.Model):
    producto_variante = models.ForeignKey(Producto_Variantes, on_delete=models.CASCADE)
    compra = models.ForeignKey(compra, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2 , null=True)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2 , null=True)


class Inventario (models.Model):
    stock = models.IntegerField()
    stock_minimo = models.IntegerField()
    stock_maximo = models.IntegerField()
    ubicacion_almacen = models.CharField(max_length=100)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

