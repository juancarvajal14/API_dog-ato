class ErrorNegocio(Exception):
    """Error de regla de negocio que main.py convierte en respuesta HTTP."""

    def __init__(self, status_code: int, detail: str, headers: dict | None = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)
