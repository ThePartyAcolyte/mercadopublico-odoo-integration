# API Licitaciones - Mercado Público Chile

**Diccionario de Datos**  
**Versión**: Beta  
**URL Base**: `http://api.mercadopublico.cl`  
**Tipo de API**: REST (XML/JSON/JSONP)

---

## TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Acceso a la API](#acceso-a-la-api)
3. [Diccionario de Campos](#diccionario-de-campos)
4. [Tipos de Licitación](#tipos-de-licitación)
5. [Unidades Monetarias](#unidades-monetarias)
6. [Parámetros Enumerados](#parámetros-enumerados)
7. [Glosario](#glosario)

---

## INTRODUCCIÓN

### Propósito

La API de Mercado Público permite consumir información de Licitaciones y Órdenes de Compra generadas en la plataforma de compras públicas de ChileCompra (`www.mercadopublico.cl`).

### Contexto

- **850+ organismos del Estado chileno** compran bienes y servicios
- **118.000+ proveedores registrados**, 91% de los cuales son micro y pequeñas empresas
- API expone datos de licitaciones en estados: publicada, cerrada, desierta, adjudicada, revocada, suspendida

---

## ACCESO A LA API

### Endpoints Base

El servicio fue implementado para que las URLs puedan utilizarse mediante parámetros GET.

**Formato XML**:
```
http://api.mercadopublico.cl/servicios/v1/publico/licitaciones.xml?codigo=[Numero_licitacion]&ticket=[Ticket_Acceso]
```

**Formato JSON**:
```
http://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?codigo=[Numero_licitacion]&ticket=[Ticket_Acceso]
```

**Formato JSONP**:
```
http://api.mercadopublico.cl/servicios/v1/publico/licitaciones.jsonp?codigo=[Numero_licitacion]&ticket=[Ticket_Acceso]
```

**Formato por defecto**: JSON (si no se especifica formato)

### Parámetros Requeridos

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `codigo` | string | Número de la licitación a consultar |
| `ticket` | string | Ticket de acceso a la API |

---

## DICCIONARIO DE CAMPOS

### Estructura Raíz

La respuesta XML/JSON tiene la siguiente estructura raíz:

```
Licitaciones/
  ├── Cantidad
  ├── FechaCreacion
  ├── Version
  └── Listado/
      └── Licitacion/ (arreglo o elemento único)
```

### Campos Disponibles en Licitación

Total de campos documentados: **97**

| # | Campo | Descripción | Tipo | Largo |
|---|-------|-------------|------|-------|
| 1 | `Licitaciones/Cantidad` | Cantidad de Licitaciones consultadas | entero | — |
| 2 | `Licitaciones/FechaCreacion` | Fecha de consulta | datetime | — |
| 3 | `Licitaciones/Version` | Versión del API de Mercado Público | texto | — |
| 4 | `Licitaciones/Listado/Licitacion/CodigoExterno` | Código de la Licitación de Mercado Público | nvarchar | 100 |
| 5 | `Licitaciones/Listado/Licitacion/Nombre` | Nombre de la Licitación | nvarchar | 255 |
| 6 | `Licitaciones/Listado/Licitacion/CodigoEstado` | Código del estado en el que se encuentra la Licitación | entero | 4 |
| 7 | `Licitaciones/Listado/Licitacion/FechaCierre` | Fecha de Cierre de la Licitación | datetime | — |
| 8 | `Licitaciones/Listado/Licitacion/Descripcion` | Descripción de la Licitación u objeto de la contratación | nvarchar | max |
| 9 | `Licitaciones/Listado/Licitacion/Estado` | Estado en el que se encuentra la Licitación | nvarchar | 510 |
| 10 | `Licitaciones/Listado/Licitacion/Comprador/CodigoOrganismo` | Código de la Institución u Organismo Público responsable | nvarchar | 100 |
| 11 | `Licitaciones/Listado/Licitacion/Comprador/NombreOrganismo` | Nombre de la Institución u Organismo Público responsable | nvarchar | 510 |
| 12 | `Licitaciones/Listado/Licitacion/Comprador/RutUnidad` | RUT de la Institución u Organismo Público responsable | nvarchar | 100 |
| 13 | `Licitaciones/Listado/Licitacion/Comprador/CodigoUnidad` | Código de la Institución u Organismo Público responsable | nvarchar | 100 |
| 14 | `Licitaciones/Listado/Licitacion/Comprador/NombreUnidad` | Nombre de la Unidad de Compra perteneciente a la Institución | nvarchar | 510 |
| 15 | `Licitaciones/Listado/Licitacion/Comprador/DireccionUnidad` | Dirección de la Unidad de Compra | nvarchar | 510 |
| 16 | `Licitaciones/Listado/Licitacion/Comprador/ComunaUnidad` | Comuna de la Unidad de Compra | nvarchar | 510 |
| 17 | `Licitaciones/Listado/Licitacion/Comprador/RegionUnidad` | Región de la Unidad de Compra | nvarchar | 510 |
| 18 | `Licitaciones/Listado/Licitacion/Comprador/RutUsuario` | RUT del usuario responsable de la Licitación | nvarchar | 100 |
| 19 | `Licitaciones/Listado/Licitacion/Comprador/CodigoUsuario` | Código del usuario responsable de la Licitación | nvarchar | 100 |
| 20 | `Licitaciones/Listado/Licitacion/Comprador/NombreUsuario` | Nombre de usuario responsable de la Licitación | texto | — |
| 21 | `Licitaciones/Listado/Licitacion/Comprador/CargoUsuario` | Cargo del usuario responsable de la Licitación | nvarchar | 100 |
| 22 | `Licitaciones/Listado/Licitacion/DiasCierreLicitacion` | Cantidad de días para el cierre de la Licitación | entero | — |
| 23 | `Licitaciones/Listado/Licitacion/Informada` | Indica si la Licitación es Informada (1=Sí, 0=No) | bit | 1 |
| 24 | `Licitaciones/Listado/Licitacion/CodigoTipo` | ID del tipo de Licitación (1=Pública, 2=Privada) | entero | 4 |
| 25 | `Licitaciones/Listado/Licitacion/Tipo` | ID del tipo de Licitación de Mercado Público (Ver sección 3.1) | nvarchar | 20 |
| 26 | `Licitaciones/Listado/Licitacion/TipoConvocatoria` | Tipo de convocatoria (1=Abierto, 0=Cerrada) | int | 4 |
| 27 | `Licitaciones/Listado/Licitacion/Moneda` | Código de la moneda en la Licitación | nvarchar | 100 |
| 28 | `Licitaciones/Listado/Licitacion/Etapas` | Número de etapas de la licitación (1 o 2 etapas) | int | 4 |
| 29 | `Licitaciones/Listado/Licitacion/EstadoEtapas` | Indica las aperturas realizadas en la licitación [1,2] | int | 4 |
| 30 | `Licitaciones/Listado/Licitacion/TomaRazon` | Toma de Razón por Contraloría (1=Sí, 0=No) | int | 4 |
| 31 | `Licitaciones/Listado/Licitacion/EstadoPublicidadOfertas` | Muestra publicidad de oferta técnica (1=Sí, 0=No) | smallint | 2 |
| 32 | `Licitaciones/Listado/Licitacion/JustificacionPublicidad` | Justificación para mostrar oferta técnica para público | nvarchar | -1 |
| 33 | `Licitaciones/Listado/Licitacion/Contrato` | Tipo de contrato (1=Requiere subscripción, 2=Formaliza con OC). Solo visible para licitaciones tipo LE | int | 4 |
| 34 | `Licitaciones/Listado/Licitacion/Obras` | Indica si la licitación es de tipo obra (0=No, 2=Sí) | int | 4 |
| 35 | `Licitaciones/Listado/Licitacion/CantidadReclamos` | Número de reclamos recibidos por la Institución | entero | — |
| 36 | `Licitaciones/Listado/Licitacion/Fechas/FechaCreacion` | Fecha de Creación de la Licitación | datetime | — |
| 37 | `Licitaciones/Listado/Licitacion/Fechas/FechaCierre` | Fecha de Cierre de la Licitación | datetime | — |
| 38 | `Licitaciones/Listado/Licitacion/Fechas/FechaInicio` | Fecha de Inicio del foro de la licitación | datetime | — |
| 39 | `Licitaciones/Listado/Licitacion/Fechas/FechaFinal` | Fecha de cierre del foro de la licitación | datetime | — |
| 40 | `Licitaciones/Listado/Licitacion/Fechas/FechaPubRespuestas` | Fecha de Publicación de las Respuestas de la Licitación | datetime | — |
| 41 | `Licitaciones/Listado/Licitacion/Fechas/FechaActoAperturaTecnica` | Fecha del Acto de Apertura Técnica de la Licitación | datetime | — |
| 42 | `Licitaciones/Listado/Licitacion/Fechas/FechaActoAperturaEconomica` | Fecha del Acto de Apertura Económica de la Licitación | datetime | — |
| 43 | `Licitaciones/Listado/Licitacion/Fechas/FechaPublicacion` | Fecha de Publicación de la Licitación | datetime | — |
| 44 | `Licitaciones/Listado/Licitacion/Fechas/FechaAdjudicacion` | Fecha de Adjudicación de la Licitación | datetime | — |
| 45 | `Licitaciones/Listado/Licitacion/Fechas/FechaEstimadaAdjudicacion` | Fecha Estimada de Adjudicación de la Licitación | datetime | — |
| 46 | `Licitaciones/Listado/Licitacion/Fechas/FechaSoporteFisico` | Fecha Soporte Físico de la Licitación | datetime | — |
| 47 | `Licitaciones/Listado/Licitacion/Fechas/FechaTiempoEvaluacion` | Fecha de la Evaluación de la Licitación | datetime | — |
| 48 | `Licitaciones/Listado/Licitacion/Fechas/FechaEstimadaFirma` | Fecha Estimada de la Firma | datetime | — |
| 49 | `Licitaciones/Listado/Licitacion/Fechas/FechasUsuario` | Indica si usuario definió fechas adicionales a la licitación | datetime | — |
| 50 | `Licitaciones/Listado/Licitacion/Fechas/FechaVisitaTerreno` | Fecha de la visita a terreno | datetime | — |
| 51 | `Licitaciones/Listado/Licitacion/Fechas/FechaEntregaAntecedentes` | Fecha en que se deben entregar los Antecedentes | datetime | — |
| 52 | `Licitaciones/Listado/Licitacion/UnidadTiempoEvaluacion` | Indica la unidad de tiempo de la evaluación | int | 4 |
| 53 | `Licitaciones/Listado/Licitacion/DireccionVisita` | Dirección de visita | varchar | 500 |
| 54 | `Licitaciones/Listado/Licitacion/DireccionEntrega` | Dirección de entrega | varchar | 500 |
| 55 | `Licitaciones/Listado/Licitacion/Estimacion` | Código de tipo de estimación (Ver sección 3.3) | — | — |
| 56 | `Licitaciones/Listado/Licitacion/FuenteFinanciamiento` | Indica la fuente de financiamiento | int | 4 |
| 57 | `Licitaciones/Listado/Licitacion/VisibilidadMonto` | Hacer público el monto estimado en ficha (1=Sí, 0=No) | bit | 1 |
| 58 | `Licitaciones/Listado/Licitacion/MontoEstimado` | Monto estimado que maneja el Organismo para licitar | float | 53 |
| 59 | `Licitaciones/Listado/Licitacion/UnidadTiempo` | Tipo de unidad de tiempo asociada a "TiempoDuracionContrato" | int | 4 |
| 60 | `Licitaciones/Listado/Licitacion/Modalidad` | Tipo Modalidad de pago (30 Días, 60 Días, etc) | int | 4 |
| 61 | `Licitaciones/Listado/Licitacion/TipoPago` | Indica el tipo de pago que se realizará | int | 4 |
| 62 | `Licitaciones/Listado/Licitacion/NombreResponsablePago` | Nombre de la persona responsable del pago | nvarchar | 200 |
| 63 | `Licitaciones/Listado/Licitacion/EmailResponsablePago` | Correo electrónico de la persona responsable del pago | nvarchar | 200 |
| 64 | `Licitaciones/Listado/Licitacion/NombreResponsableContrato` | Nombre de la persona responsable del contrato | nvarchar | 200 |
| 65 | `Licitaciones/Listado/Licitacion/EmailResponsableContrato` | Correo electrónico de la persona responsable del contrato | nvarchar | 200 |
| 66 | `Licitaciones/Listado/Licitacion/FonoResponsableContrato` | Teléfono de contacto de la persona responsable del contrato | nvarchar | 200 |
| 67 | `Licitaciones/Listado/Licitacion/ProhibicionContratacion` | Indica si se prohíbe la contratación | nvarchar | 510 |
| 68 | `Licitaciones/Listado/Licitacion/SubContratacion` | Permite la subcontratación (1=Sí, 0=No) | bit | 1 |
| 69 | `Licitaciones/Listado/Licitacion/UnidadTiempoDuracionContrato` | Unidad de tiempo del contrato | int | 4 |
| 70 | `Licitaciones/Listado/Licitacion/TiempoDuracionContrato` | Duración del contrato vinculada a "UnidadTiempoDuracionContrato" | int | 4 |
| 71 | `Licitaciones/Listado/Licitacion/TipoDuracionContrato` | Nombre de período de tiempo | nvarchar | 510 |
| 72 | `Licitaciones/Listado/Licitacion/JustificacionMontoEstimado` | Justificación del monto estimado | varchar | 255 |
| 73 | `Licitaciones/Listado/Licitacion/ExtensionPlazo` | Si se han recibido 2 o menos propuestas, plazo se amplia automáticamente en 2 días hábiles (1=Extiende, 0=No) | smallint | 2 |
| 74 | `Licitaciones/Listado/Licitacion/EsBaseTipo` | Licitación fue creada a través de licitaciones tipo (1=Sí, 0=No) | bit | 1 |
| 75 | `Licitaciones/Listado/Licitacion/UnidadTiempoContratoLicitacion` | Código de período de tiempo | int | 4 |
| 76 | `Licitaciones/Listado/Licitacion/ValorTiempoRenovacion` | Indica el valor de tiempo | int | 4 |
| 77 | `Licitaciones/Listado/Licitacion/PeriodoTiempoRenovacion` | Nombre del período de tiempo de renovación | nvarchar | 510 |
| 78 | `Licitaciones/Listado/Licitacion/EsRenovable` | Período de Renovación de Contrato es renovable (1=Sí, 0=No) | bit | 1 |
| 79 | `Licitaciones/Listado/Licitacion/Adjudicacion/Tipo` | Código del tipo de documento que garantiza la adjudicación | int | 4 |
| 80 | `Licitaciones/Listado/Licitacion/Adjudicacion/Fecha` | Fecha del documento administrativo que garantiza la adjudicación | datetime | — |
| 81 | `Licitaciones/Listado/Licitacion/Adjudicacion/Numero` | Número del documento administrativo que garantiza la adjudicación | nvarchar | 100 |
| 82 | `Licitaciones/Listado/Licitacion/Adjudicacion/NumeroOferentes` | Cantidad de proveedores adjudicados | entero | — |
| 83 | `Licitaciones/Listado/Licitacion/Adjudicacion/UrlActa` | URL que despliega el acta de adjudicación en www.mercadopublico.cl | texto | — |
| 84 | `Licitaciones/Listado/Licitacion/Items/Cantidad` | Número de productos o servicios de la Licitación | entero | — |
| 85 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/CodigoEstadoLicitacion` | Código del estado en el que se encuentra la Licitación | entero | 4 |
| 86 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Correlativo` | Número que indica el correlativo del producto o servicio licitado | entero | — |
| 87 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/CodigoProducto` | Código del producto (UNSPSC Versión 7) | entero | — |
| 88 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/CodigoCategoria` | Código de la categoría (UNSPSC Versión 7) | nvarchar | 100 |
| 89 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Categoria` | Nombre de la categoría y niveles donde está incluido producto | varchar | 400 |
| 90 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/NombreProducto` | Nombre del producto o servicio | nvarchar | 510 |
| 91 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Descripcion` | Descripción del producto o servicio | nvarchar | 510 |
| 92 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/UnidadMedida` | Unidad de medida del producto o servicio | nvarchar | 510 |
| 93 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Cantidad` | Cantidad del producto o servicio | float | 8 |
| 94 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Adjudicacion/RutProveedor` | RUT del proveedor adjudicado (por línea) | nvarchar | 100 |
| 95 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Adjudicacion/NombreProveedor` | Nombre del proveedor adjudicado (por línea) | nvarchar | 500 |
| 96 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Adjudicacion/CantidadAdjudicada` | Cantidad de producto o servicio adjudicado (por línea) | nvarchar | 500 |
| 97 | `Licitaciones/Listado/Licitacion/Items/Listado/ítem/Adjudicacion/MontoUnitario` | Monto unitario del producto o servicio adjudicado (por línea) | float | 8 |

---

## TIPOS DE LICITACIÓN

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<Tipo>`

### Clasificación por Monto

| Código | Descripción |
|--------|-------------|
| **L1** | Licitación Pública Menor a 100 UTM |
| **LE** | Licitación Pública igual o superior a 100 UTM e inferior a 1.000 UTM |
| **LP** | Licitación Pública igual o superior a 1.000 UTM e inferior a 2.000 UTM |
| **LQ** | Licitación Pública igual o superior a 2.000 UTM e inferior a 5.000 UTM |
| **LR** | Licitación Pública igual o superior a 5.000 UTM |
| **E2** | Licitación Privada Menor a 100 UTM |
| **CO** | Licitación Privada igual o superior a 100 UTM e inferior a 1.000 UTM |
| **B2** | Licitación Privada igual o superior a 1.000 UTM e inferior a 2.000 UTM |
| **H2** | Licitación Privada igual o superior a 2.000 UTM e inferior a 5.000 UTM |
| **I2** | Licitación Privada Mayor a 5.000 UTM |
| **LS** | Licitación Pública Servicios Personales Especializados |

---

## UNIDADES MONETARIAS

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<Moneda>`

| Código | Descripción |
|--------|-------------|
| **CLP** | Peso Chileno |
| **CLF** | Unidad de Fomento |
| **USD** | Dólar Americano |
| **UTM** | Unidad Tributaria Mensual |
| **EUR** | Euro |

---

## PARÁMETROS ENUMERADOS

### Monto Estimado

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<Estimacion>`

Asociación del monto estimado:

| Código | Descripción |
|--------|-------------|
| **1** | Presupuesto Disponible |
| **2** | Precio Referencial |
| **3** | Monto no es posible de estimar |

---

### Modalidad de Pago

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<Modalidad>`

| Código | Descripción |
|--------|-------------|
| **1** | Pago a 30 días |
| **2** | Pago a 30, 60 y 90 días |
| **3** | Pago al día |
| **4** | Pago Anual |
| **5** | Pago Bimensual |
| **6** | Pago Contra Entrega Conforme |
| **7** | Pagos Mensuales |
| **8** | Pago Por Estado de Avance |
| **9** | Pago Trimestral |
| **10** | Pago a 60 días |

---

### Unidad de Tiempo de Evaluación

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<UnidadTiempoEvaluacion>`

| Código | Descripción |
|--------|-------------|
| **1** | Horas |
| **2** | Días |
| **3** | Semanas |
| **4** | Meses |
| **5** | Años |

---

### Unidad de Tiempo Duración del Contrato

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<UnidadTiempoDuracionContrato>`

| Código | Descripción |
|--------|-------------|
| **1** | Horas |
| **2** | Días |
| **3** | Semanas |
| **4** | Meses |
| **5** | Años |

---

### Tipo de Acto Administrativo en Adjudicación

**Ruta**: `<Licitaciones>/<Listado>/<Licitacion>/<Adjudicacion>/<Tipo>`

Este tipo de documento se despliega solo cuando la Licitación se encuentra en estado "Adjudicada".

| Código | Descripción |
|--------|-------------|
| **1** | Autorización |
| **2** | Resolución |
| **3** | Acuerdo |
| **4** | Decreto |
| **5** | Otros |

---

## GLOSARIO

| Término | Definición |
|---------|-----------|
| **UNSPSC** | Estándar de clasificación de productos y servicios de las Naciones Unidas (Versión 7) |
| **UTM** | Unidad Tributaria Mensual (indexador chileno) |
| **CLP** | Código ISO 4217 para Peso Chileno |
| **Licitación Pública** | Proceso abierto a cualquier proveedor calificado registrado en ChileCompra |
| **Licitación Privada** | Proceso donde el organismo convoca específicamente a ciertos proveedores |
| **Convocatoria Abierta** | TipoConvocatoria = 1 |
| **Convocatoria Cerrada** | TipoConvocatoria = 0 |
| **Toma de Razón** | Revisión obligatoria por la Contraloría General de la República |
| **Etapas** | Primera (técnica) y segunda (económica) etapa de evaluación |
| **Adjudicación** | Acto administrativo que formaliza la selección del proveedor ganador |
| **Item** | Línea de producto o servicio dentro de una licitación |
| **RUT** | Rol Único Tributario (identificador fiscal chileno) |
| **DCCP** | Dirección de Compras y Contratación Pública |

---

**Última actualización**: Diccionario de Datos Beta  
**Basado en**: Documentación oficial de api.mercadopublico.cl
