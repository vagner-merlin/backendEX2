from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, F
from .models import (
    Producto, Categoria, Producto_Variantes, Comentarios, 
    Imagen_Producto, item_pedido, item_compras, Inventario
)
from .serializers import (
    ProductoBasicoSerializer, ProductoCompletoSerializer,
    CategoriaSerializer, ProductoCategoriaSerializer, ProductoCategoriaCreateSerializer,
    ReseñaSerializer, ReseñaCreateSerializer, ImagenProductoSerializer,
    ItemPedidoSerializer, ItemComprasSerializer, InventarioSerializer
)

class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para productos - PÚBLICO (sin autenticación para ver catálogo)
    """
    queryset = Producto.objects.filter(activo=True)
    serializer_class = ProductoCompletoSerializer
    permission_classes = [permissions.AllowAny]  # Público para ver catálogo
    
    def get_queryset(self):
        """Filtrar productos con parámetros opcionales"""
        queryset = Producto.objects.select_related('Categoria').filter(activo=True)
        
        # Filtro por nombre
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        
        # Filtro por categoría
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(Categoria_id=categoria)
        
        return queryset.order_by('-fecha_creacion')
    
    def list(self, request, *args, **kwargs):
        """Listar productos del catálogo"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'productos': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener producto completo con sus variantes"""
        producto = self.get_object()
        serializer = self.get_serializer(producto)
        
        return Response({
            'success': True,
            'producto': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo producto"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Producto creado exitosamente',
            'producto': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Actualizar producto completo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Producto actualizado exitosamente',
            'producto': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar producto (soft delete - marcar como inactivo)"""
        instance = self.get_object()
        instance.activo = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Producto desactivado exitosamente'
        }, status=status.HTTP_200_OK)
    
    def get_permissions(self):
        """Permisos dinámicos: solo lectura pública, escritura autenticada"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def destacados(self, request):
        """Productos destacados (los más recientes o con mejor rating)"""
        productos_destacados = self.queryset.order_by('-fecha_creacion')[:6]
        serializer = ProductoBasicoSerializer(productos_destacados, many=True)
        
        return Response({
            'success': True,
            'count': productos_destacados.count(),
            'productos_destacados': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def variantes(self, request, pk=None):
        """Obtener todas las variantes de un producto específico"""
        producto = self.get_object()
        variantes = Producto_Variantes.objects.filter(producto=producto)
        serializer = ProductoCategoriaSerializer(variantes, many=True)
        
        return Response({
            'success': True,
            'producto': producto.nombre,
            'count': variantes.count(),
            'variantes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_categoria(self, request):
        """Obtener productos filtrados por categoría"""
        categoria_id = request.query_params.get('categoria_id')
        
        if not categoria_id:
            return Response({
                'success': False,
                'message': 'categoria_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        productos = self.queryset.filter(Categoria_id=categoria_id)
        serializer = self.get_serializer(productos, many=True)
        
        return Response({
            'success': True,
            'count': productos.count(),
            'productos': serializer.data
        })

class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para categorías - PÚBLICO para navegación
    """
    queryset = Categoria.objects.filter(activo=True)
    serializer_class = CategoriaSerializer
    
    def get_permissions(self):
        """Permisos dinámicos: solo lectura pública, escritura autenticada"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request, *args, **kwargs):
        """Listar categorías principales (sin padre)"""
        categorias_principales = self.queryset.filter(id_padre__isnull=True)
        serializer = self.get_serializer(categorias_principales, many=True)
        
        return Response({
            'success': True,
            'count': categorias_principales.count(),
            'categorias': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def productos(self, request, pk=None):
        """Obtener productos de una categoría específica"""
        categoria = self.get_object()
        productos = Producto.objects.filter(
            productocategoria__categoria=categoria,
            activo=True
        ).distinct()
        
        serializer = ProductoBasicoSerializer(productos, many=True)
        
        return Response({
            'success': True,
            'categoria': categoria.nombre,
            'count': productos.count(),
            'productos': serializer.data
        })

class ProductoCategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para variantes de productos - PÚBLICO para ver, AUTENTICADO para modificar
    """
    queryset = Producto_Variantes.objects.all()
    serializer_class = ProductoCategoriaSerializer
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action in ['create', 'update', 'partial_update']:
            return ProductoCategoriaCreateSerializer
        return ProductoCategoriaSerializer
    
    def get_permissions(self):
        """Permisos dinámicos"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar variantes con parámetros"""
        queryset = Producto_Variantes.objects.select_related(
            'producto', 
            'producto__Categoria', 
            'Inventario_id'
        )
        
        # Filtro por producto
        producto_id = self.request.query_params.get('producto', None)
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        
        # Filtro por color
        color = self.request.query_params.get('color', None)
        if color:
            queryset = queryset.filter(color__icontains=color)
        
        # Filtro por talla
        talla = self.request.query_params.get('talla', None)
        if talla:
            queryset = queryset.filter(talla__icontains=talla)
        
        return queryset.order_by('-fecha_creacion')
    
    def list(self, request, *args, **kwargs):
        """Listar variantes de productos"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'variantes': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener una variante específica con toda su información"""
        variante = self.get_object()
        serializer = self.get_serializer(variante)
        
        # Devolver directamente el objeto serializado (no en 'variante')
        # para que coincida con lo que espera el frontend
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Crear nueva variante de producto"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Variante creada exitosamente',
            'variante': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Actualizar variante completa"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Variante actualizada exitosamente',
            'variante': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar variante (soft delete)"""
        instance = self.get_object()
        instance.activo = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Variante desactivada exitosamente'
        }, status=status.HTTP_200_OK)

class ReseñaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para reseñas - PÚBLICO para leer, AUTENTICADO para crear
    """
    queryset = Comentarios.objects.all()
    serializer_class = ReseñaSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReseñaCreateSerializer
        return ReseñaSerializer
    
    def get_permissions(self):
        """Solo lectura pública, escritura autenticada"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar reseñas por producto"""
        queryset = Comentarios.objects.select_related('Cliente', 'Producto_categoria')
        
        producto_variante = self.request.query_params.get('producto_variante', None)
        if producto_variante:
            queryset = queryset.filter(Producto_categoria_id=producto_variante)
        
        return queryset.order_by('-fecha_reseña')
    
    @action(detail=False, methods=['get'])
    def por_producto(self, request):
        """Reseñas de una variante específica con estadísticas"""
        producto_variante_id = request.query_params.get('producto_variante_id')
        
        if not producto_variante_id:
            return Response({
                'success': False,
                'message': 'producto_variante_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reseñas_producto = self.queryset.filter(Producto_categoria_id=producto_variante_id)
        serializer = self.get_serializer(reseñas_producto, many=True)
        
        # Calcular estadísticas
        promedio = reseñas_producto.aggregate(Avg('calificacion'))['calificacion__avg'] or 0
        
        return Response({
            'success': True,
            'producto_variante_id': producto_variante_id,
            'total_reseñas': reseñas_producto.count(),
            'calificacion_promedio': round(promedio, 2),
            'reseñas': serializer.data
        })

class ImagenProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para imágenes de productos - PÚBLICO para ver, AUTENTICADO para modificar
    """
    queryset = Imagen_Producto.objects.all()
    serializer_class = ImagenProductoSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar imágenes por producto variante"""
        queryset = Imagen_Producto.objects.select_related('Producto_categoria__producto')
        
        # Filtro por variante de producto
        producto_categoria = self.request.query_params.get('producto_categoria', None)
        if producto_categoria:
            queryset = queryset.filter(Producto_categoria_id=producto_categoria)
        
        # Filtro por producto base
        producto = self.request.query_params.get('producto', None)
        if producto:
            queryset = queryset.filter(Producto_categoria__producto_id=producto)
        
        # Filtro solo principales
        solo_principales = self.request.query_params.get('solo_principales', None)
        if solo_principales == 'true':
            queryset = queryset.filter(es_principal=True)
        
        return queryset.order_by('-es_principal', 'id')
    
    def list(self, request, *args, **kwargs):
        """Listar imágenes de productos"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'imagenes': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear nueva imagen de producto"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Imagen creada exitosamente',
            'imagen': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Actualizar imagen completa"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Imagen actualizada exitosamente',
            'imagen': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar imagen"""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'message': 'Imagen eliminada exitosamente'
        }, status=status.HTTP_204_NO_CONTENT)

class ItemPedidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para items de pedido - AUTENTICADO
    """
    queryset = item_pedido.objects.all()
    serializer_class = ItemPedidoSerializer
    permission_classes = [permissions.AllowAny]

class ItemComprasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para items de compras - AUTENTICADO
    """
    queryset = item_compras.objects.all()
    serializer_class = ItemComprasSerializer
    permission_classes = [permissions.IsAuthenticated]

class InventarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para inventario - CRUD completo para administración
    """
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Filtrar inventario con parámetros"""
        queryset = Inventario.objects.all()
        
        # Filtro por ubicación
        ubicacion = self.request.query_params.get('ubicacion', None)
        if ubicacion:
            queryset = queryset.filter(ubicacion_almacen__icontains=ubicacion)
        
        # Filtro por stock bajo (stock menor que stock_minimo)
        stock_bajo = self.request.query_params.get('stock_bajo', None)
        if stock_bajo == 'true':
            queryset = queryset.filter(stock__lt=F('stock_minimo'))
        
        return queryset.order_by('-ultima_actualizacion')
    
    def list(self, request, *args, **kwargs):
        """Listar inventario con información del producto"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'inventario': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear registro de inventario"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Registro de inventario creado exitosamente',
            'inventario': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Actualizar registro de inventario"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Registro de inventario actualizado exitosamente',
            'inventario': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar registro de inventario"""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'message': 'Registro de inventario eliminado exitosamente'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """Obtener productos con stock bajo (stock < stock_minimo)"""
        inventario_bajo = self.queryset.filter(stock__lt=F('stock_minimo'))
        serializer = self.get_serializer(inventario_bajo, many=True)
        
        return Response({
            'success': True,
            'count': inventario_bajo.count(),
            'inventario_bajo': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """Obtener alertas de inventario (stock bajo o por encima del máximo)"""
        stock_bajo = self.queryset.filter(stock__lt=F('stock_minimo'))
        stock_alto = self.queryset.filter(stock__gt=F('stock_maximo'))
        
        return Response({
            'success': True,
            'alertas': {
                'stock_bajo': {
                    'count': stock_bajo.count(),
                    'items': self.get_serializer(stock_bajo, many=True).data
                },
                'stock_alto': {
                    'count': stock_alto.count(),
                    'items': self.get_serializer(stock_alto, many=True).data
                }
            }
        })
    
    @action(detail=False, methods=['get'])
    def por_variante(self, request):
        """Obtener inventario de una variante específica"""
        variante_id = request.query_params.get('variante', None)
        
        if not variante_id:
            return Response({
                'success': False,
                'error': 'Se requiere el parámetro variante'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            variante = Producto_Variantes.objects.get(id=variante_id)
            if variante.Inventario_id:
                serializer = self.get_serializer(variante.Inventario_id)
                return Response({
                    'success': True,
                    'inventario': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Esta variante no tiene inventario asignado'
                }, status=status.HTTP_404_NOT_FOUND)
        except Producto_Variantes.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Variante no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
