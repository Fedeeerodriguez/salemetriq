"""IG Prospector — módulo interno de prospección de Instagram por nicho.

Herramienta interna de generación de leads (solo superadmin de plataforma).
Su data vive en el schema Postgres `igp` del mismo proyecto Supabase, aislada
del `public` de SALEMETRIQ. Usa la auth de la plataforma (no tiene la suya).
"""
