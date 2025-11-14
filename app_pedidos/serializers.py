from rest_framework import serializers
from .models import Pedido
from app_Cliente.serializers import ClienteSerializer, Direccion_EnvioSerializer, Metodo_PagoSerializer
from app_Cliente.models import Cliente, Direccion_Envio, Metodo_Pago

class PedidoSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Pedido"""
    direccion_info = Direccion_EnvioSerializer(source='direccion_envio', read_only=True)
    metodo_pago_info = Metodo_PagoSerializer(source='metodo_pago', read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'direccion_envio', 'fecha_pedido', 'monto_total', 'estado',
            'numero_pedido', 'subtotal', 'costo_envio', 'transaccion_id', 
            'nota', 'metodo_pago', 'tipo_pedido', 'direccion_info', 'metodo_pago_info'
        ]
        read_only_fields = ['fecha_pedido', 'numero_pedido']  # Se asignan automáticamente
    
    def validate_monto_total(self, value):
        """Validar que el monto sea positivo"""
        if value and value < 0:
            raise serializers.ValidationError("El monto total no puede ser negativo")
        return value
    
    def validate_subtotal(self, value):
        """Validar que el subtotal sea positivo"""
        if value and value < 0:
            raise serializers.ValidationError("El subtotal no puede ser negativo")
        return value
    
    def validate_costo_envio(self, value):
        """Validar que el costo de envío sea positivo"""
        if value and value < 0:
            raise serializers.ValidationError("El costo de envío no puede ser negativo")
        return value
    
    def validate_estado(self, value):
        """Validar estados permitidos"""
        estados_permitidos = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
        if value.lower() not in estados_permitidos:
            raise serializers.ValidationError(
                f"Estado no válido. Estados permitidos: {', '.join(estados_permitidos)}"
            )
        return value.lower()

class PedidoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar pedidos"""
    
    class Meta:
        model = Pedido
        fields = [
            'direccion_envio', 'monto_total', 'estado', 'subtotal', 
            'costo_envio', 'transaccion_id', 'nota', 'metodo_pago', 'tipo_pedido'
        ]
    
    def validate_monto_total(self, value):
        if value and value < 0:
            raise serializers.ValidationError("El monto total no puede ser negativo")
        return value
    
    def validate_subtotal(self, value):
        if value and value < 0:
            raise serializers.ValidationError("El subtotal no puede ser negativo")
        return value
    
    def validate_costo_envio(self, value):
        if value and value < 0:
            raise serializers.ValidationError("El costo de envío no puede ser negativo")
        return value
    
    def validate_estado(self, value):
        estados_permitidos = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
        if value.lower() not in estados_permitidos:
            raise serializers.ValidationError(
                f"Estado no válido. Estados permitidos: {', '.join(estados_permitidos)}"
            )
        return value.lower()
    
    def create(self, validated_data):
        """Generar número de pedido automáticamente"""
        import uuid
        from datetime import datetime
        
        # Generar número de pedido único
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8].upper()
        validated_data['numero_pedido'] = f"PED-{timestamp}-{unique_id}"
        
        return super().create(validated_data)
