from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Pedido
from .serializers import PedidoSerializer, PedidoCreateSerializer
from app_Cliente.models import Cliente
import uuid

class PedidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pedidos
    CRUD completo + acciones personalizadas
    """
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [permissions.AllowAny]  # Cambiar a IsAuthenticated en producción
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action in ['create', 'update', 'partial_update']:
            return PedidoCreateSerializer
        return PedidoSerializer
    
    def get_queryset(self):
        """Filtrar pedidos según parámetros opcionales"""
        # Solo select_related para campos que existen en el modelo
        queryset = Pedido.objects.select_related(
            'direccion_envio', 
            'metodo_pago'
        ).order_by('-fecha_pedido')
        
        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado__icontains=estado)
        
        # Filtro por tipo de pedido (online/presencial)
        tipo_pedido = self.request.query_params.get('tipo_pedido', None)
        if tipo_pedido:
            queryset = queryset.filter(tipo_pedido=tipo_pedido)
        
        # Filtro por número de pedido
        numero_pedido = self.request.query_params.get('numero_pedido', None)
        if numero_pedido:
            queryset = queryset.filter(numero_pedido__icontains=numero_pedido)
        
        # Filtro por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_pedido__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_pedido__lte=fecha_hasta)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Listar todos los pedidos con información completa y estadísticas"""
        try:
            queryset = self.get_queryset()
            serializer = PedidoSerializer(queryset, many=True)
            
            # Calcular estadísticas
            total_monto = queryset.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
            estadisticas_estado = queryset.values('estado').annotate(count=Count('id'))
            
            return Response({
                'success': True,
                'count': queryset.count(),
                'total_monto': float(total_monto),
                'estadisticas_estado': list(estadisticas_estado),
                'pedidos': serializer.data
            })
        except Exception as e:
            print(f"❌ Error en list: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': str(e),
                'pedidos': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """Crear un nuevo pedido con generación automática de número de pedido"""
        try:
            data = request.data.copy()
            
            # Generar número de pedido único si no se proporciona
            if not data.get('numero_pedido'):
                data['numero_pedido'] = f"PED-{uuid.uuid4().hex[:10].upper()}"
            
            # Establecer estado por defecto
            if not data.get('estado'):
                data['estado'] = 'pendiente'
            
            serializer = self.get_serializer(data=data)
            
            if serializer.is_valid():
                pedido = serializer.save()
                
                # Usar el serializer completo para la respuesta
                response_serializer = PedidoSerializer(pedido)
                
                return Response({
                    'success': True,
                    'message': 'Pedido creado exitosamente',
                    'pedido': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Datos inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"❌ Error en create: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener un pedido específico"""
        pedido = self.get_object()
        serializer = PedidoSerializer(pedido)
        
        return Response({
            'success': True,
            'pedido': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Actualizar un pedido completamente"""
        pedido = self.get_object()
        serializer = self.get_serializer(pedido, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            
            # Usar el serializer completo para la respuesta
            response_serializer = PedidoSerializer(pedido)
            
            return Response({
                'success': True,
                'message': 'Pedido actualizado exitosamente',
                'pedido': response_serializer.data
            })
        
        return Response({
            'success': False,
            'message': 'Datos inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial de un pedido (PATCH)"""
        pedido = self.get_object()
        serializer = self.get_serializer(pedido, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Usar el serializer completo para la respuesta
            response_serializer = PedidoSerializer(pedido)
            
            return Response({
                'success': True,
                'message': 'Pedido actualizado exitosamente',
                'pedido': response_serializer.data
            })
        
        return Response({
            'success': False,
            'message': 'Datos inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar un pedido"""
        pedido = self.get_object()
        pedido.delete()
        
        return Response({
            'success': True,
            'message': 'Pedido eliminado exitosamente'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def por_estado(self, request):
        """Filtrar pedidos por estado específico"""
        estado = request.query_params.get('estado', 'pendiente')
        pedidos_filtrados = self.queryset.filter(estado__icontains=estado).order_by('-fecha_pedido')
        
        serializer = PedidoSerializer(pedidos_filtrados, many=True)
        
        return Response({
            'success': True,
            'estado': estado,
            'count': pedidos_filtrados.count(),
            'pedidos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Filtrar pedidos por tipo (online/presencial)"""
        tipo = request.query_params.get('tipo', 'online')
        pedidos_filtrados = self.queryset.filter(tipo_pedido=tipo).order_by('-fecha_pedido')
        
        serializer = PedidoSerializer(pedidos_filtrados, many=True)
        
        return Response({
            'success': True,
            'tipo_pedido': tipo,
            'count': pedidos_filtrados.count(),
            'pedidos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas generales de pedidos"""
        try:
            queryset = self.get_queryset()
            
            # Estadísticas por estado
            por_estado = queryset.values('estado').annotate(
                cantidad=Count('id'),
                monto_total=Sum('monto_total')
            )
            
            # Estadísticas por tipo
            por_tipo = queryset.values('tipo_pedido').annotate(
                cantidad=Count('id'),
                monto_total=Sum('monto_total')
            )
            
            # Pedidos recientes (últimos 7 días)
            hace_7_dias = timezone.now().date() - timedelta(days=7)
            pedidos_recientes = queryset.filter(fecha_pedido__gte=hace_7_dias).count()
            
            # Totales generales
            total_pedidos = queryset.count()
            monto_total_general = queryset.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
            promedio_pedido = float(monto_total_general) / total_pedidos if total_pedidos > 0 else 0
            
            return Response({
                'success': True,
                'estadisticas': {
                    'total_pedidos': total_pedidos,
                    'monto_total': float(monto_total_general),
                    'promedio_pedido': round(promedio_pedido, 2),
                    'pedidos_ultimos_7_dias': pedidos_recientes,
                    'por_estado': list(por_estado),
                    'por_tipo': list(por_tipo)
                }
            })
        except Exception as e:
            print(f"❌ Error en estadisticas: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener todos los pedidos pendientes"""
        pedidos_pendientes = self.queryset.filter(estado='pendiente').order_by('-fecha_pedido')
        serializer = PedidoSerializer(pedidos_pendientes, many=True)
        
        return Response({
            'success': True,
            'count': pedidos_pendientes.count(),
            'pedidos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_cliente(self, request):
        """
        Obtener pedidos relacionados con un cliente
        Nota: Busca a través de direccion_envio que tiene relación con cliente
        """
        cliente_id = request.query_params.get('cliente_id')
        
        if not cliente_id:
            return Response({
                'success': False,
                'message': 'cliente_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Buscar pedidos que tengan direccion_envio asociada a ese cliente
            pedidos_cliente = self.queryset.filter(
                direccion_envio__cliente_id=cliente_id
            ).order_by('-fecha_pedido')
            
            serializer = PedidoSerializer(pedidos_cliente, many=True)
            
            return Response({
                'success': True,
                'cliente_id': cliente_id,
                'count': pedidos_cliente.count(),
                'pedidos': serializer.data
            })
        except Exception as e:
            print(f"❌ Error en por_cliente: {e}")
            return Response({
                'success': False,
                'message': str(e),
                'pedidos': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['patch'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar solo el estado de un pedido"""
        pedido = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if not nuevo_estado:
            return Response({
                'success': False,
                'message': 'El campo estado es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar estado
        estados_permitidos = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
        if nuevo_estado.lower() not in estados_permitidos:
            return Response({
                'success': False,
                'message': f'Estado no válido. Estados permitidos: {", ".join(estados_permitidos)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pedido.estado = nuevo_estado.lower()
        pedido.save()
        
        serializer = PedidoSerializer(pedido)
        
        return Response({
            'success': True,
            'message': f'Estado cambiado a "{nuevo_estado}"',
            'pedido': serializer.data
        })
