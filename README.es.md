# CAD Trim & Fillet para IngeTrazo

[![Extensión de IngeTrazo](https://img.shields.io/badge/IngeTrazo-Extension-blue.svg)](https://ingetrazo.com/extensiones)
[![Licencia: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Versión](https://img.shields.io/badge/Version-1.0.0-green.svg)]()

Suite profesional de CAD 2D/3D para recorte, empalme de esquinas y chaflán para **IngeTrazo** (el software CAD BIM de código abierto).

Desarrollado por **Aymen Alhaddad (Architect & Developer)**.

Traducción al español: **Fernando Felix**.

🌐 Also available in English: [README.md](README.md)

---

## Características

### 1. Recorte rápido
- Haz clic en cualquier segmento de línea para borrarlo entre las intersecciones más cercanas que lo delimitan.
- La vista previa al pasar el cursor brilla en rojo intenso, con marcas de eliminación en forma de "X".
- Limpia automáticamente los vértices huérfanos y repara la topología de las caras.

### 2. Recorte por límite
- Selecciona primero una línea de corte como límite y luego haz clic en las líneas que la cruzan para recortar el lado donde hiciste clic.

### 3. Arco de empalme tangente
- Crea arcos circulares tangentes y suaves que redondean las esquinas entre dos líneas.
- **Compatibilidad con el cuadro de medidas (VCB)**: escribe el radio directamente en cualquier momento (por ejemplo `0.5`, `1.2`) y pulsa `Enter`.
- **Esquina viva ($R=0$)**: si el radio es `0`, las aristas se extienden o se recortan hasta formar un vértice en esquina viva.
- **Reparación de caras B-Rep**: actualiza automáticamente los polígonos de las superficies incidentes y elimina la cuña exterior que queda fuera del arco.
- Vista previa del arco circular en tiempo real en la vista mientras mueves el cursor.

### 4. Chaflán
- Conexiones rectas biseladas en las esquinas, con distancias personalizables ($D_1$, $D_2$).
- Compatibilidad completa con la entrada de distancia en el VCB y recorte automático de caras.

### 5. Cuadro de diálogo de configuración
- Ventana de configuración para ajustar el radio de empalme predeterminado, la resolución de segmentos del arco (suavidad) y las distancias del chaflán.

### 6. Arquitectura profesional y deshacer/rehacer
- Integración completa de deshacer/rehacer transaccional con `SnapshotImport` de IngeTrazo (`Ctrl+Z` / `Ctrl+Y`).
- Íconos vectoriales de alta resolución que se adaptan al tema (compatibles con los temas claro y oscuro de la interfaz).
- Accesos directos en el menú contextual de la vista, con clic derecho.

### 7. Interfaz multiidioma (inglés / español)
- Elige el idioma en el cuadro de configuración (**Automático / English / Español**). La elección se guarda entre sesiones; reinicia IngeTrazo para aplicarla a los menús y la barra de herramientas.
- Con **Automático**, se usa español si IngeTrazo o el sistema usan español, e inglés en los demás casos.
- Para forzar un idioma desde el código, cambia `FORCE_LANGUAGE = "en"` o `FORCE_LANGUAGE = "es"` cerca del inicio de `__init__.py`.
- Para agregar otro idioma, copia el bloque `"en"` dentro de `_TEXTS` y tradúcelo.

---

## Instalación

1. Descarga la última versión `cad_trim_fillet_v1.0.0.zip` desde [Releases](https://github.com/aymenart/cad_trim_fillet/releases).
2. Extrae la carpeta `cad_trim_fillet` en el directorio de plugins de IngeTrazo:
   - **Windows**: `%APPDATA%\IngeTrazo\plugins\`  
     (`C:\Users\<TuUsuario>\AppData\Roaming\IngeTrazo\plugins\`)
   - **Linux / Flatpak / AppImage**: `~/.config/IngeTrazo/plugins/`
3. Reinicia IngeTrazo. La barra de herramientas **CAD Trim & Fillet** aparecerá en la parte superior, junto con las entradas del menú en **Extensiones > CAD Trim & Fillet**.

---

## Licencia

Este proyecto está licenciado bajo la Licencia Pública General de GNU v3.0 o posterior (GPL-3.0-or-later).
