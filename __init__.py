# Parche de runtime para compatibilidad de recoleccion de basura (WeakSet) en Python 3.14+
import odoo.tools.misc
if not getattr(odoo.tools.misc.OrderedSet, '_py314_patched', False):
    def _safe_orderedset_copy(self):
        inst = object.__new__(self.__class__)
        inst._map = self._map.copy()
        return inst
    odoo.tools.misc.OrderedSet.copy = _safe_orderedset_copy
    odoo.tools.misc.OrderedSet._py314_patched = True

from . import models
from . import wizards