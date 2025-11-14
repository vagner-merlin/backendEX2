"""
API CRUD para ItemCarrito - Gestión directa de items del carrito
"""
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Carrito, ItemCarrito
from .serializers import ItemCarritoSerializer
from app_productos.models import Producto_Variantes
from app_Cliente.models import Cliente


class ItemCarritoViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD completo para ItemCarrito
    
    - GET /api/carrito/items/ - Lista todos los items del carrito del usuario
    - GET /api/carrito/items/{id}/ - Obtiene un item específico
    - POST /api/carrito/items/ - Crea un nuevo item en el carrito
    - PUT/PATCH /api/carrito/items/{id}/ - Actualiza un item
    - DELETE /api/carrito/items/{id}/ - Elimina un item
    """
    serializer_class = ItemCarritoSerializer
    permission_classes = [AllowAny]  # Temporal para testing, cambiar a [IsAuthenticated]
    
    def get_queryset(self):
        """Devuelve solo los items del carrito del usuario autenticado"""
        if not self.request.user or not self.request.user.is_authenticated:
            return ItemCarrito.objects.none()
        
        try:
            cliente = Cliente.objects.get(user=self.request.user)
            carrito = Carrito.objects.filter(cliente=cliente).first()
            if carrito:
                return ItemCarrito.objects.filter(carrito=carrito).select_related(
                    'producto_variante', 
                    'producto_variante__producto'
                )
            return ItemCarrito.objects.none()
        except Cliente.DoesNotExist:
            print(f"⚠️ Usuario {self.request.user} no tiene Cliente asociado")
            return ItemCarrito.objects.none()
        except Exception as e:
            print(f"❌ Error en get_queryset: {e}")
            return ItemCarrito.objects.none()
    
    def get_carrito(self):
        """Obtiene o crea el carrito del usuario autenticado"""
        try:
            cliente = Cliente.objects.get(user=self.request.user)
            carrito, created = Carrito.objects.get_or_create(cliente=cliente)
            return carrito
        except Cliente.DoesNotExist:
            return None
        except Exception as e:
            print(f"❌ Error obteniendo carrito: {e}")
            return None
    
    def list(self, request, *args, **kwargs):
        """
        GET /api/carrito/items/
        Lista todos los items del carrito del usuario
        """
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'message': 'Debes iniciar sesión',
                    'items': []
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            # Calcular totales
            total_items = sum(item.cantidad for item in queryset)
            total_precio = sum(
                float(item.cantidad * item.producto_variante.precio_unitario) 
                for item in queryset
            )
            
            return Response({
                'success': True,
                'count': queryset.count(),
                'total_items': total_items,
                'total_precio': total_precio,
                'items': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error en list: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': str(e),
                'items': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/carrito/items/{id}/
        Obtiene un item específico del carrito
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'item': serializer.data
            }, status=status.HTTP_200_OK)
        except ItemCarrito.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error en retrieve: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """
        POST /api/carrito/items/
        Crea un nuevo item en el carrito
        
        Body:
        {
            "producto_variante": 1,  # ID de la variante
            "cantidad": 2
        }
        """
        try:
            carrito = self.get_carrito()
            if not carrito:
                return Response({
                    'success': False,
                    'message': 'No se pudo obtener el carrito. Verifica que tengas un perfil de cliente.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            producto_variante_id = request.data.get('producto_variante')
            cantidad = request.data.get('cantidad', 1)
            
            if not producto_variante_id:
                return Response({
                    'success': False,
                    'message': 'producto_variante es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar que el producto existe
            try:
                producto_variante = Producto_Variantes.objects.get(id=producto_variante_id)
            except Producto_Variantes.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Producto no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verificar si ya existe en el carrito
            item_existente = ItemCarrito.objects.filter(
                carrito=carrito,
                producto_variante=producto_variante
            ).first()
            
            if item_existente:
                # Actualizar cantidad existente
                item_existente.cantidad += cantidad
                item_existente.save()
                serializer = self.get_serializer(item_existente)
                return Response({
                    'success': True,
                    'message': 'Cantidad actualizada en el carrito',
                    'item': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Crear nuevo item
                nuevo_item = ItemCarrito.objects.create(
                    carrito=carrito,
                    producto_variante=producto_variante,
                    cantidad=cantidad
                )
                serializer = self.get_serializer(nuevo_item)
                return Response({
                    'success': True,
                    'message': 'Producto agregado al carrito',
                    'item': serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(f"❌ Error en create: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """
        PUT /api/carrito/items/{id}/
        Actualiza completamente un item del carrito
        
        Body:
        {
            "producto_variante": 1,
            "cantidad": 5
        }
        """
        try:
            instance = self.get_object()
            cantidad = request.data.get('cantidad')
            
            if cantidad is None:
                return Response({
                    'success': False,
                    'message': 'cantidad es requerida'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if cantidad <= 0:
                return Response({
                    'success': False,
                    'message': 'La cantidad debe ser mayor a 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance.cantidad = cantidad
            instance.save()
            
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'message': 'Item actualizado exitosamente',
                'item': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ItemCarrito.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error en update: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/carrito/items/{id}/
        Actualiza parcialmente un item del carrito
        
        Body:
        {
            "cantidad": 3
        }
        """
        try:
            instance = self.get_object()
            cantidad = request.data.get('cantidad')
            
            if cantidad is not None:
                if cantidad <= 0:
                    return Response({
                        'success': False,
                        'message': 'La cantidad debe ser mayor a 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                instance.cantidad = cantidad
                instance.save()
            
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'message': 'Item actualizado exitosamente',
                'item': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ItemCarrito.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error en partial_update: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/carrito/items/{id}/
        Elimina un item del carrito
        """
        try:
            instance = self.get_object()
            producto_nombre = instance.producto_variante.producto.nombre
            instance.delete()
            
            return Response({
                'success': True,
                'message': f'"{producto_nombre}" eliminado del carrito'
            }, status=status.HTTP_200_OK)
            
        except ItemCarrito.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error en destroy: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
