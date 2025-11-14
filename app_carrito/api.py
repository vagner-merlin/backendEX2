from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated , AllowAny
from django.shortcuts import get_object_or_404
from .models import Carrito, ItemCarrito
from .serializers import (
    CarritoSerializer, 
    ItemCarritoSerializer, 
    AgregarItemCarritoSerializer
)
from app_productos.models import Producto_Variantes
from app_Cliente.models import Cliente

class CarritoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar carritos - Requiere autenticación"""
    serializer_class = CarritoSerializer
    permission_classes = [AllowAny]  # Cambiado temporalmente para debugging
    
    def get_queryset(self):
        """Solo devuelve el carrito del cliente autenticado"""
        # Si el usuario no está autenticado, retornar queryset vacío
        if not self.request.user or not self.request.user.is_authenticated:
            return Carrito.objects.none()
        
        try:
            cliente = Cliente.objects.get(user=self.request.user)
            return Carrito.objects.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            print(f"⚠️ Usuario {self.request.user} existe pero no tiene registro de Cliente")
            return Carrito.objects.none()
        except Exception as e:
            print(f"❌ Error en get_queryset: {type(e).__name__}: {str(e)}")
            return Carrito.objects.none()
    
    def get_or_create_carrito(self):
        """Obtiene o crea un carrito para el cliente autenticado"""
        if not self.request.user or not self.request.user.is_authenticated:
            print("⚠️ Usuario no autenticado intentando acceder al carrito")
            return None
            
        try:
            cliente = Cliente.objects.get(user=self.request.user)
            carrito, created = Carrito.objects.get_or_create(cliente=cliente)
            if created:
                print(f"✅ Carrito creado para cliente {cliente.id}")
            return carrito
        except Cliente.DoesNotExist:
            print(f"❌ Usuario {self.request.user.email} no tiene registro de Cliente")
            return None
        except Exception as e:
            print(f"❌ Error en get_or_create_carrito: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def list(self, request, *args, **kwargs):
        """Listar carritos con mejor manejo de errores"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'message': 'Debes iniciar sesión',
                    'carritos': []
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'carritos': serializer.data
            })
        except Exception as e:
            print(f"❌ Error en list: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': str(e),
                'carritos': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def mi_carrito(self, request):
        """Obtiene el carrito actual del usuario autenticado"""
        try:
            carrito = self.get_or_create_carrito()
            if not carrito:
                return Response({
                    'success': False,
                    'message': 'Cliente no encontrado. Verifica que tengas un perfil de cliente.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(carrito)
            return Response({
                'success': True,
                'carrito': serializer.data
            })
        except Exception as e:
            print(f"❌ Error en mi_carrito: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def agregar_item(self, request):
        """Agrega un item al carrito"""
        serializer = AgregarItemCarritoSerializer(data=request.data)
        
        if serializer.is_valid():
            carrito = self.get_or_create_carrito()
            if not carrito:
                return Response({
                    'success': False,
                    'message': 'Cliente no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            producto_variante_id = serializer.validated_data['producto_variante_id']
            cantidad = serializer.validated_data['cantidad']
            
            try:
                producto_variante = Producto_Variantes.objects.get(id=producto_variante_id)
                
                # Nota: Validaciones de stock comentadas porque Producto_Variantes no tiene campo 'stock'
                # TODO: Agregar campo 'stock' al modelo o implementar lógica con tabla Inventario
                # Verificar stock disponible
                # if not hasattr(producto_variante, 'stock'):
                #     print("⚠️ WARNING: Producto_Variantes no tiene campo 'stock'")
                # elif producto_variante.stock < cantidad:
                #     return Response({
                #         'success': False,
                #         'message': f'Stock insuficiente. Disponible: {producto_variante.stock}'
                #     }, status=status.HTTP_400_BAD_REQUEST)
                
                # Buscar si ya existe el item en el carrito
                item_existente = ItemCarrito.objects.filter(
                    carrito=carrito, 
                    producto_variante=producto_variante
                ).first()
                
                if item_existente:
                    # Actualizar cantidad
                    nueva_cantidad = item_existente.cantidad + cantidad
                    # Validación de stock desactivada (campo no existe en el modelo)
                    # if nueva_cantidad > producto_variante.stock:
                    #     return Response({
                    #         'success': False,
                    #         'message': f'Cantidad total excede el stock. Disponible: {producto_variante.stock}'
                    #     }, status=status.HTTP_400_BAD_REQUEST)
                    
                    item_existente.cantidad = nueva_cantidad
                    item_existente.save()
                    item_serializer = ItemCarritoSerializer(item_existente)
                    
                    return Response({
                        'success': True,
                        'message': 'Cantidad actualizada en el carrito',
                        'item': item_serializer.data
                    })
                else:
                    # Crear nuevo item
                    nuevo_item = ItemCarrito.objects.create(
                        carrito=carrito,
                        producto_variante=producto_variante,
                        cantidad=cantidad
                    )
                    item_serializer = ItemCarritoSerializer(nuevo_item)
                    
                    return Response({
                        'success': True,
                        'message': 'Producto agregado al carrito',
                        'item': item_serializer.data
                    }, status=status.HTTP_201_CREATED)
                    
            except Producto_Variantes.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Producto no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'message': 'Datos inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['put'])
    def actualizar_item(self, request):
        """Actualiza la cantidad de un item del carrito"""
        item_id = request.data.get('item_id')
        nueva_cantidad = request.data.get('cantidad')
        
        if not item_id or not nueva_cantidad:
            return Response({
                'success': False,
                'message': 'item_id y cantidad son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            carrito = self.get_or_create_carrito()
            item = ItemCarrito.objects.get(id=item_id, carrito=carrito)
            
            if nueva_cantidad <= 0:
                return Response({
                    'success': False,
                    'message': 'La cantidad debe ser mayor a 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validación de stock desactivada (campo no existe en el modelo)
            # if hasattr(item.producto_variante, 'stock') and nueva_cantidad > item.producto_variante.stock:
            #     return Response({
            #         'success': False,
            #         'message': f'Stock insuficiente. Disponible: {item.producto_variante.stock}'
            #     }, status=status.HTTP_400_BAD_REQUEST)
            
            item.cantidad = nueva_cantidad
            item.save()
            
            serializer = ItemCarritoSerializer(item)
            return Response({
                'success': True,
                'message': 'Cantidad actualizada',
                'item': serializer.data
            })
            
        except ItemCarrito.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item no encontrado en tu carrito'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['delete'])
    def eliminar_item(self, request):
        """Elimina un item del carrito"""
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response({
                'success': False,
                'message': 'item_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            carrito = self.get_or_create_carrito()
            item = ItemCarrito.objects.get(id=item_id, carrito=carrito)
            item.delete()
            
            return Response({
                'success': True,
                'message': 'Producto eliminado del carrito'
            })
            
        except ItemCarrito.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item no encontrado en tu carrito'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['delete'])
    def vaciar_carrito(self, request):
        """Vacía completamente el carrito"""
        carrito = self.get_or_create_carrito()
        if carrito:
            ItemCarrito.objects.filter(carrito=carrito).delete()
            return Response({
                'success': True,
                'message': 'Carrito vaciado exitosamente'
            })
        
        return Response({
            'success': False,
            'message': 'No se pudo vaciar el carrito'
        }, status=status.HTTP_400_BAD_REQUEST)