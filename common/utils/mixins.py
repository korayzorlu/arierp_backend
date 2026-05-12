from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

class CompletionRateMixin:
    COMPLETION_FIELDS: list[str] = []
    
    def _is_field_filled(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True

    def get_completion_rate(self) -> float:
        total = len(self.COMPLETION_FIELDS)
        if not total:
            return 0.0
        filled = sum(
            1 for f in self.COMPLETION_FIELDS
            if self._is_field_filled(getattr(self, f, None))
        )
        return round((filled / total) * 100, 2)