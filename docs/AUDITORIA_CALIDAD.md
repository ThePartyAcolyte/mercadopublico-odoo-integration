# Auditoría de Calidad de Código — Módulo MercadoPublico-Odoo

**Fecha:** 2026-06-05  
**Alcance:** Todos los archivos `.py` del módulo  
**Objetivo:** Identificar bugs, código muerto, duplicación, problemas de rendimiento y deuda técnica antes del lanzamiento a producción.

---

## Estado General

El módulo tiene una arquitectura sólida y cubre los flujos principales correctamente. Sin embargo, contiene bugs de alta severidad que afectarían directamente a una instalación en producción, junto con varios patrones de código que acumulan deuda técnica. El objetivo de esta auditoría es dejar el código limpio y sin retrocompatibilidades innecesarias, listo para empaquetar y desplegar en una instancia limpia de Odoo 18.

---

## Hallazgos por Severidad

### Alta — Bugs activos en producción

#### A-01: Campos inexistentes escritos desde el wizard de feedback

**Archivo:** `wizards/mercadopublico_licitacion_descartar_wizard.py` líneas 95, 99, 103  
**Descripción:** El método `action_confirmar()` escribe dos campos que no existen en el modelo `mercadopublico.licitacion`:
- `vals['modo_analisis_ejecutado'] = 'manual'`
- `vals['relevancia'] = 0` / `vals['relevancia'] = 100`

El modelo tiene el campo `rating` (Selection `'0'`–`'3'`), no `relevancia`. Estos writes o fallan silenciosamente o lanzan `ValueError` en producción, dejando la decisión del usuario sin persistirse correctamente.

**Decisión:** Eliminar `modo_analisis_ejecutado` (no tiene definición en ningún modelo). Reemplazar `relevancia` por `rating` con los valores correctos del tipo Selection.

---

#### A-02: `NameError` latente en `analizar_pendientes()`

**Archivo:** `models/mercadopublico_api.py` línea 359  
**Descripción:** Dentro del bucle que procesa ítems, se accede a `cats_odoo`:
```python
cat_record = cats_odoo.filtered(lambda c: c.codigo == item_cat)
```
Sin embargo, `cats_odoo` solo se define si `categorias_extraidas` no está vacío (línea 346). Si una licitación no tiene categorías extraídas pero `cat_filtro_ids` está configurado, el código llega a la línea 359 con `cats_odoo` indefinida, produciendo un `NameError` que deja la licitación en estado `nuevo` para siempre.

**Decisión:** Inicializar `cats_odoo` como recordset vacío antes del bloque condicional.

---

#### A-03: `raise_if_not_found` faltante en cron de archivado

**Archivo:** `models/mercadopublico_licitacion.py` línea 192  
**Descripción:** En `cron_archivar_licitaciones_expiradas()`:
```python
self.env.ref('MercadoPublico-Odoo.etapa_convertida').id  # sin raise_if_not_found=False
```
Justo encima, `etapa_descartada` sí usa `raise_if_not_found=False`. Si el XML ID `etapa_convertida` no existe (instalación incompleta, datos corrompidos), este cron falla con excepción no controlada en vez de degradarse con gracia.

**Decisión:** Agregar `raise_if_not_found=False` y proteger el acceso a `.id`.

---

### Media — Problemas de rendimiento y seguridad

#### M-01: N+1 queries en los bucles de importación

**Archivo:** `models/mercadopublico_api.py` líneas 206, 241, 529  
**Descripción:** En `importar_licitaciones()` y `sincronizar_organismos()` se hace una query SQL individual por cada elemento del listado recibido de la API:
```python
# Se ejecuta cientos de veces, una por cada ítem
if self.env['mercadopublico.licitacion'].search_count([('codigo', '=', codigo)]) > 0:
```
Con listas de 100–500 ítems esto genera cientos de queries cuando bastaría una sola.

**Decisión:** Pre-cargar todos los códigos existentes en un `set` antes del bucle:
```python
codigos_existentes = set(
    self.env['mercadopublico.licitacion'].search([]).mapped('codigo')
)
```

---

#### M-02: Gestión de librerías Python desde la interfaz web

**Archivos:** `models/res_config_settings.py` líneas 84–100, `wizards/mercadopublico_onboarding_wizard.py` líneas 38–59  
**Descripción:** Los métodos `action_install_libraries()` ejecutan `pip install` directamente desde el proceso del servidor web mediante `subprocess.check_call`. Esto es problemático porque:
1. En Odoo.sh y entornos containerizados el filesystem puede ser de solo lectura.
2. En producción con múltiples workers, la instalación en un worker no se propaga a los demás sin reinicio.
3. Otorga a cualquier usuario con acceso a Configuración la capacidad de ejecutar procesos arbitrarios en el servidor.

**Decisión:** Eliminar `action_install_libraries()` de ambos archivos. La dependencia ya está declarada en `__manifest__.py` bajo `external_dependencies`. Reemplazar el botón de instalación por un mensaje informativo que instruya al administrador del sistema a instalar la librería vía `pip` o en el panel de módulos de Odoo.sh. La bandera `FUZZY_AVAILABLE` ya existe y el sistema debe operar correctamente sin la librería mediante búsqueda simple como fallback — verificar y documentar este fallback explícitamente.

---

#### M-03: Credencial hardcodeada en código fuente

**Archivo:** `models/res_company.py` línea 6  
**Descripción:**
```python
mercadopublico_api_ticket = fields.Char(default='F8537A18-6766-4DEF-9E59-426B4FEE2844', ...)
```
Aunque es un ticket de prueba público de ChileCompra, su presencia en el repositorio git genera ruido en auditorías de seguridad automáticas y normaliza la práctica de tener credenciales en el código.

**Decisión:** Eliminar el valor por defecto del campo. Limpiar el historial de git con `git filter-repo` o `BFG Repo-Cleaner` para remover el valor de todos los commits anteriores. El onboarding ya exige ingresar el ticket como primer paso.

---

### Baja — Deuda técnica y antipatrones

#### B-01: Código duplicado — Detección de `fuzzywuzzy`

**Archivos:** `mercadopublico_api.py` L6–10, `res_config_settings.py` L68–76, `mercadopublico_onboarding_wizard.py` L23–31  
**Descripción:** El mismo bloque de detección de la librería está copiado tres veces.  
**Decisión:** Consolidar en un único helper en `mercadopublico_api.py` o en un archivo `utils.py`. Los demás archivos importan la constante `FUZZY_AVAILABLE`.

---

#### B-02: Construcción de URL duplicada

**Archivo:** `models/mercadopublico_licitacion.py` líneas 164–167 y 175–179  
**Descripción:** El mismo f-string condicional para construir la URL de Mercado Público aparece en `create()` y en `action_abrir_mercadopublico()`.  
**Decisión:** Extraer a un método `_build_url(codigo, tipo_proceso)` y llamarlo desde ambos lugares.

---

#### B-03: Imports dentro de métodos

**Descripción:** `import pytz` está dentro de dos métodos en `mercadopublico_api.py` (L69, L181) y dentro de `set_values()` en `res_config_settings.py` (L51). `from datetime import datetime, timedelta` también dentro de `set_values()`. `from odoo.exceptions import ValidationError` dentro de `action_finish_onboarding()`.  
**Decisión:** Mover todos los imports al nivel de módulo.

---

#### B-04: Campo `name` redundante en `MercadoPublicoFiltro`

**Archivo:** `models/mercadopublico_filtro.py`  
**Descripción:** El modelo tiene `name` (computed, store=True, readonly=False) y `keyword` (el campo real). El compute solo asigna `name` si está vacío, lo que hace que `name` y `keyword` puedan divergir indefinidamente si el usuario edita `keyword` después de crear el registro. La lógica de retrocompatibilidad en `create()` es un vestigio sin uso activo.  
**Decisión:** Eliminar `name`, el campo compute, la constrain, y el override de `create()`. Usar `keyword` directamente como `_rec_name`. No hay retrocompatibilidad que preservar.

---

#### B-05: Anti-patrón `MercadoPublicoDashboard` como modelo persistido

**Archivo:** `models/mercadopublico_dashboard.py`  
**Descripción:** El dashboard es un `models.Model` con un único registro en BD y todos sus campos son `compute` sin `store`. Esto combina lo peor de ambos mundos: acceso a BD innecesario + recálculo siempre. `action_check_status()` llama `_compute_kpis()` manualmente, lo cual no tiene efecto persistente.  
**Decisión:** Convertido a `models.TransientModel`. El router crea un nuevo registro efímero en cada visita. Se eliminaron los métodos muertos `action_check_status()` y `cron_analizar_licitaciones()` (este último nunca fue llamado por ningún cron — los crons apuntan a `mercadopublico.api`). La motivación original de mantenerlo persistido (recarga de formulario vacío al instalar dependencias) desapareció con la eliminación de M-02. Se eliminó también la action `action_mercadopublico_dashboard` con `res_id=1` hardcodeado de `window_actions.xml` ya que no era utilizada por ningún menú.

---

#### B-06: `except` sin tipo en `_parse_fecha`

**Archivo:** `models/mercadopublico_api.py` línea 572  
```python
except: return False
```
Captura `SystemExit`, `KeyboardInterrupt` y errores de memoria.  
**Decisión:** Reemplazar por `except (ValueError, AttributeError, TypeError): return False`.

---

#### B-07: `add_to_compute` sobre campo `related`

**Archivo:** `models/mercadopublico_licitacion.py` línea 109  
**Descripción:** `self.env.add_to_compute(self.env['mercadopublico.licitacion']._fields['organismo_favorito'], self)` — `organismo_favorito` es un campo `related`, no computed con lógica propia. Esta llamada no tiene efecto.  
**Decisión:** Eliminar la línea.

---

#### B-08: Fallback de búsqueda simple sin `fuzzywuzzy` no verificado

**Archivo:** `models/mercadopublico_api.py`  
**Descripción:** La bandera `FUZZY_AVAILABLE` existe pero el código solo ejecuta matching de texto cuando la librería está disponible. Si `FUZZY_AVAILABLE` es `False`, las palabras clave y tags son silenciosamente ignoradas en el filtrado (líneas 396–409), con un mensaje de log menor. El usuario no recibe ninguna indicación en la interfaz.  
**Decisión:** Implementar fallback explícito con `str.lower() in texto` cuando `FUZZY_AVAILABLE` es `False`, y mostrar un aviso en la UI (Settings + Onboarding) explicando la degradación. Documentar la diferencia de precisión entre ambos modos.

---

## Trabajos Pendientes — Backlog

### P-01: Refactorizar el sistema de Tags de Productos como Palabras Clave ✅

**Contexto:** La opción anterior "Usar Tags de Productos como Palabras Clave" cargaba *todos* los tags del sistema en cada análisis, generando falsos positivos con tags internos no relacionados al rubro comercial.

**Implementado:**

1. **Eliminado** `mercadopublico_usar_tags_productos` de `res_company.py`, `res_config_settings.py`, `mercadopublico_api.py` y el wizard de onboarding.
2. **Agregado en Onboarding** el paso "3b. Importar Tags de Productos como Palabras Clave": campo `import_tag_ids` (Many2many a `product.tag`) donde el usuario selecciona explícitamente qué tags importar. Los seleccionados se crean como registros `mercadopublico.filtro` al guardar el onboarding.
3. **Agregado en Ajustes** `mercadopublico_auto_import_tags` (Boolean). Si está activo, un hook en `product.tag.create()` (en `product_extension.py`) crea automáticamente el `mercadopublico.filtro` correspondiente y lo vincula a las palabras clave de la compañía.
4. Los tags importados son registros normales de `mercadopublico.filtro`, editables y desactivables individualmente sin vínculo al tag original.

---

### P-02: Limpiar historial git de la credencial API

**Descripción:** (RESUELTO) El historial de git ha sido limpiado mediante la creación de un Orphan Branch para eliminar todos los commits antiguos.
**Estado:** Completado.

---

### P-03: Migrar de `fuzzywuzzy` a `thefuzz` ✅

**Descripción:** `fuzzywuzzy` está deprecated. El paquete sucesor oficial es `thefuzz` (mismo API, mismo autor). Cambio drop-in: `from fuzzywuzzy import fuzz` → `from thefuzz import fuzz`. Actualizado `__manifest__.py`, `mercadopublico_api.py`, `res_config_settings_views.xml` y `mercadopublico_onboarding_wizard_view.xml`.

---

### P-04: Soporte multi-compañía para `codigo_uniq` ✅

**Descripción:** Cambiado `unique(codigo)` → `unique(codigo, company_id)` en `_sql_constraints` de `mercadopublico.licitacion`. Permite que dos compañías en la misma instancia de Odoo rastreen la misma licitación de forma independiente.

---

## Checklist de Cierre para Producción

- [x] **A-01** Corregir campos inexistentes en `action_confirmar()` del wizard de feedback
- [x] **A-02** Inicializar `cats_odoo` antes del bloque condicional en `analizar_pendientes()`
- [x] **A-03** Agregar `raise_if_not_found=False` en `cron_archivar_licitaciones_expiradas()`
- [x] **M-01** Reemplazar N+1 queries por pre-carga de códigos en sets
- [x] **M-02** Eliminar `action_install_libraries()` y reemplazar por mensajes informativos
- [x] **M-03** Eliminar credencial hardcodeada + limpiar historial git (P-02)
- [x] **B-01** Consolidar detección de `fuzzywuzzy` en un único punto
- [x] **B-02** Extraer `_build_url()` para eliminar duplicación de URL
- [x] **B-03** Mover imports al nivel de módulo
- [x] **B-04** Eliminar campo `name` de `MercadoPublicoFiltro`, usar `keyword` como `_rec_name`
- [x] **B-05** Convertir `MercadoPublicoDashboard` a `TransientModel`; eliminar métodos muertos
- [x] **B-06** Especificar tipos en `except` de `_parse_fecha`
- [x] **B-07** Eliminar `add_to_compute` sobre campo related
- [x] **B-08** Implementar fallback explícito de búsqueda simple + aviso en UI
- [x] **P-01** Refactorizar sistema de Tags: selección explícita en onboarding + hook auto-import
- [x] **P-03** Migrar de `fuzzywuzzy` a `thefuzz` (drop-in replacement)
- [x] **P-04** Constraint `codigo_uniq` → `unique(codigo, company_id)` para multi-compañía
- [x] **P-02** Limpiar historial git de la credencial API
- [ ] Verificar que `external_dependencies` en `__manifest__.py` es suficiente para Odoo.sh
- [ ] Ejecutar instalación en instancia limpia de Odoo 18 y validar flujo completo de onboarding
