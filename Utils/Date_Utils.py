from datetime import datetime
import re

class DateUtils:
    @staticmethod
    def normalizedatetime(datestr=None):
        """Convierte cualquier fecha a ISO 8601 (YYYY-MM-DDTHH:MM:SS.sssZ)."""
        if not datestr:
            return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Patrones CORREGIDOS (sin r-a inválido)
        patterns = [
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO básico
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)',  # Con milisegundos
            r'"publishDate":"([^"]+)"',  # La Razón[file:4]
            r'(\d{1,2})\s*(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)',  # El País[file:5]
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-Z]?\d{2}?'  # La Razón genérico
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(datestr))
            if match:
                dtstr = match.group(1)
                if not dtstr.endswith('Z'):
                    dtstr += '.000Z' if '.' not in dtstr else 'Z'
                return dtstr
        
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
