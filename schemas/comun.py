from pydantic import BaseModel, ConfigDict, field_validator


class Entrada(BaseModel):
    """Base de los cuerpos de entrada: recorta espacios y trata los textos vacíos como ausentes."""

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def vacio_a_none(cls, valor):
        return None if isinstance(valor, str) and valor.strip() == "" else valor


class PersonaResumen(BaseModel):
    id: int
    nombre: str
    apellido: str
