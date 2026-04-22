import os

readme_content = """# 🐢 Kamehouse — Gym Management System

**Kamehouse** es una plataforma robusta de gestión de reservas para gimnasios y centros de entrenamiento, diseñada bajo una arquitectura de "control total" desde el panel de administración. El sistema permite a los administradores gestionar bloques horarios, registrar alumnos manualmente y automatizar la comunicación profesional con los clientes.

Este proyecto forma parte del ecosistema de **Perseus Technology**.

## 🚀 Características Principales

- **Monitor de Clases (Dashboard):** Integración de `FullCalendar.js` en el inicio del administrador para una visualización panorámica de la agenda semanal.
- **Gestión de Cupos:** Lógica de negocio centralizada en `services.py` que controla la capacidad máxima por bloque y evita sobrecupos.
- **Notificaciones Automatizadas:** Envío de correos electrónicos de confirmación con diseño HTML personalizado y archivos adjuntos de calendario (`.ics`) para sincronización con Google Calendar, Apple y Outlook.
- **Interfaz Administrativa Pro:** - Modo Claro/Oscuro dinámico con persistencia en `localStorage`.
    - Formularios de reserva optimizados (UI/UX) con diseño industrial.
    - Acciones rápidas para creación de reservas desde el monitor principal.
- **Seguridad y Control:** Acceso restringido mediante el sistema de autenticación nativo de Django (`staff_only`).

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.x, Django 5.x.
- **Frontend Admin:** JavaScript (ES6+), FullCalendar 6.1, CSS3 (Variables dinámicas).
- **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción).
- **Utilidades:** `icalendar` para generación de eventos, `django-tailwind` para estilos frontend.