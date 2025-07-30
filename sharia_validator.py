# sharia_validator.py

def validar_sharia(asset_name: str, descripcion: str) -> str:
    """
    Valida si un activo cumple con los principios de la ley Sharia.
    Esta es una simulación básica. Puedes integrar API reales como IdealRatings más adelante.
    """
    criterios_prohibidos = ["alcohol", "armas", "juegos de azar", "interés", "pornografía", "tabaco"]
    contenido = f"{asset_name.lower()} {descripcion.lower()}"

    for criterio in criterios_prohibidos:
        if criterio in contenido:
            return "⛔ No cumple con los principios de la Sharia."

    return "✅ Cumple con los principios de la Sharia."
