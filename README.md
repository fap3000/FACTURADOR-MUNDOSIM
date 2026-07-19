# Mundosim Facturador — Guía de deploy en Render.com

## ¿Qué es esto?
App web para emitir Facturas C electrónicas en ARCA (ex-AFIP).
Accesible desde cualquier PC con internet, con login por sucursal.

## Usuarios predeterminados
| Usuario  | Contraseña  | Acceso              |
|----------|-------------|---------------------|
| mendoza  | mendoza123  | Solo Mendoza (PV 1) |
| sanjuan  | sanjuan123  | Solo San Juan (PV 2)|
| admin    | admin2024   | Ve todo             |

---

## Deploy en Render.com (GRATIS, sin tarjeta)

### Paso 1 — Subir el código a GitHub
1. Creá una cuenta en github.com (si no tenés)
2. Creá un repositorio nuevo llamado `mundosim-facturador`
3. Subí todos estos archivos al repositorio

### Paso 2 — Crear la app en Render
1. Entrá a render.com y creá una cuenta con tu email
2. Hacé clic en "New +" → "Web Service"
3. Conectá tu repositorio de GitHub
4. Configuración:
   - **Name**: mundosim-facturador
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free

### Paso 3 — Variables de entorno (Environment Variables)
En Render → tu servicio → "Environment", agregá:

```
SECRET_KEY       = (una cadena larga aleatoria, ej: mundosim2024xK9mP)
PASS_MENDOZA     = (contraseña para encargado de Mendoza)
PASS_SANJUAN     = (contraseña para encargado de San Juan)
PASS_ADMIN       = (contraseña de administrador)
PV_MENDOZA       = 1     (punto de venta Mendoza en ARCA)
PV_SANJUAN       = 2     (punto de venta San Juan en ARCA)
```

### Paso 4 — Conectar ARCA (cuando tengas el certificado)
Agregar también estas variables:
```
CUIT             = 20123456789  (tu CUIT sin guiones)
CERT_PATH        = /etc/secrets/cert.crt
KEY_PATH         = /etc/secrets/key.pem
PRODUCCION       = true
CONCEPTO         = 2   (1=Productos, 2=Servicios, 3=Ambos)
```

Y subir los archivos del certificado en: Render → "Secret Files"

---

## Modo DEMO
Sin la variable CUIT configurada, la app funciona en modo demo
(simula la emisión sin conectarse a ARCA). Útil para probar la interfaz.

## URL final
Render te da una URL del tipo: https://mundosim-facturador.onrender.com
Esa URL la pueden usar desde Mendoza, San Juan o cualquier lugar.

---

## Estructura del proyecto
```
mundosim_facturador/
├── app.py              ← Backend Flask principal
├── requirements.txt    ← Dependencias Python
├── Procfile            ← Comando de inicio para Render
├── templates/
│   ├── base.html       ← Layout con nav y estilos
│   ├── login.html      ← Pantalla de login
│   ├── dashboard.html  ← Lista de comprobantes
│   ├── emitir.html     ← Formulario nueva factura
│   └── masivo.html     ← Carga masiva CSV
└── static/
    └── facturas_ejemplo.csv
```
