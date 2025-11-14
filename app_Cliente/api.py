from .serializers import (
    ClienteSerializer, ClienteDetailSerializer, 
    Metodo_PagoSerializer, Direccion_EnvioSerializer,
    UserDetailSerializer
)
from .models import Cliente, Metodo_Pago, Direccion_Envio
from rest_framework import viewsets, permissions, status , serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar clientes
    """
    queryset = Cliente.objects.select_related('usuario').all()
    serializer_class = ClienteDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        """Usar serializer detallado para list y retrieve"""
        if self.action in ['list', 'retrieve']:
            return ClienteDetailSerializer
        return ClienteSerializer
    
    def list(self, request, *args, **kwargs):
        """Listar todos los clientes con información de usuario"""
        queryset = self.get_queryset().order_by('-fecha_creacion')
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'clientes': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener un cliente específico con información de usuario"""
        cliente = self.get_object()
        serializer = self.get_serializer(cliente)
        
        return Response({
            'success': True,
            'cliente': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo cliente"""
        serializer = ClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verificar que el usuario no tenga ya un cliente asociado
        usuario_id = request.data.get('usuario')
        if Cliente.objects.filter(usuario_id=usuario_id).exists():
            return Response({
                'success': False,
                'message': f'El usuario con id {usuario_id} ya tiene un perfil de cliente'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Cliente creado exitosamente',
            'cliente': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Actualizar cliente completo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = ClienteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Cliente actualizado exitosamente',
            'cliente': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar cliente y su usuario asociado"""
        cliente = self.get_object()
        usuario = cliente.usuario
        
        # Guardar información para la respuesta
        cliente_id = cliente.id
        usuario_username = usuario.username
        
        # Eliminar cliente (esto también eliminará el usuario por CASCADE)
        cliente.delete()
        
        return Response({
            'success': True,
            'message': f'Cliente #{cliente_id} y usuario "{usuario_username}" eliminados exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def desactivar_cuenta(self, request, pk=None):
        """Desactivar cuenta del cliente (is_active = False)"""
        cliente = self.get_object()
        usuario = cliente.usuario
        
        if not usuario.is_active:
            return Response({
                'success': False,
                'message': f'La cuenta del usuario "{usuario.username}" ya está desactivada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        usuario.is_active = False
        usuario.save()
        
        return Response({
            'success': True,
            'message': f'Cuenta del usuario "{usuario.username}" desactivada exitosamente',
            'cliente': {
                'id': cliente.id,
                'usuario': usuario.username,
                'is_active': usuario.is_active
            }
        })
    
    @action(detail=True, methods=['post'])
    def activar_cuenta(self, request, pk=None):
        """Activar cuenta del cliente (is_active = True)"""
        cliente = self.get_object()
        usuario = cliente.usuario
        
        if usuario.is_active:
            return Response({
                'success': False,
                'message': f'La cuenta del usuario "{usuario.username}" ya está activa'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        usuario.is_active = True
        usuario.save()
        
        return Response({
            'success': True,
            'message': f'Cuenta del usuario "{usuario.username}" activada exitosamente',
            'cliente': {
                'id': cliente.id,
                'usuario': usuario.username,
                'is_active': usuario.is_active
            }
        })
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Listar solo clientes con cuentas activas"""
        clientes_activos = self.queryset.filter(usuario__is_active=True).order_by('-fecha_creacion')
        serializer = self.get_serializer(clientes_activos, many=True)
        
        return Response({
            'success': True,
            'count': clientes_activos.count(),
            'clientes_activos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def inactivos(self, request):
        """Listar solo clientes con cuentas inactivas"""
        clientes_inactivos = self.queryset.filter(usuario__is_active=False).order_by('-fecha_creacion')
        serializer = self.get_serializer(clientes_inactivos, many=True)
        
        return Response({
            'success': True,
            'count': clientes_inactivos.count(),
            'clientes_inactivos': serializer.data
        })



class Metodo_PagoViewSet(viewsets.ModelViewSet):
    queryset = Metodo_Pago.objects.all()
    serializer_class = Metodo_PagoSerializer
    permission_classes = [permissions.IsAuthenticated]


class Direccion_EnvioViewSet(viewsets.ModelViewSet):
    queryset = Direccion_Envio.objects.all()
    serializer_class = Direccion_EnvioSerializer
    permission_classes = [permissions.AllowAny]


class VendedorViewSet(viewsets.ViewSet):
    """
    ViewSet para crear usuarios vendedores (is_staff=True)
    No tiene relación con el modelo Cliente
    """
    permission_classes = [permissions.AllowAny]
    
    def create(self, request):
        """Crear un usuario vendedor (is_staff=True)"""
        # Validar campos requeridos
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Validaciones
        if not username or not email or not password or not password2:
            return Response({
                'success': False,
                'message': 'Los campos username, email, password y password2 son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if password != password2:
            return Response({
                'success': False,
                'message': 'Las contraseñas no coinciden'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el username ya existe
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'message': f'El username "{username}" ya está en uso'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el email ya existe
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': f'El email "{email}" ya está registrado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Crear usuario vendedor (is_staff=True)
            vendedor = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,  # Vendedor
                is_superuser=False,
                is_active=True
            )
            
            return Response({
                'success': True,
                'message': 'Vendedor creado exitosamente',
                'vendedor': {
                    'id': vendedor.id,
                    'username': vendedor.username,
                    'email': vendedor.email,
                    'first_name': vendedor.first_name,
                    'last_name': vendedor.last_name,
                    'is_staff': vendedor.is_staff,
                    'is_active': vendedor.is_active,
                    'date_joined': vendedor.date_joined
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al crear vendedor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def list(self, request):
        """Listar todos los vendedores (usuarios con is_staff=True)"""
        vendedores = User.objects.filter(is_staff=True, is_superuser=False).order_by('-date_joined')
        
        vendedores_data = [{
            'id': v.id,
            'username': v.username,
            'email': v.email,
            'first_name': v.first_name,
            'last_name': v.last_name,
            'is_staff': v.is_staff,
            'is_active': v.is_active,
            'date_joined': v.date_joined,
            'last_login': v.last_login
        } for v in vendedores]
        
        return Response({
            'success': True,
            'count': vendedores.count(),
            'vendedores': vendedores_data
        })
    
    def retrieve(self, request, pk=None):
        """Obtener un vendedor específico"""
        try:
            vendedor = User.objects.get(pk=pk, is_staff=True, is_superuser=False)
            
            return Response({
                'success': True,
                'vendedor': {
                    'id': vendedor.id,
                    'username': vendedor.username,
                    'email': vendedor.email,
                    'first_name': vendedor.first_name,
                    'last_name': vendedor.last_name,
                    'is_staff': vendedor.is_staff,
                    'is_active': vendedor.is_active,
                    'date_joined': vendedor.date_joined,
                    'last_login': vendedor.last_login
                }
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Vendedor con id {pk} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """Eliminar un vendedor"""
        try:
            vendedor = User.objects.get(pk=pk, is_staff=True, is_superuser=False)
            username = vendedor.username
            vendedor.delete()
            
            return Response({
                'success': True,
                'message': f'Vendedor "{username}" eliminado exitosamente'
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Vendedor con id {pk} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


