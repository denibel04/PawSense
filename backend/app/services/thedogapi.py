"""
TheDogAPI Service - Helper para consultar información de razas de perros.
API: https://api.thedogapi.com/v1/breeds/search?q=<breed>
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class TheDogAPIError(Exception):
    """Exception para errores de TheDogAPI."""
    pass


async def get_breed_info(breed_name: str) -> Optional[Dict[str, Any]]:
    """
    Consulta TheDogAPI para obtener información de una raza.
    
    Args:
        breed_name: Nombre de la raza a buscar
        
    Returns:
        Diccionario con datos normalizados de la raza o None si no existe.
        
    Raises:
        TheDogAPIError: Si la API key no está configurada o falla la API.
    """
    if not settings.THE_DOG_API_KEY:
        raise TheDogAPIError("THE_DOG_API_KEY no está configurada en variables de entorno")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Consultar TheDogAPI
            url = "https://api.thedogapi.com/v1/breeds/search"
            headers = {"x-api-key": settings.THE_DOG_API_KEY}
            params = {"q": breed_name}
            
            response = await client.get(url, headers=headers, params=params)
            
            # Manejar errores HTTP
            if response.status_code == 401:
                raise TheDogAPIError("API key inválida o expirada")
            elif response.status_code >= 500:
                raise TheDogAPIError(f"TheDogAPI retornó error {response.status_code}")
            
            response.raise_for_status()
            
            # Parsear respuesta
            data = response.json()
            
            if not data or len(data) == 0:
                return None
            
            # Tomar el primer resultado (mejor match)
            breed = data[0]
            
            # Normalizar respuesta
            normalized = {
                "found": True,
                "breed": breed.get("name", breed_name),
                "temperament": breed.get("temperament"),
                "life_span": breed.get("life_span"),
                "height_metric": breed.get("height", {}).get("metric"),
                "weight_metric": breed.get("weight", {}).get("metric"),
                "bred_for": breed.get("bred_for"),
                "breed_group": breed.get("breed_group"),
                "origin": breed.get("origin"),
            }
            
            return normalized
            
    except httpx.HTTPError as e:
        # Errores de conexión
        raise TheDogAPIError(f"Error conectando a TheDogAPI: {str(e)}")
    except Exception as e:
        # Otros errores
        raise TheDogAPIError(f"Error inesperado consultando TheDogAPI: {str(e)}")
