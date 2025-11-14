# API CRUD de ItemCarrito

## 📋 Endpoints Disponibles

### 1. **Listar Items del Carrito**
```http
GET /api/carrito/items/
```
**Respuesta:**
```json
{
  "success": true,
  "count": 3,
  "total_items": 7,
  "total_precio": 149.97,
  "items": [
    {
      "id": 1,
      "carrito": 1,
      "producto_variante": 5,
      "cantidad": 2,
      "subtotal": 59.98,
      "variante_info": {
        "id": 5,
        "producto": 2,
        "color": "Rojo",
        "talla": "M",
        "precio_unitario": "29.99",
        "activo": true,
        "producto_info": {
          "id": 2,
          "nombre": "Camiseta Deportiva",
          "descripcion": "Camiseta de alta calidad",
          "activo": true
        },
        "imagenes": [...],
        "imagen_principal": "https://..."
      }
    }
  ]
}
```

### 2. **Obtener Item Específico**
```http
GET /api/carrito/items/{id}/
```
**Respuesta:**
```json
{
  "success": true,
  "item": {
    "id": 1,
    "carrito": 1,
    "producto_variante": 5,
    "cantidad": 2,
    "subtotal": 59.98,
    "variante_info": {...}
  }
}
```

### 3. **Agregar Item al Carrito**
```http
POST /api/carrito/items/
Content-Type: application/json

{
  "producto_variante": 5,
  "cantidad": 2
}
```
**Respuesta (nuevo):**
```json
{
  "success": true,
  "message": "Producto agregado al carrito",
  "item": {...}
}
```
**Respuesta (actualizado):**
```json
{
  "success": true,
  "message": "Cantidad actualizada en el carrito",
  "item": {...}
}
```

### 4. **Actualizar Item (PUT - Completo)**
```http
PUT /api/carrito/items/{id}/
Content-Type: application/json

{
  "producto_variante": 5,
  "cantidad": 5
}
```
**Respuesta:**
```json
{
  "success": true,
  "message": "Item actualizado exitosamente",
  "item": {...}
}
```

### 5. **Actualizar Item (PATCH - Parcial)**
```http
PATCH /api/carrito/items/{id}/
Content-Type: application/json

{
  "cantidad": 3
}
```
**Respuesta:**
```json
{
  "success": true,
  "message": "Item actualizado exitosamente",
  "item": {...}
}
```

### 6. **Eliminar Item**
```http
DELETE /api/carrito/items/{id}/
```
**Respuesta:**
```json
{
  "success": true,
  "message": "\"Camiseta Deportiva\" eliminado del carrito"
}
```

---

## 🔒 Autenticación

**Nota:** Actualmente los permisos están en `AllowAny` para testing.

Para producción, cambiar en `item_api.py`:
```python
permission_classes = [IsAuthenticated]
```

---

## 🧪 Testing con Postman/Thunder Client

### Headers requeridos (cuando se active IsAuthenticated):
```
Authorization: Token {tu_token_aqui}
Content-Type: application/json
```

### Ejemplos de prueba:

**1. Agregar producto al carrito:**
```bash
POST http://localhost:8000/api/carrito/items/
{
  "producto_variante": 1,
  "cantidad": 2
}
```

**2. Listar items:**
```bash
GET http://localhost:8000/api/carrito/items/
```

**3. Actualizar cantidad:**
```bash
PATCH http://localhost:8000/api/carrito/items/1/
{
  "cantidad": 5
}
```

**4. Eliminar item:**
```bash
DELETE http://localhost:8000/api/carrito/items/1/
```

---

## ✅ Características

- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Validación de datos
- ✅ Manejo de errores robusto
- ✅ Calcula subtotales automáticamente
- ✅ Si agregas un producto que ya existe, suma la cantidad
- ✅ Incluye información completa del producto y sus imágenes
- ✅ Solo muestra items del carrito del usuario autenticado
- ✅ Logs detallados para debugging

---

## 🚀 Próximos Pasos

1. Activar autenticación: Cambiar `AllowAny` a `IsAuthenticated`
2. Agregar campo `stock` a `Producto_Variantes` para validaciones
3. Implementar validación de stock antes de agregar/actualizar items
