"""
Prediction API endpoints.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter

try:
    from ..utils.mongodb_connector import get_mongodb_connector
except ImportError:
    from utils.mongodb_connector import get_mongodb_connector

prediction_router = APIRouter()


@prediction_router.get("/status")
async def prediction_status():
    return {"status": "ok", "module": "predictions"}


@prediction_router.post("/peak-hours")
async def predict_peak_hours():
    return {"result": "endpoint ready", "user_story": "US037"}


@prediction_router.get("/bus-recommendations")
async def bus_recommendations():
    """Compat endpoint for Flutter: returns horarios list used by BusRecommendationsView."""
    capacidad_bus = 50
    connector = await get_mongodb_connector()

    # Last 4 weeks window, same intent as legacy JS endpoint
    fecha_limite = datetime.utcnow() - timedelta(days=28)

    pipeline = [
        {
            "$match": {
                "fecha_hora": {"$exists": True, "$gte": fecha_limite}
            }
        },
        {
            "$addFields": {
                "fechaObj": {
                    "$cond": [
                        {"$eq": [{"$type": "$fecha_hora"}, "date"]},
                        "$fecha_hora",
                        {"$toDate": "$fecha_hora"}
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "hora": {"$hour": "$fechaObj"},
                    "tipo": "$tipo"
                },
                "cantidad": {"$sum": 1}
            }
        },
        {"$sort": {"_id.hora": 1}}
    ]

    async with connector.get_connection() as db:
        asistencias_por_hora = await db["asistencias"].aggregate(pipeline).to_list(length=None)

    horarios = []
    for hora in range(6, 21):
        entradas = next(
            (x.get("cantidad", 0) for x in asistencias_por_hora
             if x.get("_id", {}).get("hora") == hora and x.get("_id", {}).get("tipo") == "entrada"),
            0
        )
        salidas = next(
            (x.get("cantidad", 0) for x in asistencias_por_hora
             if x.get("_id", {}).get("hora") == hora and x.get("_id", {}).get("tipo") == "salida"),
            0
        )
        total = entradas + salidas
        buses_recomendados = (total + capacidad_bus - 1) // capacidad_bus

        horarios.append({
            "hora": hora,
            "entradas": entradas,
            "salidas": salidas,
            "total": total,
            "buses_recomendados": buses_recomendados,
            "es_hora_pico": total > (capacidad_bus * 2)
        })

    hora_mas_congestionada = max(horarios, key=lambda h: h["total"]) if horarios else None
    buses_maximos = max((h["buses_recomendados"] for h in horarios), default=0)

    return {
        "success": True,
        "capacidad_por_bus": capacidad_bus,
        "periodo_analizado": "Ultimas 4 semanas",
        "horarios": horarios,
        "resumen": {
            "hora_mas_congestionada": hora_mas_congestionada,
            "buses_maximos_requeridos": buses_maximos
        }
    }
