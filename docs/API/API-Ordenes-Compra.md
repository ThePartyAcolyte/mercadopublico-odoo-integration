# API Órdenes de Compra - Mercado Público Chile

**Diccionario de Datos**  
**Versión**: Beta  
**URL Base**: `http://api.mercadopublico.cl`  
**Tipo de API**: REST (XML/JSON/JSONP)

---

## TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Acceso a la API](#acceso-a-la-api)
3. [Diccionario de Campos](#diccionario-de-campos)
4. [Tipos de Orden de Compra](#tipos-de-orden-de-compra)
5. [Unidades Monetarias](#unidades-monetarias)
6. [Parámetros Enumerados](#parámetros-enumerados)
7. [Glosario](#glosario)

---

## INTRODUCCIÓN

### Propósito

La API de Órdenes de Compra permite consumir información de las Órdenes de Compra generadas en la plataforma de compras públicas de ChileCompra (`www.mercadopublico.cl`).

### Contexto

- **850+ organismos del Estado chileno** realizan compras públicas
- **118.000+ proveedores registrados**, 91% de los cuales son micro y pequeñas empresas
- API expone datos de órdenes de compra en estados: enviada a proveedor, aceptada, cancelada, recepción conforme, pendiente de recepcionar, recepcionada parcialmente, recepción conforme incompleta

---

## ACCESO A LA API

### Endpoints Base

El servicio fue implementado para que las URLs puedan utilizarse mediante parámetros GET.

**Formato XML**:
```
http://api.mercadopublico.cl/servicios/v1/publico/OrdenCompra.xml?codigo=[Codigo_OC]&ticket=[Ticket_Acceso]
```

**Formato JSON**:
```
http://api.mercadopublico.cl/servicios/v1/publico/OrdenCompra.json?codigo=[Codigo_OC]&ticket=[Ticket_Acceso]
```

**Formato JSONP**:
```
http://api.mercadopublico.cl/servicios/v1/publico/OrdenCompra.jsonp?codigo=[Codigo_OC]&ticket=[Ticket_Acceso]
```

**Formato por defecto**: JSON (si no se especifica formato)

### Parámetros Requeridos

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `codigo` | string | Código de la Orden de Compra a consultar |
| `ticket` | string | Ticket de acceso a la API |

---

## DICCIONARIO DE CAMPOS

### Estructura Raíz

La respuesta XML/JSON tiene la siguiente estructura raíz:

```
Ordenes/
  ├── Cantidad
  ├── FechaCreacion
  ├── Version
  └── Listado/
      └── OrdenCompra/ (arreglo o elemento único)
```

### Campos Disponibles en Orden de Compra

Total de campos documentados: **74**

| # | Campo | Descripción | Tipo | Largo |
|---|-------|-------------|------|-------|
| 1 | `Cantidad` | Cantidad de Órdenes de Compra consultadas | int | — |
| 2 | `FechaCreacion` | Fecha de consulta | datetime | — |
| 3 | `Version` | Versión del API de Mercado Público | texto | — |
| 4 | `Listado/Codigo` | Código de la Orden de Compra de Mercado Público | nvarchar | 50 |
| 5 | `Listado/Nombre` | Nombre de la Orden de Compra | nvarchar | 255 |
| 6 | `Listado/CodigoEstado` | Código del estado en el que se encuentra la OC | int | 4 |
| 7 | `Listado/CodigoLicitacion` | Código de la Licitación asociada a la OC | nvarchar | 50 |
| 8 | `Listado/Descripcion` | Descripción de la Orden de Compra | nvarchar | 2000 |
| 9 | `Listado/CodigoTipo` | Código del tipo de Orden de Compra | nvarchar | 80 |
| 10 | `Listado/Tipo` | Tipo de Orden de Compra (Ver sección 3.1) | nvarchar | 2 |
| 11 | `Listado/TipoMoneda` | Tipo Moneda de la Orden de Compra | nvarchar | 255 |
| 12 | `Listado/CodigoEstadoProveedor` | Código estado del Proveedor | int | — |
| 13 | `Listado/EstadoProveedor` | Estado del Proveedor | nvarchar | 255 |
| 14 | `Listado/Fechas/FechaCreacion` | Fecha de creación de la Orden de Compra | datetime | — |
| 15 | `Listado/Fechas/FechaEnvio` | Fecha de envío de la Orden de Compra | datetime | — |
| 16 | `Listado/Fechas/FechaAceptacion` | Fecha de aceptación de Orden de Compra | datetime | — |
| 17 | `Listado/Fechas/FechaCancelacion` | Fecha de cancelación de orden de compra | datetime | — |
| 18 | `Listado/Fechas/FechaUltimaModificacion` | Fecha de Última Modificación de la Orden de Compra | datetime | — |
| 19 | `Listado/TieneItems` | Indica si tiene Items (1=Sí, 0=No) | nvarchar | 255 |
| 20 | `Listado/PromedioCalificacion` | Promedio de calificación del proveedor | float | — |
| 21 | `Listado/CantidadEvaluacion` | Evaluación del proveedor | int | — |
| 22 | `Listado/Descuentos` | Descuento aplicado a la Orden de Compra | float | — |
| 23 | `Listado/Cargos` | **Cargos aplicados a la Orden de Compra** | float | — |
| 24 | `Listado/TotalNeto` | **Total neto de la Orden de Compra** | float | — |
| 25 | `Listado/PorcentajeIva` | **Porcentaje del IVA aplicado a la Orden de Compra** | float | — |
| 26 | `Listado/Impuestos` | Impuesto aplicado a la Orden de Compra | float | — |
| 27 | `Listado/Total` | Total de la Orden de Compra | float | — |
| 28 | `Listado/Financiamiento` | Fuente de Financiamiento | nvarchar | 255 |
| 29 | `Listado/Pais` | País al que pertenece la Orden de Compra | nvarchar | 255 |
| 30 | `Listado/TipoDespacho` | **Código que identifica el Tipo de Despacho (Anexo 3.3)** | nvarchar | 255 |
| 31 | `Listado/FormaPago` | **Código que identifica la forma de pago (Anexo 3.4)** | nvarchar | 255 |
| 32 | `Listado/Comprador/CodigoOrganismo` | Código que identifica al organismo comprador | nvarchar | 20 |
| 33 | `Listado/Comprador/NombreOrganismo` | Nombre del organismo del comprador | nvarchar | 255 |
| 34 | `Listado/Comprador/RutUnidad` | RUT de la Unidad | nvarchar | 20 |
| 35 | `Listado/Comprador/CodigoUnidad` | **Código de Unidad** | nvarchar | 20 |
| 36 | `Listado/Comprador/NombreUnidad` | **Nombre de Unidad** | nvarchar | 255 |
| 37 | `Listado/Comprador/Actividad` | Actividad del Comprador | nvarchar | 255 |
| 38 | `Listado/Comprador/DireccionUnidad` | Dirección de la unidad compradora | nvarchar | 255 |
| 39 | `Listado/Comprador/ComunaUnidad` | Comuna de la unidad compradora | nvarchar | 255 |
| 40 | `Listado/Comprador/RegionUnidad` | Región de la unidad compradora | nvarchar | 255 |
| 41 | `Listado/Comprador/Pais` | País de la unidad compradora | nvarchar | 255 |
| 42 | `Listado/Comprador/NombreContacto` | Nombre contacto del comprador | nvarchar | 255 |
| 43 | `Listado/Comprador/CargoContacto` | Cargo del contacto del comprador | nvarchar | 255 |
| 44 | `Listado/Comprador/FonoContacto` | Teléfono del Contacto del comprador | nvarchar | 100 |
| 45 | `Listado/Comprador/MailContacto` | E-Mail del contacto del comprador | nvarchar | 50 |
| 46 | `Listado/Proveedor/Codigo` | Código del proveedor | nvarchar | 20 |
| 47 | `Listado/Proveedor/Nombre` | Nombre del proveedor | nvarchar | 255 |
| 48 | `Listado/Proveedor/Actividad` | Actividad del Proveedor | nvarchar | 255 |
| 49 | `Listado/Proveedor/CodigoSucursal` | Código de la sucursal del proveedor | nvarchar | 20 |
| 50 | `Listado/Proveedor/NombreSucursal` | Nombre de la sucursal del proveedor | nvarchar | 255 |
| 51 | `Listado/Proveedor/RutSucursal` | RUT del Proveedor | nvarchar | 20 |
| 52 | `Listado/Proveedor/Direccion` | Dirección del proveedor | nvarchar | 255 |
| 53 | `Listado/Proveedor/Comuna` | Comuna del proveedor | nvarchar | 255 |
| 54 | `Listado/Proveedor/Region` | Región del proveedor | nvarchar | 255 |
| 55 | `Listado/Proveedor/Pais` | País del proveedor | nvarchar | 255 |
| 56 | `Listado/Proveedor/NombreContacto` | Nombre contacto del proveedor | nvarchar | 255 |
| 57 | `Listado/Proveedor/CargoContacto` | Cargo del contacto del proveedor | nvarchar | 255 |
| 58 | `Listado/Proveedor/FonoContacto` | **Teléfono del contacto del proveedor** | nvarchar | 255 |
| 59 | `Listado/Proveedor/MailContacto` | E-Mail del contacto del proveedor | nvarchar | 255 |
| 60 | `Listado/Items/Cantidad` | Cantidad de Items (Productos) de la OC | int | — |
| 61 | `Listado/Items/Listado` | Listado de Items | — | — |
| 62 | `Listado/Items/Listado/Correlativo` | **Correlativo de Items** | bitint | — |
| 63 | `Listado/Items/Listado/CodigoCategoria` | Código de categoría a la que pertenece el producto | int | — |
| 64 | `Listado/Items/Listado/Categoria` | Categoría a la que pertenece el producto | varchar | 400 |
| 65 | `Listado/Items/Listado/CodigoProducto` | Código del producto | int | — |
| 66 | `Listado/Items/Listado/EspecificacionComprador` | Especificaciones del producto que necesita el comprador | nvarchar | -1 |
| 67 | `Listado/Items/Listado/EspecificacionProveedor` | Especificaciones del producto proveído por el proveedor | nvarchar | 510 |
| 68 | `Listado/Items/Listado/Cantidad` | Cantidad de productos | float | — |
| 69 | `Listado/Items/Listado/Moneda` | **Tipo de moneda del producto** | nvarchar | 100 |
| 70 | `Listado/Items/Listado/PrecioNeto` | **Precio neto o precio unitario del producto** | float | — |
| 71 | `Listado/Items/Listado/TotalCargos` | **Total cargos asociados a la multiplicación del PrecioNeto * Cantidad** | float | — |
| 72 | `Listado/Items/Listado/TotalDescuentos` | **Total Descuentos asociados a la multiplicación del PrecioNeto * Cantidad** | float | — |
| 73 | `Listado/Items/Listado/TotalImpuestos` | Total de impuesto asociados a la multiplicación del PrecioNeto * Cantidad | float | — |
| 74 | `Listado/Items/Listado/Total` | Total final de precios de los productos | float | — |

---

## TIPOS DE ORDEN DE COMPRA

**Ruta**: `<Ordenes>/<Listado>/<OrdenCompra>/<Tipo>`

Descripción: ID del tipo de Orden de Compra de Mercado Público

| Código | Abreviación | Descripción |
|--------|-------------|-------------|
| **8** | SE | Sin emisión automática |
| **9** | CM | Convenio Marco |

---

## UNIDADES MONETARIAS

**Ruta**: `<Ordenes>/<Listado>/<OrdenCompra>/<TipoMoneda>`

Descripción: Código de la moneda en la Orden de Compra

| Valor | Descripción |
|-------|-------------|
| **CLP** | Peso Chileno |
| **CLF** | Unidad de Fomento |
| **USD** | Dólar Americano |
| **UTM** | Unidad Tributaria Mensual |
| **EUR** | Euro |

---

## PARÁMETROS ENUMERADOS

### Tipo de Despacho

**Ruta**: `<Ordenes>/<Listado>/<OrdenCompra>/<TipoDespacho>`

Descripción: Tipo de despacho

| Código | Descripción |
|--------|-------------|
| **7** | Despachar a Dirección de envío |
| **9** | Despachar según programa adjuntado |
| **12** | Otra Forma de Despacho (Ver Instrucciones) |
| **14** | Retiramos de su bodega |
| **20** | Despacho por courier o encomienda aérea |
| **21** | Despacho por courier o encomienda terrestre |
| **22** | A convenir |

---

### Forma de Pago

**Ruta**: `<Ordenes>/<Listado>/<OrdenCompra>/<FormaPago>`

Descripción: Forma de pago

| Código | Descripción |
|--------|-------------|
| **1** | 15 días contra la recepción de la factura |
| **2** | 30 días contra la recepción de la factura |
| **39** | Otra forma de pago |
| **46** | 50 días contra la recepción de la factura |
| **47** | 60 días contra la recepción de la factura |

---

## RELACIONES Y REFERENCIAS

### Relación con Licitaciones

Las Órdenes de Compra pueden estar asociadas a Licitaciones a través del campo:

```
Listado/CodigoLicitacion
```

Utilice este código para consultar la licitación correspondiente en la API de Licitaciones.

### Relación con Compra Ágil

Si la Orden de Compra proviene de un proceso de Compra Ágil, puede relacionarla usando:

```
Listado/CodigoLicitacion  (aunque para Compra Ágil corresponde al código de Compra Ágil)
```

---

## ESTADOS DE ORDEN DE COMPRA

| Estado | Descripción |
|--------|-------------|
| **Enviada a proveedor** | OC fue creada y enviada al proveedor para su aceptación |
| **Aceptada** | El proveedor aceptó la orden de compra |
| **Cancelada** | La orden de compra fue cancelada por el comprador |
| **Recepción Conforme** | El comprador ha recibido conforme los productos/servicios |
| **Pendiente de recepcionar** | La OC está esperando recepción de productos/servicios |
| **Recepcionada parcialmente** | Se han recibido parcialmente los productos/servicios |
| **Recepción conforme incompleta** | Recepción completa pero con algunas observaciones |

---

## EJEMPLOS DE CONSULTA

### Ejemplo 1: Llamada básica en JSON

```bash
curl "http://api.mercadopublico.cl/servicios/v1/publico/OrdenCompra.json?codigo=1057532-156-AG26&ticket=TU_TICKET_AQUI"
```

### Ejemplo 2: Llamada en XML

```bash
curl "http://api.mercadopublico.cl/servicios/v1/publico/OrdenCompra.xml?codigo=1057532-156-AG26&ticket=TU_TICKET_AQUI"
```

### Ejemplo 3: Python

```python
import requests
import json

ticket = 'TU_TICKET_AQUI'
codigo = '1057532-156-AG26'
url = f'http://api.mercadopublico.cl/servicios/v1/publico/OrdenCompra.json?codigo={codigo}&ticket={ticket}'

response = requests.get(url)
data = response.json()

# Acceder a información principal
oc = data['Ordenes']['Listado'][0]  # Si hay un único resultado
print(f"Código: {oc['Codigo']}")
print(f"Nombre: {oc['Nombre']}")
print(f"Estado: {oc['EstadoProveedor']}")
print(f"Total: {oc['Total']} {oc['TipoMoneda']}")

# Acceder a items
if oc['TieneItems'] == 1 or oc['TieneItems'] == '1':
    items = oc['Items']['Listado']
    for item in items:
        print(f"  - {item['CodigoProducto']}: {item['Cantidad']} x {item['PrecioNeto']}")
```

---

## GLOSARIO

| Término | Definición |
|---------|-----------|
| **OC / Orden de Compra** | Documento oficial emitido por el comprador que formaliza la compra al proveedor seleccionado |
| **RUT** | Rol Único Tributario (identificador fiscal chileno) |
| **Licitación** | Proceso de selección de proveedores en compras públicas |
| **Compra Ágil** | Mecanismo de contratación simplificada para adquisición rápida |
| **Convenio Marco** | Acuerdo previo entre comprador y proveedor sobre términos generales |
| **IVA** | Impuesto al Valor Agregado (19% en Chile) |
| **Courier** | Servicio de transporte de encomiendas |
| **Recepción Conforme** | El comprador verifica y acepta que productos/servicios cumplen con lo solicitado |
| **Sucursal** | Establecimiento secundario de una empresa proveedor |
| **DCCP** | Dirección de Compras y Contratación Pública |

---

**Última actualización**: Diccionario de Datos Beta  
**Basado en**: Documentación oficial de api.mercadopublico.cl
